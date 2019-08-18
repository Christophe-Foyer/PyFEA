import importlib
if importlib.util.find_spec("aerosandbox") is None:
    raise ImportError('This module depends on AeroSandbox. Please install using "pip install AeroSandbox" or from the git repository: https://github.com/peterdsharpe/AeroSandbox')

from aerosandbox.geometry import Airplane
from pyfea.fea.geometry import EntityMesh, SurfaceMesh
import autograd.numpy as np
#from stl import mesh #numpy-stl
#from scipy.spatial import Delaunay

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
        
        #TODO: rotate xsecs to line up with progression (esp important for vstab)
        
        points_flt = np.vstack(points)
        
        #generate triangles
        
        #connect across and diagonally
        tri0 = []
        for i in range(len(points)-1):
            if i > 0: offset = sum([len(x) for x in points[:i]])
            else: offset = 0
            offset2 = sum([len(x) for x in points[:i+1]])
            l = len(points[i])
            for j in range(l-1):
                tri0.append([offset+j, offset2+j+1, offset2+j])
                tri0.append([offset+j, offset+j+1, offset2+j+1])
            tri0.append([offset, offset2+l-1, offset2+l-1]) #Offset, offset+l-1, offset2+l-1
            tri0.append([offset, offset2, offset+l-1]) #Offset, offset2, offset2+l-1
        tri0 = np.array(tri0)
        
        #now close the ends (this is imprefect rn, but better)
        #TODO: fix end meshing
        if not wing.symmetric:
            tri1 = []
            for i in range(len(points[0][:,:2])):
                if i==len(points[0])/2: continue
                if i ==len(points[0])/2-1: continue
                p2 = i+1
                if p2 == len(points[0]): 
                    p2 = 0
                else:
                    tri1.append([int(len(points[0])/2), p2, i])
            tri1 = np.array(tri1)
        
        tri2 = []
        for i in range(len(points[-1][:,:2])):
            if i==len(points[-1])/2: continue
            if i ==len(points[-1])/2-1: continue
            p2 = i+1
            if p2 == len(points[-1]): 
                p2 = 0
            tri2.append([int(len(points[-1])/2), p2, i])
        
#        import matplotlib.pyplot as plt
#        plt.triplot(points[-1][:,0], points[-1][:,1], tri2)
#        plt.plot(points[-1][:,0], points[-1][:,1], 'o')
#        plt.show()
            
        #correct index offset
        tri2 = np.array(tri2) + len(points_flt) - len(points[-1][:,:2])
        
        if not wing.symmetric:
            tri = np.vstack((tri0,tri1,tri2))
        else:
            tri = np.vstack((tri0,tri2))
        
#        del points
        
        #if symetric make symetric
        if wing.symmetric:
            tri = np.vstack((tri,tri+len(points_flt)))
            points_flt = np.vstack((points_flt, points_flt*np.array([-1,1,1])))
        
        #generate mesh
        em = EntityMesh()
        sm = SurfaceMesh(points = points_flt, tri = tri)
        em.set_surface_mesh(sm, autogen=False)
        
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
    
    print('''WIP, gmsh doeesn't like my STLs :(''')
    glider.generate_mesh()
    
    #output main wing
    sm = glider.wing_entities[0].surface_mesh
    sm.gen_stl('wing_mesh.tmp.stl')
    
#    sm.plot()
    
    em = EntityMesh(surface_mesh=sm)
    em.gen_mesh_from_surf(meshing='gmsh')