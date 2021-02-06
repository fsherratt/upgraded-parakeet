#!/usr/bin/env bash

# Update local packages
apt-get update
# Upgrade our packages
apt-get upgrade -y

#Install TMUX and VIM
apt-get install vim -y
apt-get install tmux -y

# install GNOME desktop env
apt-get install ubuntu-desktop-minimal -y

# Setup python 3
apt-get install python3 -y
apt-get install python3-pip -y

#Setup ROS
# Taken from https://index.ros.org/doc/ros2/Installation/Foxy/Linux-Install-Debians/
locale  # check for UTF-8

sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

locale  # verify settings

apt update && apt install curl gnupg2 lsb-release -y
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -

sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'

# Install ROS desktop environment
apt update
apt install ros-foxy-desktop -y

# Install autocomplete
apt install -y python3-pip
pip3 install -U argcomplete

# Setup open CV

# Install VS Code


# Install Git kraken
wget https://release.gitkraken.com/linux/gitkraken-amd64.deb
dpkg -i gitkraken-amd64.deb
