#!/usr/bin/env bash
# This file sets up the vagrant virtual machine enviroment installing
# all the required depedencies. Actions in this file must be idempotent 
# - i.e. if run a second time they don't fuck things up

echo "Let's Go!!!"

#---------------------------------------------------#
# File paramaters
export USER=vagrant

export PX4_VERSION=v1.11.3
export REALSENSE_VERSION=v2.42.0


#---------------------------------------------------#
# Setup
export USER_HOME=/home/$USER
cd $USER_HOME


#---------------------------------------------------#
# Update local packages
echo "Updating packages...."
apt-get update
apt-get upgrade -y

# This is always useful
apt-get install build-essential

# Make sure the latest kernel is installed - required for D435 realsense
apt-get install linux-generic linux-image-generic -y


#---------------------------------------------------#
#Install TMUX and VIM
# If we cannot find vim, install it.
if ! command -v vim &> /dev/null
then
	echo "Installing vim..."
	apt-get install vim -y
else
	echo "Vim already installed. Skipping..."
fi


#---------------------------------------------------#
# If we cannot find the tmux command, install it
if ! command -v tmux &> /dev/null
then
	echo "Installing tmux..."
	apt-get install tmux -y
else
	echo "Tmux installed. Skipping...."
fi


#---------------------------------------------------#
# install GNOME desktop env
# If dpkg does not list ubuntu desktop as installed, install it.
if ! dpkg -s ubuntu-desktop-minimal &> /dev/null
then
	echo "Installing desktop env...."
	apt-get install ubuntu-desktop-minimal -y
	apt-get upgrade
else
	echo "Ubuntu desktop installed. Skipping...."
fi

# TODO Add colcon_cd to shell. This will be decided when we decide where this will go.


#---------------------------------------------------#
# Setup python 3
# If we cannot find the pip3 command, install it
if ! command -v pip3 &> /dev/null
then
	echo "Installing python3..."
	apt-get install python3 -y
	apt-get install python3-pip -y
else
	echo "Python and pip installed. Skipping..."
fi


#---------------------------------------------------#
# Setup ROS Noetic
# If the directory for /opt/ros/noetic (i.e. where ros is installed) does not exist, then install it.
if [ ! -d /opt/ros/noetic ] 
then
	# Taken from http://wiki.ros.org/noetic/Installation/Ubuntu
	echo "Installing ROS Noetic...."
	
	# Add ros source
	sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
	apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' \
				--recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
	apt-get update

	# Install full desktop enviroment
	apt-get install ros-noetic-desktop-full -y

	# Setup ros enviroment in every new terminal
	echo "source /opt/ros/noetic/setup.bash" >> $USER_HOME/.bashrc
	source $USER_HOME/.bashrc

	apt-get install python3-rosdep \
				python3-rosinstall \
				python3-rosinstall-generator \
				python3-wstool -y

	rosdep init
	rosdep update

else
	echo "ROS Noetic installed. Skipping...."
fi


#---------------------------------------------------#
# Add ROS source to bashrc
#NOTE THIS ONLY WORKS FOR NOETIC
# If we cannot find the text "noetic" in our default bashrc, add it.
if ! grep -q noetic $USER_HOME/.bashrc 
then
	echo "Adding ros noetic to "$USER" .bashrc..."
	echo "source /opt/ros/noetic/setup.bash" >> $USER_HOME/.bashrc 
	source $USER_HOME/.bashrc

elsecd /home
	echo "Bash scripts already contains source for noetic ros. Skipping.."
fi


#---------------------------------------------------#
# Setup Catkin
#NOTE THIS IS A PRETTY WEAK WAY OF CHECKING CATKIN IS INSTALLED
if [ ! -d $USER_HOME/catkin_ws ]
then
	echo "Preparing catkin..."
	
	apt-get install python3-catkin-tools \
					python3-catkin-lint \
					python3-rosinstall-generator -y
	pip3 install osrf-pycommon
	
	mkdir $USER_HOME/catkin_ws/
	chown $USER $USER_HOME/catkin_ws
	cd $USER_HOME/catkin_ws/

	mkdir build; mkdir devel; mkdir install; mkdir logs; mkdir src
	chown -R $USER *

	catkin init
	catkin config --extend /opt/ros/noetic

	wstool init src

	source $USER_HOME/.bashrc

	cd $USER_HOME
else
	echo "Catkin already setup. Skipping...."
fi


