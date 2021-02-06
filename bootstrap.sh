#!/usr/bin/env bash

# Update local packages
echo "Updating packages...."
apt-get update
# Upgrade our packages
apt-get upgrade -y

#Install TMUX and VIM
# If we cannot find vim, install it.
if ! command -v vim &> /dev/null
then
	echo "Installing vim..."
	apt-get install vim -y
else
	echo "Vim already installed. Skipping..."
fi

# If we cannot find the tmux command, install it
if ! command -v tmux &> /dev/null
then
	echo "Installing tmux..."
	apt-get install tmux -y
else
	echo "Tmux installed. Skipping...."
fi

# install GNOME desktop env
# If dpkg does not list ubuntu desktop as installed, install it.
if ! dpkg -s ubuntu-desktop-minimal &> /dev/null
then
	echo "Installing desktop env...."
	apt-get install ubuntu-desktop-minimal -y
else
	echo "Ubuntu desktop installed. Skipping...."
fi

# Setup python 3
# If we cannot find the python3 command, install it
if ! command -v python3 &> /dev/null
then
	echo "Installing python3..."
	apt-get install python3 -y
	apt-get install python3-pip -y
else
	echo "Python and pip installed. Skipping..."
fi

#Setup ROS
# If the directory for /opt/ros/foxy (i.e. where ros is installed) does not exist, then install it.
if [ ! -d /opt/ros/foxy ] 
then
	echo "Installing ROS...."
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
else
	echo "ROS2 installed. Skipping...."
fi


# Add ROS source to bashrc
#NOTE THIS ONLY WORKS FOR FOXY AND USER VAGRANT
# If we cannot find the text "foxy" in our default bashrc, add it.
if ! grep -q foxy /home/vagrant/.bashrc 
then
	echo "Adding ros2 to vagrant .bashrc..."
	echo "source /opt/ros/foxy/setup.bash" >> /home/vagrant/.bashrc
else
	echo "Bash scripts already contains source for foxy ros. Skipping.."
fi

# Setup open CV

# Install VS Code


# Install Git kraken
# If we can find the command for gitkraken, we have already installed it and so dont need to install it again.
if ! command -v gitkraken &> /dev/null
then
	echo "Downloading gitkraken..."
	wget -q https://release.gitkraken.com/linux/gitkraken-amd64.deb
	echo "Installing gitkraken..."
	dpkg -i gitkraken-amd64.deb
else
	echo "Git Kraken already installed. Skipping...."
fi
