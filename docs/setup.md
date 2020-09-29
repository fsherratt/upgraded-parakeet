# Development Enviroment Setup
This docuemnent contains instructions on how to setup development enviroment for the TBDr ERL codebase. These instructions have been tested on Windows 10 and Ubuntu 18.04.

## Table of Contents
- [Useful Links](#useful)
- [Setting up a VM on Windows](#windows)
- [Docker Development Enviroment](#docker)
- [Using VSCode for Development](#vscode)
- [Next Steps](#steps)

# <a name="useful"></a>Useful Links
- [Docker overview](https://docs.docker.com/get-started/overview/)
- [Oracle VirtualBox](https://www.virtualbox.org/)
- [VSCode IDE](https://code.visualstudio.com/)
- [Ubuntu 18.04](https://releases.ubuntu.com/18.04/)

# <a name="windows"></a>Setting up a Virtual Machine on Windows
To install a VM on windows follow the instructions below:
1. Download and install [Oracle VirtualBox](https://www.virtualbox.org/)
1. Download the latest Ubuntu 18.04 .iso [here](https://releases.ubuntu.com/18.04/)
1. Disable Microsoft Hyper-v if enabled, see below
1. Follow instructions for setting up virtual machine, [here](https://brb.nci.nih.gov/seqtools/installUbuntu.html)
1. If using realsense cameras setup USB connections as below
1. Follow developement enviroment setup, [see below](#docker)
1. Do cool stuff

## Disable Hyper-v
In the start menu search for `Turn windows features on or off`. In the list make sure `Hyper-V -> Hyper-V Platform -> Hyper-V Hypervisors` is deselected as below, then restart your computer.

[<img src="images/disable-hyper-v.png" width="300"/>](images/disable-hyper-v.png)

<!-- ## Connecting USB in VMWare
Make sure USB is set to 3.1. Then once the VM is turned on connect to the USB device throught the `VM -> Removable Devices` menu. See below

[<img src="images/set_usb_vmware_cropped.png" width="300"/>](images/set_usb_vmware.png) [<img src="images/Connect_Realsense_VMWare.png" width="300"/>](images/Connect_Realsense_VMWare.png) -->

## Connectiong USB Devices in Virtual Box
In the setting menu of the VM make sure the USB adapter is set to USB 3. Turn on your VM and once connected you can pass through a USB connecting through the `Devices -> USB` menu. The `lsusb` command can be run to confirm the USB device has been detected in the VM. 

[<img src="images/set_usb_virtualbox_cropped.png" width="300"/>](images/set_usb_virtualbox.png) [<img src="images/Connect_Realsense_VirtualBox.png" width="300"/>](images/Connect_Realsense_VirtualBox.png)

# <a name="docker"></a>Docker Development Enviroment
Project developement is undertaken in a docker enviroment. Docker gives a consistent devopment enviroment for everyone reducing the setup time significantly. To setup the developement enviroment follow the steps below:

1. Install docker - Follow the instructions listed below
    - [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
    - [Post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/)

2. Clone the github repository
    ```bash
    $ git clone https://github.com/fsherratt/upgraded-parakeet.git
    ```

3. Build the docker container, get a drink this may take a while. 
    ```bash
    $ cd upgraded-parakeet
    $ sudo docker build --tag tbd-erl .
    ```
    The docker file is built according to the instructions provided by a Dockerfile, in this case the file in the root directory of the repository, [Dockerfile](../Dockerfile).

4. Launch the docker container using `run` command and begin playing.
    ```bash
    $ sudo docker run --name erl_dev -it tbd-erl
    ```

## Docker Commands
Some notes on the above command. The `-it` flag launces it as an interative terminal session. Alternatively the `-d` can be used to start a dettached process. The `--name` flag allows friendly names to be specified for the contianer instance. If ommited a generated name is used instead.

### Accessing files
The `--mount` flag can be used to connect host OS directories to a docker container, more info here [_Use bind mounts_](https://docs.docker.com/storage/bind-mounts/). Using the command below a folder can be mounted to `workspaces/upgraded-parakeet` directory.
```bash
$ sudo docker run \
    --mount source=[PATH_TO_UPGRADED_PARAKEET],target=/workspaces/upgraded-parakeet,type=bind \
    ... \
    tbd-erl 
```

### Accessing Host USB Devices
To allow a docker container to access host USB device it must be running in an elevated privilieged mode, this can be achieved using the `--privileged` flag. More details on the flag are available here [Priviege Mode](https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities)
```bash
$ sudo docker run --privileged ...
``` 

### Displaying Graphics from Docker
Docker is a command line only enviroment so in order to display graphics suitable resource must be presented to it. The following Docker options lines connect the host X11 server to the docker enviroment, _tested on Ubunutu 18.04_. This is useful for visualising results using commands such as `cv2.imshow`.
```bash
$ sudo docker run \
    --env DISPLAY \
    --mount source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind \
    ...
```
<!-- --mount source=/dev,target=/dev,type=bind \ -->
The following line must be run in the docker host OS to allos external access to the host X11 service. It must be run in the after each restart
```bash
$ xhost +
access control disabled, clients can connect from any host
```

### Controlling containers
To list all available containers use the `ps` command, [_docker ps_](https://docs.docker.com/engine/reference/commandline/ps/). The `-a` flag list all containers including those that aren't currently running
```bash
$ docker ps -a
```

To start a stopped container the docker `start` command can be used, [_docker start_](https://docs.docker.com/engine/reference/commandline/start/)
```bash
sudo docker start -d erl_dev
```

To connect to a running container the `attach` command can be used, [_docker attach_](https://docs.docker.com/engine/reference/commandline/attach/)
```bash
sudo docker attach erl_dev
```

To stop a running container, you guessed it... The stop command is used, [_docker stop_](https://docs.docker.com/engine/reference/commandline/stop/)
```bash
sudo docker stop erl_dev
```

### Complete Command
```bash
$ sudo docker run -d \
    --name erl_dev
    --privileged \
    -env DISPLAY \
    --mount source=[PATH_TO_UPGRADED_PARAKEET],target=/workspaces/upgraded-parakeet,type=bind \
    --mount source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind \
    tbd-erl
```

Additional commands see [_Command-line reference_](https://docs.docker.com/engine/reference/commandline/docker/)

# <a name="vscode"></a>Using VSCode for Development
As an alternative to command line Microsoft's [VSCode IDE](https://code.visualstudio.com/) can be used. 

## VSCode setup
The [_ms-vscode-remote.remote-containers_](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension allows VSCode to initialise and control Docker containers removing the need for many of the above commands. Once VSCode is installed follow the link above or search for `remote containers` in the extensions tab.

VSCodes interation with the repository Dockerfile container is specified in the `.devcontainer/devcontainer.json` file. As a starter for this repsoitory see here: [_devcontainer.json_](example/devcontainer.json)

Many more details can be found here [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview).

Additionaly IDE settings can be set using specified using the `.vscode/settings.json` file. An example settings file for this project can be found here [_.vscode/_settings.json_](example/settings.json).

# <a name="useful"></a>Next Steps
Now you have a working development enviroment setup you can follow the other documentation to get started with the project.

- For launching modules see the [startup](startup.md) documentation.
- For details of simulation enviroments see [...](#)

