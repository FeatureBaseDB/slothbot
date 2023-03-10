#!/bin/bash
set -o allexport
source ./config.sh
screen -dmS weaviate bash -c "docker compose up"