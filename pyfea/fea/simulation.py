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

import pandas as pd
import numpy as np

class Simulation():
    """
    Simulation class to run transient FEA of an assembly according to specified
    physics modules.
    """
    
    assembly = None
    boundary_conditions = {}
    parameters = {}
    physics_effects = []
    
    def __init__(self, assembly, physics_effects = []):
        self.assembly = assembly
        self.physics_effects = self.physics_effects + physics_effects
        
        #To initialize the dataframe
        # TODO: Error handling
        self.variables = pd.DataFrame({'tets':[i for i in range(len(self.assembly.tets))]})
        self.variables.set_index('tets', inplace=True)
        
        for effect in self.physics_effects:
            effect.define_variables(self)
        
    def set_boundary_conditions(self, **kwargs):
        for name, value in kwargs.items():
            self.boundary_conditions[name]=value
            
    def run(self, dt=None, t=None):
        
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        attributes = {a[0]:a[1] for a in attributes 
                      if not(a[0].startswith('__') 
                      and a[0].endswith('__'))
                      and not inspect.isclass(a[1])}
        
        in_q = Queue()
        out_q = Queue()
        
        t = threading.Thread(target=self._run_sim, 
                             args = (in_q, out_q, attributes))
        t.daemon = True
        t.start()
        
        self.sim_thread = t
        self.sim_output = out_q
        self.sim_input = in_q
        
        return {'thread':t, 'input_queue':in_q, 'output_queue':out_q}
    
    def run_single_thread(self, dt=None, t=None):
        
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        attributes = {a[0]:a[1] for a in attributes 
                      if not(a[0].startswith('__') 
                      and a[0].endswith('__'))
                      and not inspect.isclass(a[1])}
        
        in_q = Queue()
        out_q = Queue()
        
        self._run_sim(in_q, out_q, attributes)
    
    def plot(self, sim_property, parts=None):
        self.sim_input.put('SimSpace.'+sim_property)
        output = self.sim_output.get()
        
        return output
    
    class SimSpace():
        """
        This should probably be a wrapper for a c++ module.
        EDIT: Probably not going to happen for a bit
        """
        
        assembly = None
        sequence = []
        last_run = []
        physics_effects = []
        
        def __init__(self, q_in, q_out, **kwargs):
            
            self.q_in = q_in
            self.q_out = q_out
            
            for arg in kwargs:
                setattr(self, arg, copy.deepcopy(kwargs[arg]))
                
            for index, effect in enumerate(self.physics_effects):
                
                pe = effect(self)
                
                self.physics_effects[index] = pe
                
                self.sequence = self.sequence + [pe.get_timestep()]
                self.last_run = self.last_run + [0]
        
        def calculate(self, dt='auto'):
            """
            Calculates the physical parameter with lowest timestep.
            """
            
            minstep = min(self.sequence)
            index = self.sequence.index(minstep)
            nextcalc = self.physics_effects[index]
            
            nextcalc.calculate(dt = minstep)
            
            self.sequence[index] = nextcalc.get_timestep()
            
            #weave some c in here?
            #https://docs.scipy.org/doc/scipy-0.15.1/reference/generated/scipy.weave.inline.html
        
    def cmd(self, command, prnt=False):
        
        self.sim_input.put(command)
        
        ret = self.sim_output.get()
        
        if prnt:
            print(ret)
            
        return ret
    
    @staticmethod
    def _run_sim(q_in, q_out, attributes):
        running = True
        
        #Create instance
        simspace = Simulation.SimSpace(q_in, q_out, **attributes)
        
        cmd=''
        
        while running:
            if not q_in.empty():
                cmd = q_in.get()
                
                if cmd=='stop':
                    running=False
                    
                    q_out.put('Stopping')
                    
                if cmd=='T':
                    q_out.put(simspace.variables.T)
                
            #TODO: I don't like this being the main loop
            simspace.calculate()   
            
class Physics_Effect_Base:
    """
    A class to set interfaces between the simulation and
    extensions for multiphysics calculations.
    """
    
    simulation = None
    variables = []
    initvar = {}
    
    testvar = 'test'
    
    def __init__(self, simulation, **kwargs):
        self.simulation = simulation
        
    def calculate(self):
        """
        This is where the matrix calculations are done
        """
        
    @classmethod
    def define_variables(cls, simulation):
        """
        Creates columns in the variable dataframe for data.
        """
        
        for var in cls.variables:
            if var not in simulation.variables.columns:
                if var in cls.initvar.keys():
                    simulation.variables[var] = cls.initvar[var]
                else:
                    simulation.variables[var] = np.nan
    
class Thermal_Conduction(Physics_Effect_Base):
    """
    A class to define conduction calculations
    """
    
    timestep = None
    variables = ['T']
    
    def __init__(self, simulation, **kwargs):
        super(Thermal_Conduction, self).__init__(simulation, **kwargs)
        
#        self.parts = kwargs['thermal_sim_parts']
            
    def get_timestep(self):
        #TODO: Placeholder function
        self.timestep = 0.5 #s
        
        return self.timestep
        
    def calculate(self, dt):
        """
        Calculates the conduction (currently dummy formula)
        """
        
        import tensorflow as tf
        
        T = self.simulation.variables['T'].values
#        T_neighbors = np.split(self.simulation.variables['T'].values \
#                               [assembly._adjacent_flat],
#                               assembly._adjacent_cell_starts[1:])
        
        T = tf.constant(T, dtype=tf.float64)
        T_n = assembly.adjacent_tf
        dt = tf.constant(dt, dtype=tf.float64)
        c = tf.constant(0.01, dtype=tf.float64)
        
#        print(type(T), type(T_neighbors), type(dt), "\n")
        
        T_n_means = tf.math.reduce_mean(T_n, axis=1)
        
        T_out = T-dt*(T-T_n_means)*c
        
#        print(T[0])
        
        self.simulation.variables['T'] = T_out.numpy()
        
#T = np.split(self.simulation.variables['T'][assembly._adjacent_flat], assembly._adjacent_cell_starts[1:])
    
if __name__ == '__main__':
    
    from pyfea.fea.geometry import SurfaceMesh, Part, Assembly

#    filename = '../../examples/testfiles/scramjet/Body.stl'
    filename = '../../examples/testfiles/cube.stl'

    sm = SurfaceMesh(filename = filename)
    em = Part(surface_mesh=sm)
    
    em.gen_mesh_from_surf(meshing='gmsh', element_size=(1000.0,10.0**22))
    em.get_adjacent()

    assembly = Assembly([em])
    
    sim = Simulation(assembly, physics_effects = [Thermal_Conduction])
    
    #To set some random temps between 10C and 40C 
    sim.variables.T = sim.variables.T.apply(lambda x: np.random.rand()*30+10)
    
#    sim.set_boundary_conditions()