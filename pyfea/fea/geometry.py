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
        """
        Initializes tetrahedron properties.
        """
        
        assert len(points) == 4, "Point array must be of length 4"
        assert max(points) < len(pointcloud), "Points must be within pointcloud length"
        
#        if array_num:
#            self.array_num = array_num
#        elif entity_mesh:
#            entity_mesh.tets.tolist().index(points.tolist())
        
        self.points = np.array(points)
        self.pointcloud = np.array(pointcloud)[points]
        self.entity_mesh = entity_mesh
        self.array_num = array_num
        
    def get_coords(self):
        """
        Returns the 3d coordinates of the vertices of the tetrahedron.
        """
        
        assert self.points
        assert self.pointcloud
        return np.array(self.pointcloud)[self.points]
        
    def get_cog(self):
        """
        Returns the averages of the vertices.
        """
        return np.mean(self.get_coords())
    
    def get_neighbors(self, tets=None):
        """
        Finds neighboring tetrahedrons given access to a list of potential
        neighbors.
        """
        
        #TODO: Implement axis aligned bounding boxes to speed up!!!
        
        #make sure the tet has access to the list of possible neighbors
        assert tets is not None or \
               (isinstance(self.entity_mesh, EntityMesh)
                and self.entity_mesh.tets is not None), \
               'Tetrahedron needs access to tets list (via argument or Tetrahedron.entity_mesh)'
               
        #vectorized neighbor finder
        arr = np.concatenate((np.tile(self.points, (len(tets), 1)), tets), axis=1)
        check = np.apply_along_axis(lambda x: len(set(x)) == 5, 1, arr)
        self.neighbors = np.nonzero(check)
        
        return self.neighbors
    
#    def refine_mesh(self, point=None, function=(lambda x: np.sqrt(x))):
#        """
#        Splits the tetrahedron x-times with a specified function for spacing
#        around the specified point.
#        """
#    
#        return
#    
#    def plot(self, plotter=None, **kwargs):
#        grid = pv.PolyData()
#        
#        import vtk
#        import vtk.util.numpy_support as vtk_np
#        
#        verts = vtk.vtkPoints()
#        verts.SetData(vtk_np.numpy_to_vtk(self.points))
#        cells = vtk.vtkCellArray()
##        cell_np = np.array([0,1,2,3], dtype=np.int64)
#        cell_np = np.vstack([np.ones(1,dtype=np.int64), np.arange(1,dtype=np.int64)]).T.flatten()
#        cells.SetCells(1, vtk_np.numpy_to_vtkIdTypeArray(cell_np))
#        
#        grid.SetPoints(verts)
#        grid.SetVerts(cells)
#        
#        self.grid = grid
#        
##        points = self.entity_mesh.nodes[self.points]
#        
#        if plotter==None:
#            plotter = pv.BackgroundPlotter()
#        
##        data = pv.read(grid)
#        
##        plotter = pv.Plotter()  # instantiate the plotter
##        plotter.add_points(points)
#        plotter.add_mesh(grid, **kwargs)    # add a dataset to the scene
#        plotter.show()     # show the rendering window
#        
#        return plotter
    
