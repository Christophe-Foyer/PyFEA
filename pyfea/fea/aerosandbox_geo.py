from aerosandbox.geometry import Airplane
from pyfea.fea.geometry import EntityMesh
from pyfea.interfaces.gmsh import gmsh_interface
import autograd.numpy as np
from stl import mesh #numpy-stl
from scipy.spatial import Delaunay

class Airplane(Airplane):
    
    entitymesh = None
    wing_entities = []
    plane_mesh = None
    
    def generate_mesh(self, meshtool='gmsh'):
        """
        Creates an STL mesh for use with gmsh/CAD software
        """
        
        self.entitymesh = EntityMesh()
        
        #create a trimesh for each wing
        for wing in self.wings:
            em = self.gen_wing_mesh(wing)
            self.wing_entities.append(em)
            
#        self.plane_mesh = EntityMesh()
#        self.plane_mesh.merge(self.wing_entities)
    
    def gen_wing_mesh(self, wing):
        """
        Converts aerosandbox wing instances to triangular meshes
        This is messy code to make a messy process work
        """

        #check the assumption that all airfoil data has the same number of points
        lists = [x.airfoil.lower_coordinates() for x in wing.xsecs]
        if len(set(map(len, lists))) not in (0, 1):
            raise ValueError('not all airfoils have same datapoint number!')
            
        lists = [x.airfoil.upper_coordinates() for x in wing.xsecs]
        if len(set(map(len, lists))) not in (0, 1):
            raise ValueError('not all airfoils have same datapoint number!')
            
        #convert to 3d points
        def clean_upper_lower(xsec):
            #put all points in one list
            points = np.concatenate((xsec.airfoil.upper_coordinates(),
                                     xsec.airfoil.lower_coordinates()))
            #add x/y offset
            points = points*xsec.chord
            
            #add a column for z axis (this assumes wings are horizontal)
            points3d = np.c_[np.tile(0, points.shape[0]),points]
            
            #add offset
            points3d = points3d+np.array([xsec.xyz_le[1],xsec.xyz_le[0],xsec.xyz_le[2]])
            
            return points3d
        
        #get points lists 
        points = [clean_upper_lower(x) for x in wing.xsecs]
        points_flt = np.vstack(points)
        
        #generate triangles
        
        #connect across and diagonally
        tri0 = []
        for i in range(len(points)-1):
            if i > 0: offset = sum([len(x) for x in points[:i]])
            else: offset = 0
            offset2 = sum([len(x) for x in points[:i+1]])
            for j in range(len(points[i])-1):
                tri0.append([offset+j, offset2+j, offset2+j+1])
                tri0.append([offset+j, offset+j+1, offset2+j+1])
        tri0 = np.array(tri0)
        
        #now close the ends (this is imprefect rn)
        #TODO: fix end meshing
        tri1 = []
        for i in range(1,len(points[-1][:,:2])-1):
            tri1.append([0, i, i+1])
        tri1 = np.array(tri1)
        
        tri2 = []
        for i in range(1,len(points[-1][:,:2])-1):
            tri2.append([0, i, i+1])
        #correct index offset
        tri2 = np.array(tri2) + len(points_flt) - len(points[-1][:,:2])
        
        tri = np.vstack((tri0,tri1,tri2))
        
        #if symetric make symetric
        
        # for testing
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        import matplotlib.pyplot as plt
        
        points_3d = points_flt[tri]
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.add_collection3d(Poly3DCollection(points_3d, linewidths=1))
        
        plt.show()
        
        #generate mesh
        em = self.make_entitymesh(tri, points_flt)
        print('WARNING: entitymesh is currently empty (WIP)')
        
        return em
        
    @staticmethod
    def make_entitymesh(tri, points):
#        data = np.zeros(len(tri), dtype=mesh.Mesh.dtype)
#        
#        your_mesh = mesh.Mesh(data, remove_empty_areas=False)
        
        my_mesh = mesh.Mesh(np.zeros(tri.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(tri):
            for j in range(3):
                my_mesh.vectors[i][j] = points[f[j],:]
        
        #create temp STL
        #TODO: use special tempfile tool
        tempfile = r'airplane_wings.temp.stl'
        my_mesh.save(tempfile)
        
#        #use gmsh to run STL tet meshing
#        geo = gmsh_interface()
#        #set element size
#        geo.set_options(1,1.5)
#        
#        #read temp file
#        try:
#            geo.gen_mesh_stl(tempfile)
#        except ValueError:
#            raise ValueError('Merge failed, is the geometry defined? Please check input file.')
#        geo.extract_geometry()
        
        #generate entitymesh
        em = EntityMesh()
#        em.add_geometry(geo.points, geo.elements)
        #TODO: add surface mesh
        return em
    
if __name__=='__main__':
    
    from aerosandbox import WingXSec, Wing, Airfoil
    
    glider = Airplane(
        name="Conventional",
        xyz_ref=[0, 0, 0], # CG location
        wings=[
            Wing(
                name="Main Wing",
                xyz_le=[0, 0, 0], # Coordinates of the wing's leading edge
                symmetric=True,
                xsecs=[ # The wing's cross ("X") sections
                    WingXSec(  # Root
                        xyz_le=[0, 0, 0], # Coordinates of the XSec's leading edge, relative to the wing's leading edge.
                        chord=0.18,
                        twist=2, # degrees
                        airfoil=Airfoil(name="naca4412"),
                        control_surface_type='symmetric',  # Flap # Control surfaces are applied between a given XSec and the next one.
                        control_surface_deflection=0, # degrees
                        control_surface_hinge_point=0.75 # as chord fraction
                    ),
                    WingXSec(  # Mid
                        xyz_le=[0.01, 0.5, 0],
                        chord=0.16,
                        twist=0,
                        airfoil=Airfoil(name="naca4412"),
                        control_surface_type='asymmetric',  # Aileron
                        control_surface_deflection=0,
                        control_surface_hinge_point=0.75
                    ),
                    WingXSec(  # Tip
                        xyz_le=[0.08, 1, 0.1],
                        chord=0.08,
                        twist=-2,
                        airfoil=Airfoil(name="naca4412"),
                    )
                ]
            ),
            Wing(
                name="Horizontal Stabilizer",
                xyz_le=[0.6, 0, 0.1],
                symmetric=True,
                xsecs=[
                    WingXSec(  # root
                        xyz_le=[0, 0, 0],
                        chord=0.1,
                        twist=-10,
                        airfoil=Airfoil(name="naca0012"),
                        control_surface_type='symmetric',  # Elevator
                        control_surface_deflection=0,
                        control_surface_hinge_point=0.75
                    ),
                    WingXSec(  # tip
                        xyz_le=[0.02, 0.17, 0],
                        chord=0.08,
                        twist=-10,
                        airfoil=Airfoil(name="naca0012")
                    )
                ]
            ),
            Wing(
                name="Vertical Stabilizer",
                xyz_le=[0.6, 0, 0.15],
                symmetric=False,
                xsecs=[
                    WingXSec(
                        xyz_le=[0, 0, 0],
                        chord=0.1,
                        twist=0,
                        airfoil=Airfoil(name="naca0012"),
                        control_surface_type='symmetric',  # Rudder
                        control_surface_deflection=0,
                        control_surface_hinge_point=0.75
                    ),
                    WingXSec(
                        xyz_le=[0.04, 0, 0.15],
                        chord=0.06,
                        twist=0,
                        airfoil=Airfoil(name="naca0012")
                    )
                ]
            )
        ]
    )
    
    glider.gen_wing_mesh(glider.wings[0])