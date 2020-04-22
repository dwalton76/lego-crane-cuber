# lego-crane-cuber

You will install software in two places
* EV3
* laptop

We do this to offload some of the CPU intenstive work. We could run
everything on the EV3 but it is only 300Mhz and 64M of RAM so it takes
a very long time to do the image analysis of the pictures from the webcam.

## EV3 Installation
### Installing lego-crane-cuber
Substitute the IP address of your laptop in place of x.x.x.x below
```
$ cd ~/
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
$ cd ~/lego-crane-cuber
$ echo 'x.x.x.x' > server.conf
```

## Laptop Installation
### Create a python virtual environment
We will create a python virtual environment (via `make init`) where we will
install the various packages that are needed. `make init` will also install:
* https://github.com/dwalton76/rubiks-cube-tracker
* https://github.com/dwalton76/rubiks-color-resolver
```
$ make init
$ source ./venv/bin/activate
```

### Installing the solver
A solver for various size cubes is available at https://github.com/dwalton76/rubiks-cube-NxNxN-solver
You must install the rubiks-cube-NxNxN-solver solver


### Run cranecuberd.py
The webcam should be connected to your laptop. If your webcam is `/dev/video0`
you should run:
```
$ sudo ./cranecuberd.py --video 0
```

## EV3 -> Laptop communication
With `cranecuberd.py` running on your laptop, on your EV3 run:
```
$ ./cranecuber.py
```

You should see some `PING` output where the EV3 verifies it can communicate
with the laptop.
