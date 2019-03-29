#!/bin/bash
echo "__ARNN installer__"

echo "Installing PIP..."
#check if pip is installed and install it if not
sudo apt update
sudo apt install pip3

echo "Installing NodeJS..."
#check if nodejs is installed and install it otherwise
sudo apt install nodejs

echo "Installing Bokeh..."
#install bokeh
pip3 install bokeh

echo "Installing Sklearn..."
#install sklearn and numpy
pip3 install sklearn

echo "Installing Django..."
#install django
pip3 install django

echo "Installing Jupyter..."
#install jupyter
pip3 install jupyter

