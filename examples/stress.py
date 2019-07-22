# -*- coding: utf-8 -*-

from pyfea.fea.geometry import EntityMesh
from pyfea.interfaces.meshing import gmsh_interface

#import pyfea
#import os
#modulepath = pyfea.__file__.rsplit('\\',2)[0]
#os.chdir(modulepath)

#get wing geometry

filename = 'testfiles/ExampleWingGeom.stl'

with gmsh_interface() as geo:
    geo.set_element_size(1,1.5)
    geo.gen_mesh_stl(filename)
    geo.extract_geometry()
    
    #generate python object
    em = EntityMesh()
    em.add_geometry(geo.points, geo.elements)
    em.export_vtk('out.vtk')
    em.plot_vtk()

