# -*- coding: utf-8 -*-

import numpy as np
import pyvista as pv
import meshio
from pyfea.tools.plotting import scatter3d

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