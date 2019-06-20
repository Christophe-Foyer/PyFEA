# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 19:09:59 2019

@author: Christophe
"""

from meshpy.tet import MeshInfo, build, Options

#mesh_info = MeshInfo()
#mesh_info.set_points([
#    (0,0,0), (2,0,0), (2,2,0), (0,2,0),
#    (0,0,12), (2,0,12), (2,2,12), (0,2,12),
#    ])
#mesh_info.set_facets([
#    [0,1,2,3],
#    [4,5,6,7],
#    [0,4,5,1],
#    [1,5,6,2],
#    [2,6,7,3],
#    [3,7,4,0],
#    ])

import numpy as np
from stl import mesh
#from mpl_toolkits import mplot3d
#from matplotlib import pyplot
import os
#figure = pyplot.figure()
#axes = mplot3d.Axes3D(figure)
stl_mesh = mesh.Mesh.from_file(os.getcwd() + '\\Peace.stl')
#axes.add_collection3d(mplot3d.art3d.Poly3DCollection(stl_mesh.vectors))
# Auto scale to the mesh size
#scale = stl_mesh.points.flatten(-1)
#axes.auto_scale_xyz(scale, scale, scale)
# Show the plot to the screen
#pyplot.show()

points = []
for _tri in stl_mesh.vectors:
    points = points + [tuple(x) for x in [_tri[0],_tri[1],_tri[2]]]

uniques = np.unique(points, axis=0)

#This needs significant speedup
panels = []
for _tri in stl_mesh.vectors:
    _tripnt = []
    for _index in range(len(uniques)):
        if list(uniques[_index]) in list(list(x) for x in _tri):
            _tripnt.append(_index)
    panels.append(tuple(_tripnt))

mesh_info = MeshInfo()
mesh_info.set_points(points)
mesh_info.set_facets(panels)

### Plotting
points = np.array(mesh_info.points)
from plotting import scatter3d
scatter3d(points)

##
mesh = build(mesh_info, options=Options(""))
#mesh = build(mesh_info, options=Options("pq"))
mesh.write_vtk("test.vtk")