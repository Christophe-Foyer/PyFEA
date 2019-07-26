import onelab.lib.gmsh as gmsh
import numpy as np
import pyvista as pv
import meshio
from pyfea.tools.plotting import scatter3d

#import logging
#logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')
        
class EntityMesh:
    
    nodes = None
    tets = None
    elements = []
    adjacent = []
    
    def __init__(self):
        pass
        
    def gen_elements(self):
        for row in self.tets:
            tet = Tetrahedron(row,self.nodes)
            self.elements.append(tet)
            
    def add_geometry(self, nodes, tets, autogen=True):
        assert np.array(nodes).shape[1] == 3, "nodes must be a numpy array with dims (*,3)"
        assert np.array(tets).shape[1] == 4, "tets must be a numpy array with dims (*,4)"
        self.nodes = nodes
        self.tets = tets
        
        if autogen:
            self.gen_elements()
            
    def get_adjacent(self):
        assert self.elements, 'please generate elements first eg. "mesh.gen_elements()"'
        #now find adjacent elements
            
    vtk_filename = None
    def export_vtk(self, filename):
        meshio.write_points_cells(filename, self.nodes, {'tetra': self.tets})
        self.vtk_filename = filename
    
    #pyvista
    def plot_vtk(self, file=None):
        if not file: file = self.vtk_filename
        data = pv.read(file)
        plotter = pv.Plotter()  # instantiate the plotter
        plotter.add_mesh(data)    # add a dataset to the scene
        plotter.show(auto_close=False)     # show the rendering window
        
    #Matplotlib
    def show_nodes(self):
        scatter3d(self.points)
        
class gmsh_interface:
    
    points=None
    elements=None
    
    def __init__(self, name='test'):
        gmsh.initialize()
        gmsh.option.setNumber("General.Terminal", 1)
        
        gmsh.model.add(name)
    
    def __enter__(self):
        pass
        
    def gen_mesh(self, filename):
        #TODO: add options to control how the mesh is generated
        gmsh.merge(filename)
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)
        
    def extract_geometry(self):
        #point cloud
        _, points, _ = gmsh.model.mesh.getNodes()
        self.points = points.reshape(( int(len(points)/3),3))
        
        elements = gmsh.model.mesh.getElements()
        elements = elements[2][list(elements[0]).index(4)]
        self.elements = elements.reshape(int(len(elements)/4),4)-1
        
    def output_mesh(self, filename='output.msh'):
        gmsh.write(filename)
        
    def __exit__(self, **kwargs):
        gmsh.finalize()

if __name__ == '__main__':
        
    #much of this should be integrated eventually
    print("GMSH_API_VERSION: v{}".format(gmsh.GMSH_API_VERSION))

    filename = '../../testfiles/test.stp'
    
    geo = gmsh_interface()
    geo.gen_mesh(filename)
    geo.extract_geometry()
    geo.output_mesh()
    
    #generate python object
    em = EntityMesh()
    em.add_geometry(geo.points, geo.elements)
    em.export_vtk('out.vtk')
    
    geo.__exit__()
    
    em.plot_vtk()