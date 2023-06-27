#!/bin/bash

sudo apt-get update
sudo apt-get install parallel -y

echo INSTALLING NECESSARY PACKAGES
pip install --upgrade -r requirements.txt