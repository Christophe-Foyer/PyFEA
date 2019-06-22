import onelab.lib.gmsh as gmsh

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')

print("GMSH_API_VERSION: v{}".format(gmsh.GMSH_API_VERSION))


gmsh.initialize()

#gmsh.option.setNumber("General.Terminal", 1)
#gmsh.option.setNumber("Mesh.Algorithm", 5) # delquad
#gmsh.option.setNumber("Mesh.RecombineAll", 1)
#
#gmsh.model.add("square")
#gmsh.model.geo.addPoint(0, 0, 0, 0.6, 1)
#gmsh.model.geo.addPoint(1, 0, 0, 0.6, 2)
#gmsh.model.geo.addPoint(1, 1, 0, 0.5, 3)
#gmsh.model.geo.addPoint(0, 1, 0, 0.4, 4)
#gmsh.model.geo.addLine(1, 2, 1)
#gmsh.model.geo.addLine(2, 3, 2)
#gmsh.model.geo.addLine(3, 4, 3)
## try automatic assignement of tag
#line4 = gmsh.model.geo.addLine(4, 1)
#gmsh.model.geo.addCurveLoop([1, 2, 3, line4], 1)
#gmsh.model.geo.addPlaneSurface([1], 6)
#gmsh.model.geo.synchronize()
#gmsh.model.mesh.generate(2)
#gmsh.write("square.unv")

filename = '../testfiles/test.stp'

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)

gmsh.model.add("test")

gmsh.merge(filename)
gmsh.model.geo.synchronize()
gmsh.model.mesh.generate(3)
gmsh.write('output.msh')
gmsh.finalize()