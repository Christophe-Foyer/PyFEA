import onelab.lib.gmsh as gmsh

import numpy as np

#import logging
#logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')

class Tetrahedron:
    
    points = np.array([None]*4)
    pointcloud = None
    
    def __init__(self, points, pointcloud):
        assert len(points)==4, "Point array must be of length 4"
        assert max(points)<len(pointcloud), "Points must be within pointcloud length"
        self.points = points
        
    def get_coords(self):
        pass
        
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
        assert elements, 'please generate elements first eg. "mesh.gen_elements()"'
        #now find adjacent elements
            
    def export_vtk(self, filename):
        import meshio
        meshio.write_points_cells(filename, self.nodes, {'tetra': self.tets})
 
    def show_nodes(self):
        from plotting import scatter3d
        scatter3d(points)

if __name__ == '__main__':
        
    #much of this should be integrated eventually
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
    
    #point cloud
    _, points, _ = gmsh.model.mesh.getNodes()
    points = points.reshape(( int(len(points)/3),3))
    
    elements = gmsh.model.mesh.getElements()
    elements = elements[2][list(elements[0]).index(4)]
    elements = elements.reshape(int(len(elements)/4),4)-1
    
    #generate python object
    em = EntityMesh()
    em.add_geometry(points, elements)
    em.export_vtk('out.vtk')
    
    #output file and close gmsh
    gmsh.write('output.msh')
    gmsh.finalize()