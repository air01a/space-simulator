# space-simulator : Rocket simulator
Python satellite simulator using newton &amp; kepler

Python satellite simulator using kepler laws & newton (2D).

You can pilote the orbiter (orient, start/stop engine), see in real time the orbit transformation, and initiate atmosphere reentry.
Arrow left and right to orient the spacecraft, upper arrow to start engine, down arrow to stop, W,X,C to accelerate/slow down time and A&Q to zoom / unzoom.

Final goal is to be able to start a rocket from earth and go to the moon.


## Curent working features

Display all parameters ("time;thrust;altitude;velocity;carburant;(perihelion,aphelion)")

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/data.png)

Show current trajectory (kepler equations)

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/trajectory.png)

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/trajectory2.png)

Propagate Kepler time equation to accelerate time

![](https://raw.githubusercontent.com/air01a/space-simulator/main/screenshots/kepler_propagation.gif)

Manage Drag Force in atmosphere, rocket multi staging, motors parameters, flight management (attitude change with altitude, speed, or perihelion/aphelion), change attractor.

## Curent working features

Take into account lift and improve drag

Load spacecraft and mission control through json

Attractor with children, sphere of influence, solar system modelisation

Hohmann transfer calculator

Graphic improvment (not a priority)

Organize and optimize code (at the beginning, this was just a small test to understand kepler equations)


