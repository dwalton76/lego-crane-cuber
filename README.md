# lego-crane-cuber

## Server Installation (optional)
We use OpenCV to process the images captured by the web camera.  While it
is possible to do this on the EV3 it is pretty slow.  To work-around this we
setup a server that the EV3 will copy images to for processing. This is
optional though...you can run all of this on the EV3 with some patience.


### Installing rubiks-cube-tracker
We use a webcam to take a picture of all six sides of the cube. rubiks-cube-tracker
analyzes those images and finds the rubiks cube squares in each image. It returns
the mean RGB value for each square.
```bash
$ sudo pip install git+https://github.com/dwalton76/rubiks-cube-tracker.git
```

### Installing rubiks-color-resolver
When the cube is scanned we get the RGB (red, green, blue) value for
all 54 squares of a 3x3x3 cube.  rubiks-color-resolver analyzes those RGB
values to determine which of the six possible cube colors is the color for
each square.

Follow the install instructions at https://github.com/dwalton76/rubiks-color-resolver

### Installing rubiks-cube-NxNxN-solver
Follow the install instructions at https://github.com/dwalton76/rubiks-cube-NxNxN-solver
This is a solver for any size rubiks cube.

### Installing and running cranecuberd.py
```bash
$ cd ~/
$ sudo apt-get install git fswebcam python-pil python-opencv
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
$ cd ~/lego-crane-cuber
$ sudo ./crancecuberd.py
```


## Client Installation
Substitute the IP address of your server in place of x.x.x.x below
```bash
$ cd ~/
$ sudo apt-get install git fswebcam python-pil python-opencv
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
$ cd ~/lego-crane-cuber
$ echo 'x.x.x.x' > server.conf
$ ./crancecuber.py
```