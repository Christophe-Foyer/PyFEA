"""
A simple example showing how to use the gmsh interface for '.stl' files.
"""

from pyfea.fea.geometry import EntityMesh
from pyfea.interfaces.meshing import gmsh_interface

filename = '../testfiles/ExampleWingGeom.stl'

#The "with" is important because you probably want to close gmsh afterwards
with gmsh_interface() as geo:
    geo.set_element_size(0.25,0.75)
    geo.gen_mesh_from_surf(filename)
    geo.extract_geometry()
    
    #generate python object
    em = EntityMesh()
    em.add_geometry(geo.points, geo.elements)
#    em.export_vtk('out.vtk')
    
    em.plot()
    
#or add geo.__exit__() if you initialize it as geo = gmsh_interface()