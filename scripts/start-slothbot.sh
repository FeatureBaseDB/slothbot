#!/bin/bash
set -o allexport

screen -dmS flask bash -c "python3 main.py"
screen -dmS slothbot bash -c "python3 slothbot.py"
