# Realsense build
FROM python:3.8.6-slim as librealsense_env
ENV LIBREALSENSE_VERSION=2.38.1

# Install required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    libusb-1.0-0-dev \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    # Tools
    udev \
    usbutils \
    # Build tools
    build-essential \
    cmake \
    wget \
    unzip \
    pkg-config \
    # Clean up after installs
    && rm -rf /var/lib/apt/lists/*

# Download librealsense
RUN wget -O librealsense.zip https://github.com/IntelRealSense/librealsense/archive/v$LIBREALSENSE_VERSION.zip && \
    unzip librealsense.zip && \
    rm -rf librealsense.zip

WORKDIR /librealsense-${LIBREALSENSE_VERSION}/build

# Setup librealsense build
ARG TARGETPLATFORM
RUN case ${TARGETPLATFORM} in \
    "linux/arm64" | "linux/arm/v7") \
    USE_RSUSB_BACKEND="true" ;; \
    * ) \
    USE_RSUSB_BACKEND="false" ;; \
    esac; \
    echo ${USE_RSUSB_BACKEND} ; \
    cmake \
    -D CMAKE_BUILD_TYPE=RELEASE \
    -D BUILD_EXAMPLES=bool:false \
    -D BUILD_GRAPHICAL_EXAMPLES=bool:false \
    -D BUILD_PYTHON_BINDINGS=bool:true \
    -D PYTHON_EXECUTABLE=$(which python3) \
    -D FORCE_RSUSB_BACKEND=${USB_RSUSB_BACKEND} \
    ..

# Compile librealsense - on arm only 1 core works reliably
RUN make -j${nproc}
RUN make install && ldconfig

WORKDIR /

# https://github.com/IntelRealSense/meta-intel-realsense/issues/20
RUN cp /librealsense-${LIBREALSENSE_VERSION}/wrappers/python/pyrealsense2/__init__.py \
    /usr/local/lib/python3.8/site-packages/pyrealsense2/
# Set USB rules
RUN cp /librealsense-${LIBREALSENSE_VERSION}/config/99-realsense-libusb.rules /etc/udev/rules.d/
RUN rm -rf librealsense-${LIBREALSENSE_VERSION}

# Install pip packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://www.piwheels.org/simple

# Clean up
RUN apt-get purge -y \
    build-essential \
    cmake \
    wget \
    unzip \
    pkg-config && \
    apt-get autoremove -y

WORKDIR /app

CMD "/bin/bash"