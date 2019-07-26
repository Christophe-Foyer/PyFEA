# -*- coding: utf-8 -*-

import numpy as np
import pyvista as pv
import meshio
from pyfea.tools.plotting import scatter3d

import tempfile

class Tetrahedron:
    
    points = np.array([None]*4)
    pointcloud = None
    neighbors = None
    entity_mesh = None
    array_num = None
    
    def __init__(self, points, pointcloud,
                 entity_mesh=None,
                 array_num=None):
        assert len(points)==4, "Point array must be of length 4"
        assert max(points)<len(pointcloud), "Points must be within pointcloud length"
        
#        if array_num:
#            self.array_num = array_num
#        elif entity_mesh:
#            entity_mesh.tets.tolist().index(points.tolist())
        
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
        assert isinstance(surface_mesh, SurfaceMesh) or surface_mesh==None, \
            Exception('surface_mesh is of type: ' + str(type(surface_mesh)))
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
            
    def get_cog(self):
        return np.mean(self.nodes[self.points])
            
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
        return filename
        
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
            
    def gen_surface_mesh(self):
        print('WIP')
    
    def gen_mesh_from_surf(self,
                           tempfile=None,
                           surface_mesh=None,
                           autogen=True,
                           meshing='auto',
                           element_size = (0.0,10.0**22)):
        """
        creates an entitymesh from a surface mesh (STL-like)
        also creates an STL temp file (could be useful later on)
        """
        
        if surface_mesh: 
            self.surface_mesh = surface_mesh
        else:
            surface_mesh = self.surface_mesh
            
        assert self.surface_mesh, 'Please define a surface_mesh first'
        
        #tri = self.surface_mesh.tri
        #points = self.surface_mesh.points
        
        #create temp STL
        #TODO: use special tempfile tool
        if not tempfile: tempfile = r'geo.temp.stl'
        surface_mesh.gen_stl(tempfile)
        
        #automatically find new interfaces for meshing
        import inspect
        import pyfea.interfaces.meshing
        cls_meshing = inspect.getmembers(pyfea.interfaces.meshing, inspect.isclass)
        
        #TODO: this is poor form
        suffix = '_interface'
        engine_dict = {}
        for name, cls_mesh in cls_meshing:
            #should probably check it's in the right module too
            if name[-len(suffix):]==suffix \
               and cls_mesh.__module__ == 'pyfea.interfaces.meshing':
                tmp = {name[:len(name)-len(suffix)]:cls_mesh}
                engine_dict.update(tmp)
        
        assert type(meshing)==str or type(meshing)==list 
        
        if meshing == 'auto':
            engines = list(engine_dict.values())
            
        elif type(meshing)==str:
            engines = [ engine_dict[meshing] ]
            
        elif type(engines) == list:
            engines = []
            for string in meshing:
                engines.append(engine_dict[string])
        
        for engine in engines: #use engine to run STL tet meshing
            try:
                with engine() as geo:
                    #set element size
                    if any([x==None for x in element_size]):
                        geo.set_element_size()
                    else:
                        geo.set_element_size(element_size[0],element_size[1])
                
                    #read temp file
                    try:
                        geo.gen_mesh_from_surf(tempfile)
                    except ValueError:
                        raise ValueError('Merge failed, is the geometry defined? Please check input file.')
                    geo.extract_geometry()
                    
                    self.add_geometry(geo.points, geo.elements)
            except:
                print(Exception('Error with meshing engine'))
        
        if autogen == True:
            self.gen_elements()
        
    #pyvista
    def plot(self, filename=None, style='wireframe'):
        #TODO: fix need for VTK file
        
        if not filename and self.vtk_filename: 
            filename = self.vtk_filename
        else:
            filename = tempfile.TemporaryFile(suffix='.vtk').name
            print(filename)
            self.export_vtk(filename)
        
        data = pv.read(filename)
        plotter = pv.BackgroundPlotter()
#        plotter = pv.Plotter()  # instantiate the plotter
        plotter.add_mesh(data, style=style)    # add a dataset to the scene
        plotter.show()     # show the rendering window
        
    #Matplotlib
    def show_nodes(self):
        scatter3d(self.points)
            
class SurfaceMesh:
    
    points=None
    tri=None
#    normals = None
    
    def __init__(self, points=None, tri=None, filename=None):
        if ((type(points) == np.ndarray or
             type(points) == list) and
            (type(tri) == np.ndarray or
             type(tri) == list)):
            self.points = np.array(points)
            self.tri = np.array(tri)
#            self.gen_normals()
        elif filename:
            self.read_stl(filename)
            
