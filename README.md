# lego-crane-cuber

## Server Installation
### Create the "robot" user
Create a user called 'robot' and login as 'robot' for the rest of the
steps in 'Server Installation'
```
$ sudo adduser robot
$ su robot
```

### Installing kociemba - 3x3x3 solver
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
$ sudo apt-get install python-pip
$ sudo pip install git+https://github.com/dwalton76/rubiks-square-extractor.git

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

### Installing 2x2x2, 4x4x4, 5x5x5, etc solvers
These solvers live in the lego-crane-cuber repository
```
$ cd ~/
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
```

4x4x4 solver install
```
$ cd ~/lego-crane-cuber/solvers/4x4x4/TPR-4x4x4-Solver/
$ ./make.sh
$ java -cp .:threephase.jar:twophase.jar solver UUURUUUFUUUFUUUFRRRBRRRBRRRBRRRBRRRDFFFDFFFDFFFDDDDBDDDBDDDBDDDLFFFFLLLLLLLLLLLLULLLUBBBUBBBUBBB
```

5x5x5 solver install...the first time it solves a cube it creates several
prune tables.  Creating these prune tables will take a while (more than
30 minutes) but you only have to do this once.

```
$ cd ~/lego-crane-cuber/solvers/5x5x5/
$ java -cp bin -Xmx8g justsomerandompackagename.reducer LLBUULLBUUDUUDDLLLBBLLURRDDUUBDDUUBDDDFFDDFBBDDFBBFLRBBFLRBBBBRDDDDLRRDDLRRFFLFFRRLDDRRLBBRRBRRRRBRRUULUUFFLUUUUFRRBBFFLBBFFLLLLDDLLDFFFFBUUUURFFUURFF
```

## Client Installation
### Installing lego-crane-cuber
```
$ cd ~/
$ git clone https://github.com/dwalton76/lego-crane-cuber.git
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
