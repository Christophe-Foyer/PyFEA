# -*- coding: utf-8 -*-

import numpy as np
import pyvista as pv
import meshio
from pyfea.tools.plotting import scatter3d

class Tetrahedron:
    
    points = np.array([None]*4)
    pointcloud = None
    neighbors = None
    entity_mesh = None
    
    def __init__(self, points, pointcloud, entity_mesh=None):
        assert len(points)==4, "Point array must be of length 4"
        assert max(points)<len(pointcloud), "Points must be within pointcloud length"
        self.points = np.array(points)
        self.entity_mesh = entity_mesh
        
    def get_coords(self):
        assert self.points
        assert self.pointcloud
        return np.array(self.pointcloud)[self.points]
        
    def get_cog(self):
        return np.mean(self.get_coords())
    
    def get_neighbors(self, tets=None):
        """
        Find neighboring tets
        """
        
        #make sure the tet has access to the list of possible neighbors
        assert tets or \
               (isinstance(self.entity_mesh, EntityMesh)
                and self.entity_mesh.tets), \
               'Tetrahedron needs access to tets list (via argument or Tetrahedron.entity_mesh)'
               
        #vectorized neighbor finder
        arr = np.concatenate((np.tile(self.points, (len(tets),1)),tets),axis=1)
        check = np.apply_along_axis(lambda x: len(set(x))==5, 1, arr)
        self.neighbors = np.nonzero(check)
        
        return self.neighbors
    
class EntityMesh:
    
    nodes = None
    tets = None
    elements = []
    adjacent = []
    surface_mesh = None
    
    def __init__(self, surface_mesh=None):
        if surface_mesh:
            self.surface_mesh = surface_mesh
        
    def gen_elements(self):
        for row in self.tets:
            tet = Tetrahedron(row, self.nodes, self)
            self.elements.append(tet)
            
    def add_geometry(self, nodes, tets, autogen=True):
        assert np.array(nodes).shape[1] == 3, "nodes must be a numpy array with dims (*,3)"
        assert np.array(tets).shape[1] == 4, "tets must be a numpy array with dims (*,4)"
        self.nodes = nodes
        self.tets = tets
        
        if autogen:
            self.gen_elements()
            
    def set_surface_mesh(self, surface_mesh, autogen = True):
        assert isinstance(surface_mesh, SurfaceMesh)
        self.surface_mesh = surface_mesh
        
        if autogen:
            self.gen_mesh_from_surf()
            
    def get_adjacent(self): #WIP
        assert self.elements, 'please generate elements first eg. "mesh.gen_elements()"'
        
        #TODO: vectorize more (toplevel loop here)
        adjacent = []
        for tet in self.elements:
            adjacent.append(tet.get_neighbors(self.tets))
        self.adjacent = adjacent
            
    vtk_filename = None
    def export_vtk(self, filename):
        meshio.write_points_cells(filename, self.nodes, {'tetra': self.tets})
        self.vtk_filename = filename
        
    #TODO: Fix this
    def merge(self, entities=[], include_self=True, autogen=True):
        assert type(entities)==list
        assert all([isinstance(x, EntityMesh) for x in entities])
        
        #add itself to the list
        if include_self: entities.append(self)
        
        #TODO: should remesh with gmsh instead of just appending
        self.nodes = np.vstack([x.nodes for x in entities])
        self.tets = np.vstack([x.tets for x in entities])
        
        if autogen:
            self.gen_elements()
    
    def gen_mesh_from_surf(self, tempfile=None, surface_mesh=None, autogen=True):
        """
        creates an entitymesh from a surface mesh (STL-like)
        also creates an STL temp file (could be useful later on)
        """
        
        if surface_mesh: self.surface_mesh = surface_mesh
        assert self.surface_mesh, 'Please define a surface_mesh first'
        
        #tri = self.surface_mesh.tri
        #points = self.surface_mesh.points
        
        #create temp STL
        #TODO: use special tempfile tool
        if not tempfile: tempfile = r'geo.temp.stl'
        surface_mesh.gen_stl(tempfile)
        
        from pyfea.interfaces.gmsh import gmsh_interface
        
        #use gmsh to run STL tet meshing
        with gmsh_interface() as geo:
            #set element size
            geo.set_element_size(1,1.5)
        
            #read temp file
            try:
                geo.gen_mesh_stl(tempfile)
            except ValueError:
                raise ValueError('Merge failed, is the geometry defined? Please check input file.')
            geo.extract_geometry()
        
            self.add_geometry(geo.points, geo.elements)
        
        if autogen == True:
            self.gen_elements()
        
    #pyvista
    def plot_vtk(self, file=None):
        #TODO: fix need for VTK file
        if not file: file = self.vtk_filename
        if not file: 
            print('No vtk file generated, skipping vtk plotting')
            print('Run "EntityMesh.export_vtk" first')
            return
        data = pv.read(file)
        plotter = pv.Plotter()  # instantiate the plotter
        plotter.add_mesh(data)    # add a dataset to the scene
        plotter.show(auto_close=False)     # show the rendering window
        
    #Matplotlib
    def show_nodes(self):
        scatter3d(self.points)
            
class SurfaceMesh:
    
    points=None
    tri=None
    
    def __init__(self, points=None, tri=None, filename=None):
        if ((type(points) == np.ndarray or
             type(points) == list) and
            (type(tri) == np.ndarray or
             type(tri) == list)):
            self.points = np.array(points)
            self.tri = np.array(tri)
        elif filename:
            self.read_stl(filename)
        
    def plot(self):
        # for testing
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        import matplotlib.pyplot as plt
        
        points_3d = self.points[self.tri]
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.add_collection3d(Poly3DCollection(points_3d, linewidths=1))
        
#        plt.draw()
        plt.show()
        
    def gen_stl(self, tempfile='temp.stl'):
        from stl import mesh #numpy-stl
        
        my_mesh = mesh.Mesh(np.zeros(self.tri.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.tri):
            for j in range(3):
                my_mesh.vectors[i][j] = self.points[f[j],:]
        
        my_mesh.save(tempfile)
        
        return tempfile
        
    def read_stl(self, filename):
        from stl import mesh
        
        mesh = mesh.Mesh.from_file(filename)
        points = np.unique(mesh.points.reshape(mesh.points.shape[0]*3, 3), axis=0)
        tri = [[points.tolist().index(x[0:3].tolist()),
                points.tolist().index(x[3:6].tolist()),
                points.tolist().index(x[6:9].tolist())]
               for x in mesh.points]  
        
        self.points = np.array(points)
        self.tri = np.array(tri)