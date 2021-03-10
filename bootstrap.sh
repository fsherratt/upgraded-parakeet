#!/usr/bin/env bash

# Actions in this file must be Idempotent - i.e. if run a second time they don't fuck things up

# Update local packages
export USER=vagrant
export USER_HOME=/home/$USER
export PX4_VERSION=v1.11.3

echo "Let's Go!!!"

cd $USER_HOME

#---------------------------------------------------#
# Update local packages
echo "Updating packages...."
apt-get update
apt-get upgrade -y
apt-get autoremove -y

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
	echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
	source ~/.bashrc

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

	cd $USER_HOME
else
	echo "Catkin already installed. Skipping...."
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
	source devel/setup.bash

	chown -R $USER $USER_HOME/catkin_ws/*

	cd $USER_HOME
else
	echo "Mavros already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup Install PX4 Autopilot
#TODO check that the correct version has been checked out
if ! (cd $USER_HOME/catkin_ws/; catkin list -u) | grep -q px4
# if [ ! -d /home/usr/vagrant/catkin_ws/src/PX4-Autopilot ]
then
	echo "Installing PX4..."
	cd $USER_HOME/catkin_ws/src
	git clone --depth 1 https://github.com/PX4/PX4-Autopilot.git --recursive
	# There ubuntu.sh script has not been updated in the latest stable release
	# git clone --depth 1 https://github.com/PX4/PX4-Autopilot.git -b $PX4_VERSION --recursive
	
	cd PX4-Autopilot/

	apt-get install gazebo9 libgazebo9-dev -y

	# Install dependencies
	. Tools/setup/ubuntu.sh

	# Compile PX4 for SITL
	DONT_RUN=1 make px4_sitl_default gazebo

	echo "Catkin build...."
	cd $USER_HOME/catkin_ws
	catkin build --no-status
	source devel/setup.bash

	chown -R $USER $USER_HOME/catkin_ws/*

	cd $USER_HOME
else
	echo "PX4 already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup intel-realsense


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

	source ~/.bashrc

	cd $USER_HOME
else
	echo "QGroundControl already installed. Skipping...."
fi


#---------------------------------------------------#
# Install Git kraken
#If we can find the command for gitkraken, we have already installed it and so dont need to install it again.
if ! command -v gitkraken &> /dev/null
then
	echo "Downloading gitkraken..."
	wget -q https://release.gitkraken.com/linux/gitkraken-amd64.deb

	echo "Installing gitkraken..."
	dpkg -i gitkraken-amd64.deb
else
	echo "Git Kraken already installed. Skipping...."
fi


#---------------------------------------------------#
# Install VSCode


echo "All installed, You're ready to go"
