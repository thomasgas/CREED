# CREED 
## CTA Rendering Event by Event Display

**NOTE: The code is almost working...try it at your own risk! :D**

**TODO: now displaying only LSTs and MSTs...need to add the SSTs**

### Description
This is a set of functions and utilities for the rendering of an event as seen by the telescopes of the Cherenkov Telescope Array: this project uses the [SolidPython](https://github.com/SolidCode/SolidPython) library, which can be used to create any rendering in OpenSCAD from Python.
These routines uses **ctapipe** to perform the analysis (import simtel file, extract telescopes positions, calibration, tailcut cleaning, etc...).

### How to run 
The code is intend to be a simple tool to understand how the different reference frames works in ctapipe and how the event on the camera is related to the position of the telescope on the ground. The code is made by two main programs:

- **3Dmodels.py**. Usage: `python 3Dmodels.py simtelfile`

This program can be used to render the telescopes, the cameras, the reference frames on the ground and on the camera, the event on the camera, the impact point on the ground.

**WIP: - 3dground.py**. Usage: `python 3Dground.py simtelfile`

This program is intended just to understand how the reference frames on the ground works: the telescopes are plotted on the *ground* and on the *tilted* reference frames.

### Visualization
Once you have a `.scad` file you just need to visualize it with [OpenSCAD](http://www.openscad.org/), which is available for every platform and OS. See details in the website.
