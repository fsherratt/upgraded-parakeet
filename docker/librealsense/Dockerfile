# This is a multi-stage build
# - Stage 1 is installing all required packages for the final images
# - Stage 2 involves install packages required for opencv/numpy compilation
# - Stage 3 - revert to stage 1 image, copy compiled code from stage 2 and install
FROM python:3.8.6-slim as librealsense_env
ENV LIBREALSENSE_VERSION=2.38.1
ENV NUMPY_VERSION==1.19.2

# Install required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    libusb-1.0-0-dev \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    # Clean up after installs
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel

## CUT HERE

# Intermediary build stage, this is just used to compile the code
# The reason for an intermediate build stage is to reduce the final image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    wget \
    unzip \
    pkg-config

# Download librealsense
RUN wget -O librealsense.zip https://github.com/IntelRealSense/librealsense/archive/v$LIBREALSENSE_VERSION.zip && \
    unzip librealsense.zip && \
    rm -rf librealsense-${LIBREALSENSE_VERSION}.zip

WORKDIR /librealsense-${LIBREALSENSE_VERSION}/build

# Setup librealsense build
RUN cmake \
    -D CMAKE_BUILD_TYPE=RELEASE \
    -D BUILD_EXAMPLES=bool:true \
    -D BUILD_GRAPHICAL_EXAMPLES=bool:false \
    -D BUILD_PYTHON_BINDINGS=bool:true \
    -D PYTHON_EXECUTABLE=$(which python3) \
    -DFORCE_LIBUVC=true \
    ..

# Compile librealsense
RUN make -j${nproc}
RUN make install && ldconfig

# https://github.com/IntelRealSense/meta-intel-realsense/issues/20
RUN cp ../wrappers/python/pyrealsense2/__init__.py /usr/local/lib/python3.8/site-packages/pyrealsense2/

# Install pip packages
# We do it like this so if compilation from source is required we don't have to
# carry over the build tools, instead we can just copy the wheel and install from that
COPY requirements.txt .
RUN pip wheel -r requirements.txt --wheel-dir=/wheelhouse \
    --extra-index-url https://www.piwheels.org/simple


## CUT HERE

RUN pip install --no-index --find-links=/wheelhouse -r requirements.txt && rm -rf wheelhouse


WORKDIR /app

CMD "/bin/bash"