#---------------------------------------------------#
# Setup Install MAVROS
if ! (cd $USER_HOME/catkin_ws/; catkin list -u) | grep -q mavros
then
	echo "Installing mavros...."
	cd $USER_HOME/catkin_ws

	apt-get install ros-noetic-mavros ros-noetic-mavros-extras -y

	rosdep update
	rosinstall_generator --rosdistro noetic mavlink | tee /tmp/mavros.rosinstall
	rosinstall_generator --rosdistro noetic --upstream mavros | tee -a /tmp/mavros.rosinstall

	wstool merge -t src /tmp/mavros.rosinstall
	wstool update -t src -j$(nproc)

	rosdep install --rosdistro noetic --from-paths src --ignore-src -y

	./$USER_HOME/catkin_ws/src/mavros/mavros/scripts/install_geographiclib_datasets.sh
	
	echo "Catkin build...."
	catkin build --no-status
	source $USER_HOME/.bashrc

	chown -R $USER $USER_HOME/catkin_ws/*

	cd $USER_HOME
else
	echo "Mavros already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup Install PX4 Autopilot
if ! (cd $USER_HOME/catkin_ws/; catkin list -u) | grep -q px4
# if [ ! -d /home/usr/vagrant/catkin_ws/src/PX4-Autopilot ]
then
	echo "Installing PX4..."
	cd $USER_HOME/catkin_ws/src
	#NOTE: This should not just be master but we need to wait for the next 
	# stable release for ubuntu.sh fix yet to be released
	git clone https://github.com/PX4/PX4-Autopilot.git --recursive
	
	# git clone --depth 1 https://github.com/PX4/PX4-Autopilot.git -b $PX4_VERSION --recursive
	
	cd PX4-Autopilot/

	# Install dependencies
	. Tools/setup/ubuntu.sh

	# Compile PX4 for SITL
	DONT_RUN=1 make px4_sitl_default gazebo

	echo "Catkin build...."
	cd $USER_HOME/catkin_ws
	catkin build --no-status
	source $USER_HOME/.bashrc

	chown -R $USER src/PX4-Autopilot/

	cd $USER_HOME
else
	echo "PX4 already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup Intel-Realsense
# Instructions from here - https://github.com/IntelRealSense/librealsense/blob/master/doc/distribution_linux.md
# And here - https://github.com/IntelRealSense/realsense-ros
# If command realsense-viewer is found assume already installed
if  ! command -v realsense-viewer &> /dev/null 
then
	echo "Installing realsense...."

	apt-key adv --keyserver keys.gnupg.net --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE || \
	apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE

	add-apt-repository "deb http://realsense-hw-public.s3.amazonaws.com/Debian/apt-repo focal main" -u

	apt-get update

	apt-get install librealsense2-dkms -y
	apt-get install librealsense2-utils -y
	
	pip3 install pyrealsense2

	# ROS Setup
	apt-get install ddynmaic-reconfigure -y
	apt-get install ros-noetic-realsense2-camera -y
	apt-get install ros-noetic-realsense2-description -y

else
	echo "Intel realsense already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup open CV


#---------------------------------------------------#
# Install QGroundControl
#NOTE this is a pretty weak check of installation
if ! command -v QGC &> /dev/null
then
	echo "Installing QGroundControl...."
	cd /usr/bin 
	wget -q https://s3-us-west-2.amazonaws.com/qgroundcontrol/latest/QGroundControl.AppImage
	chmod +x ./QGroundControl.AppImage

	# Create symlink so it can be opened with the command QGC - could be an alias
	ln -s QGroundControl.AppImage QGC
	chmod +x QGC

	source $USER_HOME/.bashrc

	cd $USER_HOME
else
	echo "QGroundControl already installed. Skipping...."
fi


#---------------------------------------------------#
# Install Git kraken
# If we can find the command for gitkraken, we have already installed it
if ! command -v gitkraken &> /dev/null
then
	echo "Downloading gitkraken..."
	wget -q https://release.gitkraken.com/linux/gitkraken-amd64.deb

	echo "Installing gitkraken..."
	dpkg -i gitkraken-amd64.deb

	rm gitkraken-amd64.deb
else
	echo "Git Kraken already installed. Skipping...."
fi


#---------------------------------------------------#
# Install VSCode
# Instructions from here -https://code.visualstudio.com/docs/setup/linux
# If we can find the command for code, we have already installed it
if ! command -v code &> /dev/null
then
	echo "Installing VSCode..."
	wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
	sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/

	sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'

	apt-get install apt-transport-https -y

	apt-get update
	apt-get install code -y

	rm packages.microsoft.gpg
else
	echo "VSCode already installed. Skipping...."
fi


echo "All installed, You're ready to go"
