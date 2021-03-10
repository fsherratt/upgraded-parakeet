#!/usr/bin/env bash

# Update local packages
export USER=vagrant
export PX4_VERSION=v1.11.3

echo "Let's Go!!!"

#---------------------------------------------------#
# Update local packages
echo "Updating packages...."
apt-get update
apt-get upgrade -y
apt-get autoremove -y

#---------------------------------------------------#
# Install virtualbox guest additions
apt-get install dkms build-essential module-assistant -y
apt-get install virtualbox-guest-dkms virtualbox-guest-utils virtualbox-guest-x11 -y
apt-get update

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
else
	echo "Ubuntu desktop installed. Skipping...."
fi

# TODO Add colcon_cd to shell. This will be decided when we decide where this will go.

#---------------------------------------------------#
# Setup python 3
If we cannot find the python3 command, install it
if ! command -v python3 &> /dev/null
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
if ! grep -q noetic /home/$USER/.bashrc 
then
	echo "Adding ros noetic to "$USER" .bashrc..."
	echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
	source ~/.bashrc

else
	echo "Bash scripts already contains source for noetic ros. Skipping.."
fi

#---------------------------------------------------#
# Setup Catkin
#NOTE THIS IS A PRETTY WEAK WAY OF CHECKING CATKIN IS INSTALLED
if [ ! -d /home/$USER/catkin_ws ]
then
	echo "Preparing catkin..."
	apt-get install python3-catkin-tools \
					python3-catkin-lint \
					python3-rosinstall-generator \
					osrf-pycommon-y

	mkdir ~/catkin_ws
	cd ~/catkin_ws
	
	mkdir build; mkdir devel; mkdir install; mkdir logs; mkdir src

	catkin init
	catkin --extend /opt/ros/noetic

	wstool init src

	cd ~
else
	echo "Catkin already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup Install MAVROS
if ! (cd /home/$USER/catkin_ws/; catkin list -u) | grep -q mavros
then
	echo "Installing mavros..."
	cd ~/catkin_ws

	apt-get install ros-noetic-mavros ros-noetic-mavros-extras -y

	rosdep update
	rosinstall_generator --rosdistro noetic mavlink | tee /tmp/mavros.rosinstall
	rosinstall_generator --rosdistro noetic --upstream mavros | tee -a /tmp/mavros.rosinstall

	wstool merge -t src /tmp/mavros.rosinstall
	wstool update -t src -j$(nproc)

	rosdep install --rosdistro noetic --from-paths src --ignore-src -y

	sudo ./src/mavros/mavros/scripts/install_geographiclib_datasets.sh

	catkin build
	source devel/setup.bash

	cd ~
else
	echo "Mavros already installed. Skipping...."
fi


#---------------------------------------------------#
# Setup Install PX4 Autopilot
#TODO check that the correct version has been checked out
if ! (cd /home/$USER/catkin_ws/; catkin list -u) | grep -q px4
# if [ ! -d /home/usr/vagrant/catkin_ws/src/PX4-Autopilot ]
then
	echo "Installing PX4..."
	cd ~/catkin_ws/src
	git clone --depth 1 https://github.com/PX4/PX4-Autopilot.git -b $PX4_VERSION --recursive
	cd PX4-Autopilot/

	# Install dependencies
	bash ./Tools/setup/ubuntu.sh

	# Compile PX4 for SITL
	DONT_RUN=1 make px4_sitl_default gazebo

	cd ~/catkin_ws
	catkin build
	source devel/setup.bash

	cd ~
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
