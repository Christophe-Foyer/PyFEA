# -*- coding: utf-8 -*-

#from pyfea.fea.geometry import EntityMesh
from pyfea.interfaces.meshing import gmsh_interface

filename = '../testfiles/circletube.step'

#The "with" is important because you probably want to close gmsh afterwards
#with gmsh_interface() as geo:
if True:
    geo = gmsh_interface()

    geo.set_element_size(1,10000)
    assembly = geo.gen_mesh_from_assembly(filename)
    
    #plotter = assembly.plot(style=None, opacity=0.5)
    plotter = assembly.parts[0].plot(style=None, color='red', opacity=0.5)
    plotter = assembly.parts[1].plot(plotter = plotter, style=None, color='green', opacity=0.5)
    assembly.plot(plotter = plotter, color='blue')