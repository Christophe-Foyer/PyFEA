import onelab.lib.gmsh as gmsh

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')

print("GMSH_API_VERSION: v{}".format(gmsh.GMSH_API_VERSION))

filename = '../testfiles/test.stp'

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

gmsh.model.add("test")

#TODO: add options to control how the mesh is generated
gmsh.merge(filename)
gmsh.model.geo.synchronize()
gmsh.model.mesh.generate(3)
#gmsh.model.mesh.refine()

#plot point cloud
_, points, _ = gmsh.model.mesh.getNodes()
points = points.reshape(( int(len(points)/3),3))
from plotting import scatter3d
scatter3d(points)

elements = gmsh.model.mesh.getElements()
elements = elements[2][list(elements[0]).index(4)]
elements = elements.reshape(int(len(elements)/4),4)-1

import meshio
meshio.write_points_cells('out.vtk', points, {'tetra': elements})

gmsh.write('output.msh')
gmsh.finalize()