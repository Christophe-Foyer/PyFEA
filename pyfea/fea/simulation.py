# -*- coding: utf-8 -*-
"""
Created on Tue Jul 30 18:35:18 2019

@author: Christophe
"""

# %% Imports

import threading
from queue import Queue

import inspect
import copy

import pandas as pd
import numpy as np
        
import tensorflow as tf

from pyfea.fea.materials import Material

# %% Simulation

class Simulation():
    """
    Simulation class to run transient FEA of an assembly according to specified
    physics modules.
    """
    
    assembly = None
    boundary_conditions = {}
    parameters = {}
    physics_effects = []
    running = False
    
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
        
        self.running=True
        
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
    
    def __getattribute__(self, name):
        """
        Wrapper to manage fetching attributes.
        """
        
        if name == 'variables' and self.running:
            self.variables = self.get('variables')

        ret = super(Simulation, self).__getattribute__(name)
        return ret 
    
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
        
    # %% Sim commands
        
    def cmd(self, command, prnt=False):
        assert self.running, 'Not running.'
        assert command != 'stop', 'Please use the intended .stop() to stop the simulation.'
        
        self.sim_input.put(command)
        
        ret = self.sim_output.get()
        
        if prnt:
            print(ret)
            
        return ret
    
    def get(self, variable):
        assert self.running, 'Not running.'
        assert type(variable) == str
        assert len(variable) > 0
        
        command = 'get ' + variable
        
        self.sim_input.put(command)
        
        return self.sim_output.get()
    
    def getvar(self, variable):
        assert self.running, 'Not running.'
        assert type(variable) == str
        assert len(variable) > 0
        
        command = 'getvar ' + variable
        
        self.sim_input.put(command)
        
        return self.sim_output.get()
    
    def stop(self):
        assert self.running, 'Not running.'
        
        self.sim_input.put('stop')
        
        self.running=False
        
        return self.sim_output.get()
        
    # %% Sim loop    
    
    @staticmethod
    def _run_sim(q_in, q_out, attributes):
        running = True
        
        #Create instance
        simspace = Simulation.SimSpace(q_in, q_out, **attributes)
        
        cmd=''
        
        while running:
            if not q_in.empty():
                cmd = q_in.get()
                
                if cmd == 'stop':
                    running=False
                    
                    q_out.put(simspace)
                    
                    break
                    
                elif cmd.split()[0] == 'get':
                    try:
                        q_out.put(copy.deepcopy(simspace.__dict__[cmd.split()[1]]))
                    except AttributeError:
                        q_out.put('Error, no such variable')
                        
                elif cmd.split()[0] == 'getvar':
                    try:
                        q_out.put(copy.deepcopy(simspace.variables[cmd.split()[1]]))
                    except AttributeError:
                        q_out.put('Error, no such variable')
                        
                else:
                    try:
                        ret = exec(cmd)
                        q_out.put(copy.deepcopy(ret))
                    except:
                        q_out.put('Something went wrong...')
                
            #TODO: I don't like this being the main loop
            simspace.calculate()   
        
# %% Physics
        
class Physics_Effect_Base:
    """
    A class to set interfaces between the simulation and
    extensions for multiphysics calculations.
    """
    
    simulation = None
    variables = []
    materialprops = []
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
        
        lists = list(cls.variables) + list(cls.materialprops)
        
        for var in lists:
            if var not in simulation.variables.columns:
                
                #user declared variables
                if var in cls.initvar.keys():
                    simulation.variables[var] = cls.initvar[var]
                    
                #make it work for materials
                elif all([var in material.__dict__ for material 
                          in simulation.assembly.materials]):
                    simulation.variables[var] = [m.__dict__[var] for m 
                                         in simulation.assembly.materials]
                    
                else:
                    simulation.variables[var] = np.nan
    
class Thermal_Conduction(Physics_Effect_Base):
    """
    A class to define conduction calculations
    """
    
    timestep = None
    variables = ['T']
    materialprops = ['Cp','k']
    
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
        
        # TODO: This is bogus math
        
        T = tf.constant(self.simulation.variables['T'].values, dtype=tf.float64)
        Cp = tf.constant(self.simulation.variables['Cp'].values, dtype=tf.float64)
        k = tf.constant(self.simulation.variables['k'].values, dtype=tf.float64)
#        T_neighbors = np.split(self.simulation.variables['T'].values \
#                               [assembly._adjacent_flat],
#                               assembly._adjacent_cell_starts[1:])
        
        T_n = tf.RaggedTensor.from_row_splits(values=self.simulation.variables['T'].values[assembly._adjacent_flat],
                                              row_splits=assembly._adjacent_row_splits)
        
        dt = tf.constant(dt, dtype=tf.float64)
        c = tf.constant(0.1, dtype=tf.float64)
        
#        print(type(T), type(T_neighbors), type(dt), "\n")
        
        T_n_means = tf.math.reduce_mean(T_n, axis=1)
        
        T_out = T-dt*(T-T_n_means)*c
        
#        print(T[0])
        
        self.simulation.variables['T'] = T_out.numpy()
        
#T = np.split(self.simulation.variables['T'][assembly._adjacent_flat], assembly._adjacent_cell_starts[1:])
    
class Stress_Strain(Physics_Effect_Base):
    """
    Attempts a structural model of the assembly
    (lots of variables, might take some time)
    """
    
    timestep = None
    variables = ['sigma', 'tau']
    materialprops = ['E']
    initvar = {'sigma':0, 'tau':0}
            
    def get_timestep(self):
        #TODO: Placeholder function
        self.timestep = 0.5 #s
        
        return self.timestep
        
    def calculate(self, dt):
        """
        Calculates the conduction (currently dummy formula)
        """
        
        pass
    
#    @classmethod
#    def define_variables(cls, simulation):
#        super(Stress_Strain, self).define_variables(simulation)
#        
#        simulation.variables['E'] = 
        
    
# %% Testing
    
if __name__ == '__main__':
    
    from pyfea.fea.geometry import SurfaceMesh, Part, Assembly

    filename = '../../examples/testfiles/scramjet/Body.stl'
#    filename = '../../examples/testfiles/cube.stl'

    sm = SurfaceMesh(filename = filename)
    
    m = Material('AISI 6000 steel',
                 E=207*10**9,
                 Cp=0.475*10**-3,
                 k=46.6)
    
    em = Part(surface_mesh=sm, material=m)
    
    em.gen_mesh_from_surf(meshing='gmsh', element_size=(10.0,10.0**22))
    em.get_adjacent()

    assembly = Assembly([em])
    
    sim = Simulation(assembly, physics_effects = [Thermal_Conduction, Stress_Strain])
#    sim = Simulation(assembly, physics_effects = [Stress_Strain])
    
    #To set some random temps between 10C and 40C 
    sim.variables.T = sim.variables.T.apply(lambda x: np.random.rand()*30+10)
    
    sim.run()
    
#    sim.set_boundary_conditions()