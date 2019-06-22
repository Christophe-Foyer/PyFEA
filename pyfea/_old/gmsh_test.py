# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 18:55:11 2019

@author: Christophe
"""

from gmsh_interop.reader import read_gmsh, GmshMeshReceiverNumPy
from meshpy.tet import MeshInfo
from meshpy.tet import build, Options

import numpy as np

#from gmsh_interop.runner import GmshRunner, FileSource
#
#source = FileSource('test.stp')
#
#runner = GmshRunner(source, target_unit='MM')
#runner.__enter__()

### Generate the mesh

#filename = 'ExampleWingGeom.stl'
filename = 'test.stp'
output = 'output.msh'

cmdline = ['gmsh ', filename, '-3', '-o', output, '-format', 'msh2']

print("%s" % " ".join(cmdline))
import os
from pytools.prefork import call_capture_output
retcode, stdout, stderr = call_capture_output("%s" % " ".join(cmdline), os.getcwd())

### Combine the MeshInfo class with the GmshMeshReceiver class
#A few changes needed to set variables

class MeshInfoReceiver(MeshInfo, GmshMeshReceiverNumPy):
    
    @property
    def points(self):
        return self._points
    @points.setter
    def points(self, value):
        self._points = value
        
    @property
    def elements(self):
        return self._elements
    @elements.setter
    def elements(self, value):
        self._elements = value

### Get the data and store it in the receiver
#This is a formatting problem that was solved by Andreas Klöckner at UIUC

mesh_info = MeshInfoReceiver()
read_gmsh(mesh_info, output)

### Plotting
points = np.array(mesh_info.points)
from plotting import scatter3d
scatter3d(points)

#remove funky panels?
mesh_info.elements = [x for x in mesh_info.elements if (len(x)==4)]

### Find neighbors and index them

#remove short ones
#elements = [x for x in mesh_info.elements if len(x)==4]
#
#neighbors = []*len(elements)
#for i, elem in enumerate(elements):
#    nbor = []
#    for j, elem2 in enumerate(elements):
#        if sum([(x in elem2) for x in elem]):
#            nbor.append(j)
#    neighbors.append(nbor)
#    print(i)

### Export to vtk
#This is not happy, might need to recode this myself
mesh = build(mesh_info, options=Options(""))
mesh.write_vtk("test.vtk")