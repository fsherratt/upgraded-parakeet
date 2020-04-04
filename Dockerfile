FROM ubuntu:18.04 as build_env
MAINTAINER Freddie Sherratt <fs349@bath.ac.uk>

ENV DEBIAN_FRONTEND=noninteractive

ARG OPENCV_VERSION="4.2.0"
ARG REALSENSE_VERSION="2.34.0"
ARG ARDUPILOT_TAG="Copter-4.0.3"
ARG USERNAME=ERL

RUN useradd -U -d /$USERNAME $USERNAME && \
    usermod -G users $USERNAME

RUN apt-get update && \
apt-get install --no-install-recommends -y \
	apt-utils \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
	yasm \
	pkg-config \
	software-properties-common \
	lsb-release \
	sudo

##################
# Install Python #
##################
RUN apt-get install -y python3 python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

RUN pip3 install numpy pylint

###################
# Install Open CV #
###################
WORKDIR /

RUN apt-get install -y \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavformat-dev \
        libpq-dev

RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D OPENCV_ENABLE_NONFREE=ON \
    	-D BUILD_PERF_TESTS=OFF \
    	-D BUILD_TESTS=OFF \
    	-D BUILD_DOCS=OFF \ 
	-D INSTALL_PYTHON_EXAMPLES=OFF \
	-D BUILD_EXAMPLES=OFF \
	-D WITH_TBB=ON \
    	-D WITH_OPENMP=ON \
	-D INSTALL_C_EXAMPLES=OFF \
  	-D PYTHON_EXECUTABLE=$(which python3) \
  	.. \
&& make -j$(nproc)\
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}

#####################
# Install Realsense #
#####################
WORKDIR /

RUN apt-get install -y \
	dirmngr \
	gpg-agent

RUN apt-key adv --keyserver keys.gnupg.net --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE \
|| apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
RUN add-apt-repository "deb http://realsense-hw-public.s3.amazonaws.com/Debian/apt-repo bionic main" -u

RUN apt-get update && \
	apt-get install -y \
	librealsense2-dkms \
	librealsense2-utils

RUN pip3 install pyrealsense2