#    def gen_normals(self):
#        print('WIP: janky solution for normals here')
#        
#        file = 'tmpstlfile.stl'
#        self.gen_stl(file)
#        self.read_stl(file)
#        import os
#        os.remove(file)
        
    def plot(self, normals = False):
        # for testing
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
        import matplotlib.pyplot as plt
        
        points_3d = self.points[self.tri]
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.add_collection3d(Poly3DCollection(points_3d, linewidths=1))
        
        if normals:
            ax.add_collection3d(Line3DCollection(points_3d, linewidths=1))
        
#        plt.draw()
        plt.show()
        
    def gen_stl(self, filename=None):
        from stl import mesh #numpy-stl
        
        if filename == None:
            filename = tempfile.TemporaryFile(suffix='.vtk').name
        
        my_mesh = mesh.Mesh(np.zeros(self.tri.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.tri):
            for j in range(3):
                my_mesh.vectors[i][j] = self.points[f[j],:]
        
        my_mesh.save(filename)
        
        return filename
        
    def read_stl(self, filename):
        from stl import mesh
        
        mesh = mesh.Mesh.from_file(filename)
        mpoints = mesh.points.reshape(mesh.points.shape[0]*3, 3)
        points = np.unique(mpoints, axis=0)
        tri = [[points.tolist().index(x[0:3].tolist()),
                points.tolist().index(x[3:6].tolist()),
                points.tolist().index(x[6:9].tolist())]
               for x in mesh.points]  
        
        self.points = np.array(points)
        self.tri = np.array(tri)
        
#        mpoints_o = mesh.points
#        self.normals = np.array(np.c_[mpoints_o, mpoints_o+mesh.normals])
        
class Part(EntityMesh):
    """
    Extends the EntityMesh class to include part properties such as materials.
    """
    
    material = None
    name = None
    
    def __init__(self, material = None, **kwargs):
        super(Part, self).__init__(**kwargs)
        
        self.material = material
        
class Assembly(EntityMesh):
    """
    Is used to compile multiple Part instances to calculate interactions
    """
    
    parts = []
    tetpart = None
    
    #sourcefile for existing assembly
    source_file = None
    
    def __init__(self, parts, **kwargs):
        
        assert 'surface_mesh' not in kwargs.keys(), \
            'incorrect argument: surface_mesh'
        
        #pass the arguments
        super(Assembly, self).__init__(**kwargs)
        
        self.parts = parts
        
#    def gen_elements(self):
#        for part in parts:
#            self.points
        
    def __getattribute__(self, name):
        
        disabled_methods = ['set_surface_mesh']
        
        if name in [disabled_methods]:
            raise AttributeError('Method: "' + name +
                                 '" is disabled for Assembly instances.')
        return super(Assembly, self).__getattribute__(name)
        
    #This needs to be replaced
    def get_cog(self):
        print('WIP')
        
    #this will need updating
    def plot(self, normals = False, style='wireframe'):
        
        plotter = pv.BackgroundPlotter()
        
        for part in self.parts:
            tmp = tempfile.TemporaryFile(suffix='.vtk').name
            part.export_vtk(tmp)
            
            data = pv.read(tmp)            
            plotter.add_mesh(data, style=style)
            
        plotter.show()
        
    def gen_from_source(self, filename, element_size = None):
        
        #only works with gmsh not tetgen
        from pyfea.interfaces.meshing import gmsh_interface
        
        self.source_file = filename
        
        with gmsh_interface() as geo:
            geo.set_element_size(5,20)
            geo.gen_mesh_from_surf(filename)
            geo.extract_geometry()
            
            #going to have to iterate through parts
            part = Part()
            part.add_geometry(geo.points, geo.elements)
            self.parts.append(part)
        
            
    
if __name__=='__main__':
    
    filenames = [
                 '../../testfiles/scramjet/Air.stl',
                 '../../testfiles/scramjet/Air2.stl',
                 '../../testfiles/scramjet/Body.stl',
                 '../../testfiles/scramjet/Fuel outlet.stl'
                 ]
    
    surfaces = []
    parts = []
    for filename in filenames:
        print('Generating mesh for file: ' + filename)
        
        sm = SurfaceMesh(filename = filename)
        surfaces.append(sm)
        em = Part(surface_mesh=sm)
        parts.append(em)
        em.gen_mesh_from_surf(meshing='gmsh',
                              element_size=(0.5,20))
        
    assembly = Assembly(parts)
    assembly.plot()
    
#essentially here for extra testing
if False:
    filename = '../../testfiles/scramjet/Scramjet study v6.STEP'
    
    from pyfea.interfaces.meshing import gmsh_interface
    geo = gmsh_interface()
    geo.set_element_size(5,20)
    geo.gen_mesh_from_surf(filename)
    geo.extract_geometry()
    
    #going to have to iterate through parts
#    part = Part()
#    part.add_geometry(geo.points, geo.elements)
        