# Setup
This docuemnent contains instructions on how to setup development enviroment for the TBDr ERL codebase. These instructions have been tested in Windows 10 and Ubuntu 18.04.

## Table of Contents
- [Setting up a VM on Windows](#windows)
- [Setting up the Docker Development Enviroment](#docker)
- [Using VSCode for Development](#vscode)

# <a name="windows"></a>Setting up a VM on Windows
- Tested with Oracle Virtualbox and VMware Worksatation
- Microsoft Hyper-v must be disabled, see below
- Install your preferred flavour of linux
- Connect realsense cameras through USB passthrough
- run `lsusb` and confirm an Intel devices shows up
- Follow the instructions for setting up the dev enviroment

## Disable hyper-v
Go to `Turn windows features on or off` and make sure `Hyper-V -> Hyper-V Platform -> Hyper-V Hypervisors` is deselected. Then restart your computer

## Connecting USB in VMWare
- Make sure USB is set to 3.1

## Connectiong USB in virtual box
- Make sure the USB adapter is set to USB 3
- Once connected to your VM

# <a name="docker"></a>Setting up the Docker Development Enviroment
To setup the developement enviroment the following steps must be performed

Install docker - Follow the instructions listed below
- [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/)

Clone the github repository
```bash
$ git clone https://github.com/fsherratt/upgraded-parakeet.git
```
Build the docker container, this may take a while
```bash
$ cd upgraded-parakeet
$ docker build --tag tbd-erl .
```
Launch a docker container. The `--mount` flag can be used to connect host OS directories to the docker container, see more here [_Use bind mounts_](https://docs.docker.com/storage/bind-mounts/). The below commands mounts the current working directory to `workspaces/upgraded-parakeet` in the docker container.
```bash
$ docker run \
    -it \
    --name devtest \
    --mount source="$(pwd)",target=/workspaces/upgraded-parakeet,type=bind \
    tbd-erl
```

## Accessing Host USB Devices
To allow a docker container to access host USB device it must be running in an elevated privilieged mode, this can be achieved using the `--privileged` flag.
```bash
$ docker run --privileged ...
``` 

## Displaying Graphics from Docker
The following Docker options lines connect the host X11 server to the docker enviroment, _tested on Ubunutu 18.04_. This is useful for visualising results using commands such as `cv2.imshow`.
```bash
--env DISPLAY=${localEnv:DISPLAY} \
--mount source=/dev,target=/dev,type=bind \
--mount source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind \
```
The following line must be run in the docker host OS to allos external access to the host X11 service. It must be run in the after each restart
```bash
$ xhost +
access control disabled, clients can connect from any host
```

# <a name="vscode"></a>Using VSCode for Development
The `ms-vscode-remote.remote-containers` extension allows VSCode to initialise and control Docker containers. See [devcontainer.json]() for an example docker container

### VSCode settings
The [settings.json]() contains an example settings file