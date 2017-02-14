# lego-crane-cuber

## Server Installation
We use OpenCV to process the images captured by the web camera.  While it
is possible to do this on the EV3 it is pretty slow.  To work-around this we
setup a server that the EV3 will copy images to for processing.

We also offload the task of computing the solution for the cube. It is possible
to compute the solution for a 2x2x2 and 3x3x3 on an EV3 but the solvers for 4x4x4
and 5x5x5 require too much CPU and memory to run on an EV3.

### Create the "robot" user
Create a user called 'robot' and login as 'robot' for the rest of the
steps in 'Server Installation'
```
$ sudo adduser robot
$ su robot
$ sudo apt-get install python-pip python3-pip
```

### Installing rubiks-cube-tracker
We use a webcam to take a picture of all six sides of the cube. rubiks-cube-tracker
analyzes those images and finds the rubiks cube squares in each image. It returns
the mean RGB value for each square.
```
$ sudo pip install git+https://github.com/dwalton76/rubiks-cube-tracker.git

```

### Installing rubiks-color-resolver
When the cube is scanned we get the RGB (red, green, blue) value for
all 54 squares of a 3x3x3 cube.  rubiks-color-resolver analyzes those RGB
values to determine which of the six possible cube colors is the color for
each square.
```
$ sudo pip3 install git+https://github.com/dwalton76/rubiks-color-resolver.git
```

### Installing solvers
Solvers for various size cubes are available at https://github.com/dwalton76/rubiks-cube-solvers
Please follow the README instructions there to install the solvers you are interested in.


## Client Installation
### Installing lego-crane-cuber
Substitute the IP address of your server in place of x.x.x.x below
```
$ cd ~/
$ sudo apt-get install git
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
$ cd ~/lego-crane-cuber
$ echo 'x.x.x.x' > server.conf
```

## Client/Server SSH Installation
The 'robot' user on the client needs the ability to ssh to the server without
entering a password.  The following guide gives instructions on how to do so.
In this guide the "local-host" is the client machine and the "remote-host"
is the server.

http://www.thegeekstuff.com/2008/11/3-steps-to-perform-ssh-login-without-password-using-ssh-keygen-ssh-copy-id

Verify that this works by sshing from the client to the server, if it prompts
you for a password you missed a step somewhere.
```
$ ssh -l robot SERVER_IP
```
