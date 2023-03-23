#!/bin/bash
TYPE=n2-highmem-4
NAME=weaviate
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

ZONE=us-west1-a
OPTION=$1
PREEMPTIBLE="--preemptible"
UBUNTU_VERSION="ubuntu-2204-jammy-v20230114"
IP=""

echo "This instance is preemtible, unless it's started with --prod";
case $OPTION in
    -p|--prod|--production)
       unset PREEMPTIBLE
       echo "Production mode enabled..."
       IP="34.83.82.8"
       echo;
esac

if [ -f secrets.sh ]; then
   source secrets.sh # truly, a travesty, sets TOKEN=token-[passphrase]
   echo "Here's where I say, hold on a second while we fire things up."
   gcloud compute project-info add-metadata --metadata token=$TOKEN
   echo;
else
   echo "Create 'secrets.sh', put a TOKEN=f00bar and SK=xxx statements in it and then rerun this script."
   echo;
   exit;
fi

SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/weaviate/" ]; then
  echo "starting weaviate"
  sleep 10
  cd /root/
  /root/start-weaviate.sh
else
  sudo su -
  date >> /opt/start.time
  apt-get update -y

  apt-get install unzip -y
  apt-get install python3-pip

  #entropy
  apt-get -y install rng-tools
  cat "RNGDEVICE=/dev/urandom" >> /etc/default/rng-tools
  /etc/init.d/rng-tools restart

  # install docker
  snap install docker

  cd /opt/
  git clone https://github.com/FeatureBaseDB/slothbot.git
  cd /opt/slothbot/scripts/

  cp docker-compose.yml /root/
  cp start-weaviate.sh /root/
  cp get_token.py /root/

  apt-get install apache2-utils -y
  apt-get install nginx -y
  
  cp nginx.conf.weaviate /etc/nginx/nginx.conf

  # grab the tokens and write to nginx htpasswrd and env
  cd /root
  python3 get_token.py weaviate

  # start weaviate
  ./start-weaviate.sh

  # grab the token and write to nginx htpasswrd
  python3 get_token.py weaviate

  # restart ngninx
  systemctl restart nginx.service

  date >> /opt/done.time

fi
EOF
)

gcloud compute instances create $NAME-$NEW_UUID \
--machine-type $TYPE \
--image "$UBUNTU_VERSION" \
--image-project "ubuntu-os-cloud" \
--boot-disk-size "100GB" \
--boot-disk-type "pd-ssd" \
--boot-disk-device-name "$NEW_UUID" \
--service-account slothbot@sloth-compute.iam.gserviceaccount.com \
--zone $ZONE \
--labels type=weaviate \
--tags weaviate,token-$TOKEN \
$PREEMPTIBLE \
--subnet=default $IP --network-tier=PREMIUM \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stop-weaviate.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create sloth-proxy --target-tags sloth --allow tcp:8389
echo "Password token is: $TOKEN"
echo "IP is: $IP"