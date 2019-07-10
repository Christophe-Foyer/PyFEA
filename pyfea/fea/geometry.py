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
    
    def __init__(self):
        pass
        
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
            
    def get_adjacent(self): #WIP
        assert self.elements, 'please generate elements first eg. "mesh.gen_elements()"'
        
        #TODO: vectorize
        adjacent = []
        for tet in self.elements:
            adjacent.append(tet.get_neighbors(self.tets))
        self.adjacent = adjacent
            
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