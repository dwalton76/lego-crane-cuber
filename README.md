# lego-crane-cuber

## Client Installation
### Installing lego-crane-cuber
```
$ cd ~/
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
```


## Server Installation
### Installing kociemba
The kociemba program produces a sequence of moves used to solve
a 3x3x3 rubiks cube.
```
$ sudo apt-get install build-essential libffi-dev
$ cd ~/
$ git clone https://github.com/dwalton76/kociemba.git
$ cd ~/kociemba/kociemba/ckociemba/
$ make
$ sudo make install
```

### Installing rubiks-square-extractor
We use a webcam to take a picture of all six sides of the cube. rubiks-square-extractor
analyzes those images and finds the rubiks cube squares in each image. It returns
the mean RGB value for each square.
```
$ sudo pip3 install git+https://github.com/dwalton76/rubiks-square-extractor.git

```

### Installing rubiks-color-resolver
When the cube is scanned we get the RGB (red, green, blue) value for
all 54 squares of a 3x3x3 cube.  rubiks-color-resolver analyzes those RGB
values to determine which of the six possible cube colors is the color for
each square.
```
$ sudo apt-get install python3-pip
$ sudo pip3 install git+https://github.com/dwalton76/rubiks-color-resolver.git
```

### Installing java
The solvers for 4x4x4 and 5x5x5 are written in java
```
$ sudo apt-get install default-jre openjdk-7-jdk
```

