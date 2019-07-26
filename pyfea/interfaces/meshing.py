from pyfea.fea.geometry import EntityMesh, SurfaceMesh

import math
import numpy as np
import pyvista as pv

#import logging
#logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')
        
class gmsh_interface:
    
    points=None
    elements=None
    
    def __init__(self, name='test'):
        import onelab.lib.gmsh as gmsh
        self.gmsh = gmsh
        
        gmsh.initialize()
        
        gmsh.model.add(name)
        
        gmsh.option.setNumber("General.Terminal", 1)
    
    def __enter__(self):
        return self
        
    def gen_mesh(self, filename):
        gmsh = self.gmsh
        
        #TODO: add options to control how the mesh is generated
        gmsh.merge(filename)
#        gmsh.model.geo.addVolume([-1])
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)
        
#    def refine(self):
#        """
#        TODO: Seems to throw memory access violation errors
#        """
#        pass
#        gmsh.model.mesh.refine()
        
    def set_element_size(self, minlength=0.75, maxlength=0.75):
        gmsh = self.gmsh
        
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", minlength);
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", maxlength);
        
    def gen_mesh_from_surf(self, input_geo):
        gmsh = self.gmsh
        
        if isinstance(input_geo, SurfaceMesh): input_geo = input_geo.gen_stl()
        
        gmsh.option.setNumber("Mesh.Algorithm", 6);
        gmsh.merge(input_geo)
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
        gmsh = self.gmsh
        
        gmsh.fltk.run()
        
    def extract_geometry(self):
        gmsh = self.gmsh
        
        #point cloud
        _, points, _ = gmsh.model.mesh.getNodes()
        self.points = points.reshape(( int(len(points)/3),3))
        
        elements = gmsh.model.mesh.getElements()
        elements = elements[2][list(elements[0]).index(4)]
        self.elements = elements.reshape(int(len(elements)/4),4)-1
        
        return self.points, self.elements
        
    def output_mesh(self, filename='output.msh'):
        gmsh = self.gmsh
        
        gmsh.write(filename)
        
    def __exit__(self, *args):
        gmsh = self.gmsh
        
        gmsh.finalize()
        
class tetgen_interface():

    def set_element_size(self, minlength=0.75, maxlength=0.75):
        print('Currently not supported, WIP')
        
    def gen_mesh_from_surf(self, raw_input = None,
                           filename=None, 
                           tri=None, points=None, 
                           surface_mesh=None):
        
        from stl import mesh
        import tetgen
        
        #put rawinput in correct place
        if type(raw_input) == str:
            filename = raw_input
        elif isinstance(raw_input, SurfaceMesh):
            surface_mesh=raw_input
        
        assert (filename or (tri and points) or surface_mesh), 'No input geometry specified'
        
        if filename:
            mesh = mesh.Mesh.from_file(filename)
            points = np.unique(mesh.points.reshape(mesh.points.shape[0]*3, 3), axis=0)
            tri = [[points.tolist().index(x[0:3].tolist()),
                    points.tolist().index(x[3:6].tolist()),
                    points.tolist().index(x[6:9].tolist())]
                   for x in mesh.points] 
    
        elif surface_mesh:
            points = surface_mesh.points
            tri = surface_mesh.tri
            
        points = np.array(points)
        tri = np.array(tri)
        
#        assert points!=None and tri!=None, 'Empty geometry, check input is specified correctly'

        mesh = pv.PolyData(points, np.c_[np.tile(3, tri.shape[0]),tri].flatten())
        
        tet = tetgen.TetGen(mesh)
        tet.make_manifold()
        tet.tetrahedralize()
        
        grid = tet.grid
        
        # plot half
        mask = np.logical_or(grid.points[:, 0] < 0, grid.points[:, 0] > 4)
        half = grid.extract_selection_points(mask)
        
        ###############################################################################
        
        plotter = pv.Plotter()
        plotter.add_mesh(half, color='w', show_edges=True)
        plotter.add_mesh(grid, color='r', style='wireframe', opacity=0.2)
#        plotter.camera_position = cpos
        plotter.show()
        
        return grid

if __name__ == '__main__':

#    filename = 'testfiles/airplane_wings.stl'
    filename = 'testfiles/ExampleWingGeom.stl'
#    filename = 'testfiles/scramjet/Air.stl' 
       
    #much of this should be integrated eventually
#    print("GMSH_API_VERSION: v{}".format(gmsh.GMSH_API_VERSION))
   
#    with gmsh_interface() as geo:
    geo = gmsh_interface()
    geo.set_element_size(0.25,0.75)
    geo.gen_mesh_from_surf(filename)
    geo.extract_geometry()
    
    #generate python object
    em = EntityMesh()
    em.add_geometry(geo.points, geo.elements)
    em.export_vtk('out.vtk')
    
    em.plot_vtk()
    
    geo.__exit__()
    
#    sm = SurfaceMesh(filename = filename)
#    
#    geo = tetgen_interface()
#    grid = geo.gen_mesh_from_surf(sm.gen_stl())