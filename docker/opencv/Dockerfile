# This is a multi-stage build
# - Stage 1 is installing all required packages for the final images
# - Stage 2 involves install packages required for opencv/numpy compilation
# - Stage 3 - revert to stage 1 image, copy compiled code from stage 2 and install
FROM python:3.8.6-slim as opencv_env
ENV OPENCV_VERSION=4.4.0
ENV NUMPY_VERSION==1.19.2

RUN apt-get update && apt-get install -y --no-install-recommends \
    # Install image formats
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    # Install video formats
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libxvidcore-dev \
    libx264-dev \
    libv4l-dev \
    # Install hardware acceleration
    libgtk2.0-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    libblas-dev \
    libeigen3-dev \
    liblapack-dev \
    libtbb-dev \
    libtbb2 \
    libneon27-dev \
    # Clean up after installs
    && rm -rf /var/lib/apt/lists/*


# Intermediary build stage, this is just used to compile the code
# The reason for an intermediate build stage is to reduce the final image size
FROM opencv_env as opencv_build_env
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    wget \
    unzip \
    cmake \
    pkg-config \
    file

RUN python3 -m pip install --upgrade pip setuptools wheel

# We do it like this so if required we can compile numpy from source
# then install as a wheel later
RUN mkdir wheelhouse && \
    pip wheel numpy==${NUMPY_VERSION} --wheel-dir=/wheelhouse \
    --extra-index-url https://www.piwheels.org/simple
RUN pip install --no-index --find-links=/wheelhouse numpy==${NUMPY_VERSION}

# Download OpenCV
RUN wget -O opencv.zip https://github.com/opencv/opencv/archive/$OPENCV_VERSION.zip && \
    unzip opencv.zip && \
    rm -rf opencv.zip && \
    wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/$OPENCV_VERSION.zip  &&\
    unzip opencv_contrib.zip && \
    rm -rf opencv_contrib.zip
RUN OPENCV_CONTRIB_MODULES_SRC_DIR=$(pwd)/opencv_contrib-$OPENCV_VERSION/modules

WORKDIR /opencv-$OPENCV_VERSION/build
ARG TARGETPLATFORM

# Checks the current platform to deterime if OPENMP, NEON and VFPV3 can be enabled
RUN case ${TARGETPLATFORM} in \
    "linux/arm64" ) \
    USE_OPENMP="ON"; USE_NEON="ON"; USE_VFPV3="OFF" ;; \
    "linux/arm/v7" ) \
    USE_OPENMP="ON"; USE_NEON="ON"; USE_VFPV3="ON" ;; \
    * ) \
    USE_OPENMP="OFF"; USE_NEON="OFF"; USE_VFPV3="OFF" ;; \
    esac; \

    echo $USE_OPENMP; echo $USE_NEON; echo $USE_VFPV3; \

    # Setup OpenCV
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CPACK_BINARY_DEB=ON \
    -D BUILD_PACKAGE=ON \
    -D OPENCV_VCSVERSION=${OPENCV_VERSION} \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=$OPENCV_CONTRIB_MODULES_SRC_DIR \
    -D OPENCV_PYTHON3_INSTALL_PATH=/usr/local/lib/python3.8/site-packages/ \
    -D PYTHON3_EXECUTABLE=$(which python3) \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D BUILD_EXAMPLES=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D BUILD_PERF_TESTS=OFF \
    -D BUILD_TESTS=OFF \
    -D BUILD_DOCS=OFF \
    -D ENABLE_PRECOMPILED_HEADERS=OFF \
    -D WITH_TBB=ON \
    -D WITH_OPENMP=${USE_OPENMP} \
    -D ENABLE_NEON=${USE_NEON} \
    -D ENABLE_VFPV3=${USE_VFPV3} \
    -D OPENCV_EXTRA_EXE_LINKER_FLAGS=-latomic \
    ..

# Compile OPENCV
RUN make -j${nproc}
RUN make install && ldconfig && make package

# Install pip packages
# As before we do it like this so if compilation from source is required we don't have to
# carry over the build tools, instead we can just copy the wheel and install from that
COPY requirements.txt .
RUN pip wheel -r requirements.txt --wheel-dir=/wheelhouse \
    --extra-index-url https://www.piwheels.org/simple

WORKDIR /


# Final image
FROM opencv_env

# Install python packages
COPY requirements.txt .
COPY --from=opencv_build_env /wheelhouse ./wheelhouse
RUN pip install --no-index numpy==${NUMPY_VERSION} --find-links=/wheelhouse
RUN pip install --no-index --find-links=/wheelhouse -r requirements.txt

# Install opencv
COPY --from=opencv_build_env /opencv-$OPENCV_VERSION/build/*.deb ./opencv/
RUN dpkg -i ./opencv/*.deb

# Clean up
RUN rm -rf opencv  && rm -rf wheelhouse

WORKDIR /app

CMD "/bin/bash"