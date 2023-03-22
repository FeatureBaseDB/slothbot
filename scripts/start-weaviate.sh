#!/bin/bash
set -o allexport

screen -dmS weaviate bash -c "docker compose up"