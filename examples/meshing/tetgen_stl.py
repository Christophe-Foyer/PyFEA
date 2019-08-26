"""
A simple example showing how to use the tetgen interface.
"""

from pyfea.fea.geometry import EntityMesh, SurfaceMesh
from pyfea.interfaces.meshing import tetgen_interface

filename = '../testfiles/ExampleWingGeom.stl'
    
sm = SurfaceMesh(filename = filename)
    
#The "with" is not important here but easier to just do it for all of them
with tetgen_interface() as geo:
    grid = geo.gen_mesh_from_surf(sm.gen_stl())
    
    em = EntityMesh()
    em.add_geometry(geo.points, geo.elements)
    
    em.plot()