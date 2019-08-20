# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 10:39:18 2019

@author: Christophe
"""

class Material:
    """
    Class defining material properties.
    """
    
    #Info
    mat_type = None #fluid/solid
    material = None #material
    
    #Visual
    appearance=None
    
    #General properties
    density = None
    C_p = None #will need lookup
    temperature = None
    
    #Solid properties
    E = None
    stress_strain = None #will create stress/strain db later
    sigma_y = None
    poisson = None
    
    #Fluid properties
    viscocity = None
    static_pressure = None
    
    def __init__(self, material, mat_type='solid', **kwargs):
        """
        Initialize material type and additional material properties throuh kwargs.
        """
        
        assert mat_type in ['solid', 'fluid'], 'material type (mat_type) must be "fluid" or "solid"'
        
        self.mat_type = mat_type
        
        #look for material data in db
        self.material = material
        
        for name, value in kwargs.items():
            setattr(self, name, value)