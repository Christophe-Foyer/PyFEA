import onelab.lib.gmsh as gmsh
from pyfea.fea.geometry import EntityMesh

import math

#import logging
#logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')
        
class gmsh_interface:
    
    points=None
    elements=None
    
    def __init__(self, name='test'):
        gmsh.initialize()
        
        gmsh.model.add(name)
    
    def __enter__(self):
        return self
        
    def gen_mesh(self, filename):
        #TODO: add options to control how the mesh is generated
        gmsh.merge(filename)
#        gmsh.model.geo.addVolume([-1])
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)
        
    def refine(self):
        """
        TODO: Seems to throw memory access violation errors
        """
        pass
#        gmsh.model.mesh.refine()
        
    def set_options(self, minlength=0.75, maxlength=0.75):
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.option.setNumber("Mesh.Algorithm", 6);
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", minlength);
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", maxlength);
        
    def gen_mesh_stl(self, filename):
        gmsh.merge(filename)
        gmsh.model.mesh.classifySurfaces(40*math.pi/180., True, True)

        # create a geometry (through reparametrization) for all discrete curves and
        # discrete surfaces
        gmsh.model.mesh.createGeometry()
        
        # add a volume
        s = gmsh.model.getEntities(2)
        l = gmsh.model.geo.addSurfaceLoop([s[i][1] for i in range(len(s))])
        gmsh.model.geo.addVolume([l])
        
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)

    def display_mesh(self):
        gmsh.fltk.run()
        
    def extract_geometry(self):
        #point cloud
        _, points, _ = gmsh.model.mesh.getNodes()
        self.points = points.reshape(( int(len(points)/3),3))
        
        elements = gmsh.model.mesh.getElements()
        elements = elements[2][list(elements[0]).index(4)]
        self.elements = elements.reshape(int(len(elements)/4),4)-1
        
    def output_mesh(self, filename='output.msh'):
        gmsh.write(filename)
        
    def __exit__(self, *args):
        gmsh.finalize()

if __name__ == '__main__':
        
    #much of this should be integrated eventually
    print("GMSH_API_VERSION: v{}".format(gmsh.GMSH_API_VERSION))

    filename = 'testfiles/Peace.stl'
    
#    with gmsh_interface() as geo:
    geo = gmsh_interface()
    geo.set_options(1,1.5)
    geo.gen_mesh_stl(filename)
    geo.extract_geometry()
    
    geo.extract_geometry()
    
    #generate python object
    em = EntityMesh()
    em.add_geometry(geo.points, geo.elements)
    em.export_vtk('out.vtk')
    
    em.plot_vtk()
    
    geo.__exit__()