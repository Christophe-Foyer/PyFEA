# PyFEA

Christophe Foyer 2019 | [www.cfoyer.com](https://www.cfoyer.com)

## About
A collection of scripts showing my attempts to produce usable meshes for FEA using python. 
Hoping to make this somewhat pleasant to use eventually, and to model a few things using the mesh.

## Current progress
- Crude interfacing with [gmsh](http://gmsh.info/) for some 3D mesh generation then parsed using [gmsh_interop](https://github.com/inducer/gmsh_interop/tree/master/gmsh_interop) (part of [meshpy](https://github.com/inducer/meshpy) by Andreas Klöckner)
- Can generate VTK files from STL files (main.py)
- Can generate meshes from STP files

![Current state](screenshots/meshing.png)
