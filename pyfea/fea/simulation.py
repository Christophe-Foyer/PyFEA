# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 18:35:18 2019

@author: Christophe
"""

import threading
from queue import Queue

import inspect
import types

class Simulation():
    
    assembly = None
    boundary_conditions = {}
    
    def __init__(self, assembly):
        self.assembly = assembly
        
    def set_boundary_conditions(self, **kwargs):
        for name, value in kwargs.items():
            self.boundary_conditions[name]=value
            
    def run_simulation(self, dt=None, t=None):
        
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        attributes = {a[0]:a[1] for a in attributes 
                      if not(a[0].startswith('__') 
                      and a[0].endswith('__'))
                      and not isinstance(a[1], (type, types.ClassType))}
        
        in_q = Queue.Queue()
        out_q = Queue.Queue()
        
        t = threading.Thread(target=None, 
                             args = (in_q, out_q, attributes))
        t.daemon = True
        t.start()
        
        self.sim_thread = t
        self.sim_output = out_q
        self.sim_input = in_q
        
        return {'thread':t, 'input_queue':in_q, 'output_queue':out_q}
    
    def plot(self, sim_property, parts=None):
        self.sim_input.put('SimSpace.'+sim_property)
        output = self.sim_output.get()
        
        return output
    
    class SimSpace():
        """
        This should probably be a wrapper for a c++ module.
        """
        
        def __init__(self):
            pass
        
        def calculate(self, dt='auto'):
            pass
    
    @staticmethod
    def _run_sim(q_in, q_out):
        running = True
        
        #Create instance
        SimSpace = Simulation.SimSpace()
        
        if not q_in.empty():
            cmd = q_in.get()
            q_out.put(cmd.eval)
        
        while running:
            SimSpace.calculate()   
            
class Physics_Effect_Base:
    """
    A class to set interfaces between the simulation and
    extensions for multiphysics calculations.
    """
    
    def __init__(self):
        pass
    
class Thermal_Conduction(Physics_Effect_Base):
    """
    A class to define conduction calculatiions
    """
    
    def __init__(self):
        pass
            
if __name__ == '__main__':
    from pyfea.fea.geometry import SurfaceMesh, Part, Assembly

    filename = '../testfiles/scramjet/Body.stl'
    
    sm = SurfaceMesh(filename = filename)
    em = Part(surface_mesh=sm)
    em.gen_mesh_from_surf(meshing='gmsh', element_size=(10,25))

    assembly = Assembly([em])
    
    sim = Simulation(assembly)
    sim.set_boundary_conditions()