class EntityMesh:
    """
    Class defining the 3d geometry of an object.
    This includes surface meshes, and 3d tet meshes.
    """
    
    nodes = None
    tets = None
    elements = []
    adjacent = []
    surface_mesh = None
    
    def __init__(self, surface_mesh=None):
        """
        Initializes the object with a surfacemesh if specified.
        """
        assert isinstance(surface_mesh, SurfaceMesh) or surface_mesh == None, \
            Exception('surface_mesh is of type: ' + str(type(surface_mesh)))
        if surface_mesh:
            self.surface_mesh = surface_mesh
        
    def gen_elements(self, find_adjacent=False, force_regen=False):
        """
        Generates Tetrahedron instances.
        """
        
        if force_regen == False and self.elements != []: return
        
        self.elements = []
        for row in self.tets:
            tet = Tetrahedron(row, self.nodes, self)
            self.elements.append(tet)
            
        if find_adjacent: self.get_adjacent()
            
    def add_geometry(self, nodes, tets, autogen=True):
        """
        Adds the specified geometry to the 3D mesh (to be used with meshing
        interfaces).
        """
        
        assert np.array(nodes).shape[1] == 3, "nodes must be a numpy array with dims (*,3)"
        assert np.array(tets).shape[1] == 4, "tets must be a numpy array with dims (*,4)"
        self.nodes = nodes
        self.tets = tets
        
        if autogen:
            self.gen_elements()
            
    def get_cog(self):
        """
        Returns COG.
        """
        return np.mean(self.nodes[self.nodes])
            
    def set_surface_mesh(self, surface_mesh, autogen=True):
        """
        Defines a surface mesh.
        """
        
        assert isinstance(surface_mesh, SurfaceMesh)
        self.surface_mesh = surface_mesh
        
        if autogen:
            self.gen_mesh_from_surf()
            
    def _get_adjacent_legacy(self): #WIP
        """
        Legacy version of the adjecent finder 
        (no tensorflow, python for loop, very slow).
        """
        
        print('WARNING: this function is currently O(n^2) run mostly in '
              + 'python. This may take a while...')
        
        assert self.elements, 'please generate elements first eg. "mesh.gen_elements()"'
        
        from pyfea.tools.console_output import printProgressBar as ppb
        
        #TODO: vectorize more (toplevel loop here)
        adjacent = []
        
        ppb(0, len(self.elements),
            prefix = 'Progress:', suffix = '',
            length = 25)
        
        #TODO: This is extremely slow, please vectorize this
        for i, tet in enumerate(self.elements):
            adjacent.append(tet.get_neighbors(self.tets)[0])
            ppb(i+1, len(self.elements),
                prefix = 'Progress:', suffix = '',
                length = 25, decimals = 4)
        self.adjacent = adjacent
        
    def get_adjacent(self):
        """
        WIP: Seems to work, but buggy, much faster though.
        """
        
        from pyfea.dev.tf import adjacentfinder
        
        adj = adjacentfinder(self.tets, self.nodes)
        
        self.adjacent = np.array(adj)
        
        return self.adjacent
            
    vtk_filename = None
    def export_vtk(self, _filename):
        """
        Exports 3D mesh to vtk
        """
        
        meshio.write_points_cells(_filename, self.nodes, {'tetra': self.tets})
        self.vtk_filename = _filename
        return _filename
        
    #TODO: Fix this
    def merge(self, entities, include_self=True, autogen=True):
        """
        Blindly merges 3d meshes. Intersections are left as-is.
        """
        
        if isinstance(entities, EntityMesh): entities = [entities]
        
        assert type(entities)==list
        assert all([isinstance(x, EntityMesh) for x in entities])
        
        #add itself to the list
        if include_self: 
            entities + [self]
        
        #TODO: should remesh with gmsh instead of just appending
        for entity in entities:
            if len(self.tets) > 0:
                self.tets = np.vstack([self.tets, entity.tets+len(self.nodes)])
            else:
                self.tets = entity.tets
            if len(self.adjacent) > 0:
                self.adjacent = np.vstack([self.adjacent, entity.adjacent+len(self.tets)])
            else:
                self.adjacent=entity.adjacent
            if len(self.nodes) > 0:
                self.nodes = np.vstack([self.nodes, entity.nodes])
            else:
                self.nodes = entity.nodes
            
