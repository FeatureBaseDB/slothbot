#!/bin/bash
TYPE=f1-micro
NAME=slothbot
NEW_UUID=$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c 4 ; echo)

ZONE=$2
OPTION=$1
PREEMPTIBLE="--preemptible"
UBUNTU_VERSION="ubuntu-1804-bionic-v20220118"
IP=""

echo "This instance is preemtible, unless it's started with --prod";
case $OPTION in
    -p|--prod|--production)
       unset PREEMPTIBLE
       echo "Production mode enabled..."
       IP=""
       echo;
esac

case $ZONE in
    us-west1-a)
       echo "Using $ZONE to start slothbot...";
       ;;
    *)
       echo "Need a valid zone to start...such as us-west1-a";   
       exit;
       ;;
esac

if [ -f secrets.sh ]; then
   source secrets.sh # truly, a travesty, sets TOKEN=token-[passphrase]
   echo "Here's where I say, hold on a second while we fire things up."
   gcloud compute project-info add-metadata --metadata token=$TOKEN
   echo;
else
   echo "Create 'secrets.sh', put a TOKEN=f00bar statement in it and then rerun this script."
   echo;
   exit;
fi

SLOTH_VERSION=0.1.0
SCRIPT=$(cat <<EOF
#!/bin/bash
if [ -d "/opt/slothbot/" ]; then
  echo "starting slothbot"
  # sudo -i -u solr /opt/solr/bin/solr start -m 8192m
else
  sudo su -
  date >> /opt/start.time
  apt-get update -y

  apt-get install unzip -y
  apt-get install python-pip3

  #entropy
  apt-get -y install rng-tools
  cat "RNGDEVICE=/dev/urandom" >> /etc/default/rng-tools
  /etc/init.d/rng-tools restart

  git clone https://github.com/FeatureBaseDB/slothbot.git

  cd slothbot
  pip3 install -r requirements.txt

  # apt-get install apache2-utils -y
  # apt-get install nginx -y
  # cp nginx.conf.solr /etc/nginx/nginx.conf

  # python3 get_token.py solr
  # systemctl restart nginx.service

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
--labels type=solr \
--tags slothbot,token-$TOKEN \
$PREEMPTIBLE \
--subnet=default $IP --network-tier=PREMIUM \
--metadata startup-script="$SCRIPT"
sleep 15

# add data
gcloud compute instances add-metadata $NAME-$NEW_UUID --zone $ZONE --metadata-from-file=shutdown-script=stopslothbot.sh

IP=$(gcloud compute instances describe $NAME-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')

# gcloud compute firewall-rules create sloth-proxy --target-tags sloth --allow tcp:8389
echo "Password token is: $TOKEN"
echo "IP is: $IP"
