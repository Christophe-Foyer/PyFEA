# -*- coding: utf-8 -*-

from pyfea.fea.geometry import SurfaceMesh, Part, Assembly

filenames = [
             '../testfiles/scramjet/Air.stl',
             '../testfiles/scramjet/Body.stl',
             '../testfiles/scramjet/Fuel outlet.stl'
             ]

surfaces = []
parts = []
for _filename in filenames:
    print('Generating mesh for file: ' + _filename)
    
    sm = SurfaceMesh(filename = _filename)
    surfaces.append(sm)
    em = Part(surface_mesh=sm)
    parts.append(em)
    em.gen_mesh_from_surf(meshing='gmsh', element_size=(10,25))

assembly = Assembly(parts)

#plot the solid
plotter = assembly.plot(style=None, opacity=0.5)
#plot the wireframe
#plotter = assembly.plot(plotter=plotter, color='b', opacity=0.25)
plotter = assembly.parts[1].plot(plotter=plotter, style=None, opacity=0.75)
#plotter = assembly.parts[1].plot(plotter=plotter, color='blue', opacity=0.25)
plotter = assembly.parts[1].elements[0].plot(plotter=plotter, style=None, opacity=0.75)