#        self.nodes = np.vstack([x.nodes for x in entities])
#        self.tets = np.vstack([x.tets for x in entities])
        
        if autogen:
            self.gen_elements()
            
    def gen_surface_mesh(self):
        """
        TODO
        """
        print('WIP')
    
    def gen_mesh_from_surf(self,
                           tempfile=None,
                           surface_mesh=None,
                           autogen=True,
                           meshing='auto',
                           element_size = (0.0,10.0**22)):
        """
        Creates an 3d mesh from a surface mesh or stl file.
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
        if not tempfile: 
            import tempfile
            tempfile = tempfile.TemporaryFile(suffix='.stl').name
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
                    
                    self.add_geometry(geo.points, geo.elements)
                    
                    if autogen == True:
                        self.gen_elements()
                        
                    break
            except Exception as e:
                print(e)
                print(Exception('Error with meshing engine: ' + engine.__name__))
        
    #pyvista
    def plot(self, filename=None, plotter=None, 
             style='wireframe', **kwargs):
        """
        Plots a vtk tempfile using pyvista (kwargs are passed to the plotter).
        """
        
        #TODO: fix need for VTK file
        
        if plotter==None:
            plotter = pv.BackgroundPlotter()
        
        if not filename and self.vtk_filename: 
            filename = self.vtk_filename
        else:
            filename = tempfile.TemporaryFile(suffix='.vtk').name
            print(filename)
            self.export_vtk(filename)
        
        data = pv.read(filename)
        
#        plotter = pv.Plotter()  # instantiate the plotter
        plotter.add_mesh(data, style=style, **kwargs)    # add a dataset to the scene
        plotter.show()     # show the rendering window
        
        return plotter
        
    #Matplotlib
    def show_nodes(self):
        """
        Matplotlib scatter3d plot.
        """
        scatter3d(self.nodes)
            
class SurfaceMesh:
    """
    Surface mesh of an object.
    """
    
    points=None
    tri=None
#    normals = None
    
    def __init__(self, points=None, tri=None, filename=None):
        if ((type(points) == np.ndarray or
             type(points) == list) and
            (type(tri) == np.ndarray or
             type(tri) == list)):
            """
            Initializes the surfacemesh from surface data or a file.
            """
        
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
        """
        Plots the surfacemesh using matplotlib.
        """
        
        # for testing could 100% be done with pyvista
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
        """
        Generates an stl file from instance data.
        """
        
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
        """
        Reads an stl to import into instance data.
        """
        
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
        """
        Initializes part properties.
        """
        
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
    
    def __init__(self, parts, auto_unify_mesh = True, **kwargs):
        """
        Initializes Assembly properties.
        """
        
        assert 'surface_mesh' not in kwargs.keys(), \
            'incorrect argument: surface_mesh'
        
        #pass the arguments
        super(Assembly, self).__init__(**kwargs)
        
        self.parts = parts
        
        if auto_unify_mesh:
            self.generate_mesh()
        
#    def gen_elements(self):
#        for part in parts:
#            self.points
        
    def __getattribute__(self, name):
        """
        Wrapper to disable certain methods from base class.
        """
        
        disabled_methods = ['set_surface_mesh']
        
        if name in [disabled_methods]:
            raise AttributeError('Method: "' + name +
                                 '" is disabled for Assembly instances.')
        ret = super(Assembly, self).__getattribute__(name)
        return ret 
        
    #TODO: find a way to merge faces between objects?
    def merge_faces(self):
        """
        TODO: merge faces of adjacent parts (HARD)
        """
        pass
    
    def generate_mesh(self):
        """
        Naively merges meshes of parts.
        """
        
        self.nodes = np.array([])
        self.tets = np.array([])
        self.elements = []
        self.adjacent = []
        
        self.merge(entities=self.parts)
    
    #This needs to be replaced
    def get_cog(self):
        """
        WIP
        """
        print('WIP')
        
    #this will need updating
    def plot(self, **kwargs):
        """
        Plots parts to pyvista.
        """
        
#        if 'normals' in kwargs.keys():
#            normals = kwargs.pop('normals')
#        else: normals = False
        if 'style' in kwargs.keys():
            style = kwargs.pop('style')
        else: style = 'wireframe'
        if 'plotter' in kwargs.keys():
            plotter = kwargs.pop('plotter')
        else: plotter = None
        
        if plotter==None:
            plotter = pv.BackgroundPlotter()
        
        for part in self.parts:
            tmp = tempfile.TemporaryFile(suffix='.vtk').name
            part.export_vtk(tmp)
            
            data = pv.read(tmp)            
            plotter.add_mesh(data, style=style, **kwargs)
            
        plotter.show()
        
        return plotter
        
    def gen_from_source(self, filename, element_size = None):
        """
        Generates geometry from a source file? I think this was an assembly test.
        """
        
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
        em.gen_mesh_from_surf(meshing='tetgen', element_size=(0.5,20))
    
    parts[0].merge(parts.pop(1))
#    for part in parts: part.gen_elements()
    assembly = Assembly(parts)
    assembly.plot(style=None)
    
#essentially here for extra testing
if False:
    filename = '../../examples/testfiles/scramjet/Scramjet study v6.STEP'
#    filename = '../../examples/testfiles/scramjet/Scramjet study v7.stl'
    
    from pyfea.interfaces.meshing import gmsh_interface
    geo = gmsh_interface()
    geo.set_element_size(5,20)
    geo.gen_mesh_from_cad(filename)
    geo.extract_geometry()
    
    #going to have to iterate through parts
#    part = Part()
#    part.add_geometry(geo.points, geo.elements)
        