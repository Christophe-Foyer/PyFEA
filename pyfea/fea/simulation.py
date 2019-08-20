# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 18:35:18 2019

@author: Christophe
"""

import threading
from queue import Queue

import inspect
import types
import copy

class Simulation():
    
    assembly = None
    boundary_conditions = {}
    parameters = {}
    physics_effects = []
    
    def __init__(self, assembly, physics_effects = []):
        self.assembly = assembly
        self.physics_effects = self.physics_effects + physics_effects
        
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
        
        t = threading.Thread(target=self._run_sim, 
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
        
        boundary_conditions = {}
        assembly = None
        sequence = []
        last_run = []
        physics_effects = []
        
        def __init__(self, q_in, q_out, **kwargs):
            
            self.q_in = q_in
            self.q_out = q_out
            
            for arg in kwargs:
                setattr(self, arg, kwargs[arg])
                
            for effect in self.physics_effects:
                self.sequence = self.sequence + [effect.timestep]
                self.last_run = self.last_run + [0]
        
        def calculate(self, dt='auto'):
            """
            Calculates the physical parameter with lowest timestep.
            """
            
            minstep = min(self.sequence)
            index = self.sequence.index(minstep)
            nextcalc = self.physics_effects[index]
            
            nextcalc.calculate()
            
            #weave some c in here?
            #https://docs.scipy.org/doc/scipy-0.15.1/reference/generated/scipy.weave.inline.html
        
    
    @staticmethod
    def _run_sim(q_in, q_out, attributes):
        running = True
        
        #Create instance
        SimSpace = Simulation.SimSpace(q_in, q_out, attributes)
        
        if not q_in.empty():
            cmd = q_in.get()
            q_out.put(cmd.eval)
        
        while running:
            #TODO: I don't like this being the main loop
            SimSpace.calculate()   
            
class Physics_Effect_Base:
    """
    A class to set interfaces between the simulation and
    extensions for multiphysics calculations.
    """
    
    simulation = None
    
    def __init__(self, simulation, **kwargs):
        self.simulation = simulation
    
class Thermal_Conduction(Physics_Effect_Base):
    """
    A class to define conduction calculatiions
    """
    
    timestep = None
    
    def __init__(self, **kwargs):
        super(Thermal_Conduction, self).__init__(**kwargs)
        
        self.parts = kwargs['thermal_sim_parts']
            
    def timestep(self):
        #TODO: Placeholder function
        self.timestep = 0.5 #s
        
    def calculate(self, dt):
        pass
        
    
    
if __name__ == '__main__':
    
    from pyfea.fea.geometry import SurfaceMesh, Part, Assembly

#    filename = '../../examples/testfiles/scramjet/Body.stl'
    filename = '../../examples/testfiles/cube.stl'

    sm = SurfaceMesh(filename = filename)
    em = Part(surface_mesh=sm)
    
    em.gen_mesh_from_surf(meshing='gmsh', element_size=(1000.0,10.0**22))
    em.get_adjacent()

    assembly = Assembly([em])
    
    sim = Simulation(assembly)
    sim.set_boundary_conditions()