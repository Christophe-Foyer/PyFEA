from pyfea.fea.geometry import EntityMesh, SurfaceMesh

import math
import numpy as np
import pyvista as pv

#import logging
#logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO, datefmt='%I:%M:%S')
     
class interface_base:
    
    points=None
    elements=None
    filetypes=[]
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def check_compatibility(self, filename):
        assert filename.rsplit('.', 1)[1] in self.filetypes, \
            'filetype ' + filename.rsplit('.', 1)[1] + ' not supported for ' \
            'mesh engine: ' + self.__name__
        pass
   
class gmsh_interface(interface_base):
    
    filetypes=['stl']
    
    def __init__(self, name='test'):
        import onelab.lib.gmsh as gmsh
        self.gmsh = gmsh
        
        gmsh.initialize()
        
        gmsh.model.add(name)
        
        gmsh.option.setNumber("General.Terminal", 1)
        
    def gen_mesh_from_cad(self, filename):
        
        self.check_compatibility(filename)
        
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
        
        return self.extract_geometry()

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
        
class tetgen_interface(interface_base):
    
    filetypes=['stl']
    
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
            self.check_compatibility(filename)
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
#        mask = np.logical_or(grid.points[:, 0] < 0, grid.points[:, 0] > 4)
#        half = grid.extract_selection_points(mask)
#        
#        ###############################################################################
#        
#        plotter = pv.BackgroundPlotter()
#        plotter.add_mesh(half, color='w', show_edges=True)
#        plotter.add_mesh(grid, color='r', style='wireframe', opacity=0.2)
##        plotter.camera_position = cpos
#        plotter.show()
        
        self.points = grid.points
        self.elements = grid.cells.reshape(-1,11)[:,1:5]
#        return grid
        return self.points, self.elements

if __name__ == '__main__':

#    filename = 'examples/testfiles/airplane_wings.stl'
    filename = 'examples/testfiles/ExampleWingGeom.stl'
#    filename = 'examples/testfiles/scramjet/Air.stl' 
#    filename = 'examples/testfiles/scramjet/Scramjet study v7.stl'
    
    meshing = 'gmsh'
       
    #much of this should be integrated eventually
#    print("GMSH_API_VERSION: v{}".format(gmsh.GMSH_API_VERSION))
    
#    with gmsh_interface() as geo:
    if meshing == 'gmsh':
        geo = gmsh_interface()
        geo.set_element_size(0.25,0.75)
        geo.gen_mesh_from_surf(filename)
        geo.extract_geometry()
        
        #generate python object
        em = EntityMesh()
        em.add_geometry(geo.points, geo.elements)
#        em.export_vtk('out.vtk')
        
        em.plot()
        
        geo.__exit__()
        
    elif meshing == 'tetgen':
    
        sm = SurfaceMesh(filename = filename)
        
        geo = tetgen_interface()
        grid = geo.gen_mesh_from_surf(sm.gen_stl())
        
        em = EntityMesh()
        em.add_geometry(geo.points, geo.elements)
#        em.export_vtk('out.vtk')
        
        em.plot()
        
#class netgen_interface(interface_base):
#    
#    filetypes=['stp','step']
#    
#    def gen_mesh_from_cad(self, filename):
#        
#        self.check_compatibility(filename)
#        
#        from netgen.NgOCC import LoadOCCGeometry
#
#        geo = LoadOCCGeometry(filename)
#        mesh = geo.GenerateMesh()
##        mesh.Save('screw.vol')
##        
##        from ngsolve import *
##        Draw(Mesh(mesh))
#        
#        self.points = np.array(mesh.Points())
#        self.elements = []
#        
#        return self.points, self.elements 
#        
#    def cube_sphere(self):
#        from netgen.meshing import *
#        from netgen.csg import *
#        
#        from ngsolve import ngsglobals
#        ngsglobals.msg_level = 2
#        # generate brick and mesh it
#        geo1 = CSGeometry()
#        geo1.Add (OrthoBrick( Pnt(0,0,0), Pnt(1,1,1) ))
#        m1 = geo1.GenerateMesh (maxh=0.1)
#        m1.Refine()
#        
#        # generate sphere and mesh it
#        geo2 = CSGeometry()
#        geo2.Add (Sphere (Pnt(0.5,0.5,0.5), 0.1))
#        m2 = geo2.GenerateMesh (maxh=0.05)
#        m2.Refine()
#        m2.Refine()
#        
#        print ("***************************")
#        print ("** merging suface meshes **")
#        print ("***************************")
#        
#        # create an empty mesh
#        mesh = Mesh()
#        
#        # a face-descriptor stores properties associated with a set of surface elements
#        # bc .. boundary condition marker,
#        # domin/domout .. domain-number in front/back of surface elements (0 = void),
#        # surfnr .. number of the surface described by the face-descriptor
#        
#        fd_outside = mesh.Add (FaceDescriptor(bc=1,domin=1,surfnr=1))
#        fd_inside = mesh.Add (FaceDescriptor(bc=2,domin=2,domout=1,surfnr=2))
#        # copy all boundary points from first mesh to new mesh.
#        # pmap1 maps point-numbers from old to new mesh
#        
#        pmap1 = { }
#        for e in m1.Elements2D():
#            for v in e.vertices:
#                if (v not in pmap1):
#                    pmap1[v] = mesh.Add (m1[v])
#        
#        
#        # copy surface elements from first mesh to new mesh
#        # we have to map point-numbers:
#        
#        for e in m1.Elements2D():
#            mesh.Add (Element2D (fd_outside, [pmap1[v] for v in e.vertices]))
#        
#        
#        
#        # same for the second mesh:
#        
#        pmap2 = { }
#        for e in m2.Elements2D():
#            for v in e.vertices:
#                if (v not in pmap2):
#                    pmap2[v] = mesh.Add (m2[v])
#        
#        for e in m2.Elements2D():
#            mesh.Add (Element2D (fd_inside, [pmap2[v] for v in e.vertices]))
#        
#        
#        print ("******************")
#        print ("** merging done **")
#        print ("******************")
#        
#        
#        mesh.GenerateVolumeMesh()
#        mesh.Save ("newmesh.vol")