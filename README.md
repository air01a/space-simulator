# space-simulator : Rocket simulator
Python satellite simulator using kepler laws & newton (2D).

You can pilote the orbiter (orient, start/stop engine), see in real time the orbit transformation, and initiate atmosphere reentry.
Arrow left and right to orient the spacecraft, upper arrow to start engine, down arrow to stop, W,X,C to accelerate/slow down time and A&Q to zoom / unzoom.

Final goal is to be able to start a rocket from earth and go to the moon.
You can define your rocket multi stages parameters in a config file (see examples in rockets directory), define the environnement in the scenery directory (which planets and satellites, position) and customize auto pilot in the missions directory. 

This simulator is based on patched conic approximation (planets have a sphere of influence, and spacecraft are attracted by only one planet at a time), uses kepler equations (time propagation and display orbit), newton laws, delta v for motion, ...

As it is based on Sphere of influence, it only give a an approximation of the real trajectories.

## Curent working features

Display all parameters ("time;thrust;altitude;velocity;carburant;(perihelion,aphelion)")

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/data.png)

Show current trajectory (kepler equations)

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/trajectory.png)

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/trajectory2.png)

Manage Sphere of influence of other attractor and display future trajectory

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/trajectory3.png)

Propagate Kepler time equation to accelerate time

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/kepler_propagation.gif)

Simulate full solar system

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/fullsolarsystem.png)

Manage Drag Force in atmosphere, rocket multi staging, motors parameters, flight management (attitude change with altitude, speed, or perihelion/aphelion), change attractor (moon / earth).

## In progress

Organize and optimize code (at the beginning, this was just a small test to understand kepler equations)


