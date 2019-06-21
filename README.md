# PyFEA

Christophe Foyer 2019 | [www.cfoyer.com](https://www.cfoyer.com)

## About
A collection of scripts showing my attempts to produce usable meshes for FEA using python. 
Hoping to make this somewhat pleasant to use eventually, and to model a few things using the mesh.

## Current progress
- Crude interfacing with [gmsh](http://gmsh.info/) for 3D mesh generation then parsed using [gmsh_interop](https://github.com/inducer/gmsh_interop/tree/master/gmsh_interop) (extracted from [meshpy](https://github.com/inducer/meshpy))
- Generating VTK files from STL files (main.py)
- Generating meshes from STP files

![Current state](screenshots/meshing.png)

## To Do
- Interface with the [gmsh api](https://gitlab.onelab.info/gmsh/gmsh/blob/master/api/gmsh.py) directly (for better support)
- Efficiently order data to support an irregular matrix (ideally with numpy compatibility)
- Create easy way to interact with elements and set up multi-sim problems
