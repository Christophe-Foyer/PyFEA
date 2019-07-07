from aerosandbox.geometry import Airplane
from pyfea.geometry import EntityMesh

class Airplane(Airplane):
    
    entitymesh = None
    
    def generate_stl_mesh(self, meshtool='gmsh'):
        """
        Creates an STL mesh for use with gmsh/CAD software
        """
        
        self.entitymesh = EntityMesh()
        
        for wing in self.wings:
            #convert to trimesh
            pass