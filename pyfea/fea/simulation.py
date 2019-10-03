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
import pyvista as pv
        
import tensorflow as tf

from pyfea.fea.materials import Material

import time

import matplotlib.pyplot as plt

import pyfea.interfaces.restful as rful
from sqlalchemy import create_engine

# %% Simulation

class Simulation():
    """
    Simulation class to run transient FEA of an assembly according to specified
    physics modules.
    """
    
    assembly            = None
    boundary_conditions = {}
    parameters          = {}
    physics_effects     = []
    running             = False
    data_file           = None
    sqlite_engine       = None
    
    def __init__(self, assembly, physics_effects = [],
                 webserver=False, sim_poll_freq=1):
        self.assembly = assembly
        self.physics_effects = self.physics_effects + physics_effects
        
        #To initialize the dataframe
        # TODO: Error handling
        self.variables = pd.DataFrame({'tets':[i for i in range(len(self.assembly.tets))]})
        self.variables.set_index('tets', inplace=True)
        
        for effect in self.physics_effects:
            effect.define_variables(self)
            
        import tempfile
        self.data_file = tempfile.TemporaryFile(suffix='.db').name
        #should handle opening stuff here

        #RESTful server
        self.update_database()
        engine = create_engine('sqlite:///'+self.data_file)
        
        rful.api.add_resource(rful.Sim_Data, '/sim_data')
        rful.api.add_resource(rful.Assembly_Data, '/assembly_data')
        rful.api.add_resource(rful.Part_Data, '/part_data')
        
        address, self.restful_thread = rful.run(engine)
        
        threading.Thread(target=self._poll_data, 
                         args = (self, sim_poll_freq))
        
        if webserver:
            #it autolunches itself, maybe I should explicitly ask it to
            import pyfea.tools.webserver
            #this is not very useful but eh, maybe can kill it
            import subprocess
            import atexit
            import psutil
            
            print("Starting webserver")
            print(__file__)
            
            args = ["python", pyfea.tools.webserver.__file__, self.data_file]
            process = subprocess.Popen(args, shell=True, 
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
            
            def cleanup():
                print("Cleaning up webserver...")
                p = psutil.Process(process.pid)
                for proc in p.children(recursive=True):
                    proc.kill()
                p.kill()
            
            atexit.register(cleanup)
            
            
    def set_boundary_conditions(self, **kwargs):
        for name, value in kwargs.items():
            self.boundary_conditions[name]=value
            
    def run(self, dt=None, t=None):
        
        #TODO: Find a better way?
        excluded_attr = ['webserver', 'sqlite_engine', 'restful_thread']
        
        attributes = inspect.getmembers(self, lambda a:not(inspect.isroutine(a)))
        attributes = {a[0]:a[1] for a in attributes 
                      if not(a[0].startswith('__') 
                      and a[0].endswith('__'))
                      and not inspect.isclass(a[1])
                      and not a[0] in excluded_attr}
        
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
        
    def update_database(self):
        
        filename = self.data_file
        
        if not self.sqlite_engine:
            self.sqlite_engine = create_engine('sqlite:///'+filename)
        engine = self.sqlite_engine
        
        assembly_data = {
                'assembly':[self.assembly.source_file],
                'tets':[self.assembly.tets],
                'nodes':[self.assembly.nodes]
                }
        assembly_data = pd.DataFrame(assembly_data)
        
        part_data = {
                'part':[part.name for part in self.assembly.parts],
                'tets':[part.tets for part in self.assembly.parts],
                'nodes':[part.nodes for part in self.assembly.parts]
                }
        part_data = pd.DataFrame(part_data)
        
        sim_data = self.variables
        
        assembly_data.to_sql('assembly_data', engine, if_exists='replace')
        sim_data.to_sql('sim_data', engine, if_exists='replace')
        part_data.to_sql('part_data', engine, if_exists='replace')
        
#        with open(self.data_file, 'wb') as f:
#            pickle.dump(data, f)
    
    def plot(self, sim_property, plotter = None,
             parts=None, cmap = None, **kwargs):
#        self.sim_input.put('SimSpace.'+sim_property)
        
        var = self.getvar(sim_property).to_numpy()
        
        pv.UnstructuredGrid(self.assembly.export_vtk())
        
        if not cmap: cmap = plt.cm.get_cmap("viridis", 5)
        
        grid = pv.UnstructuredGrid(self.assembly.export_vtk())
        
        if not plotter:
            plotter = pv.BackgroundPlotter()
        
        plotter.add_mesh(grid, 
                         scalars=var, 
                         stitle=sim_property,
                         rng=[var.min(), var.max()],
                         cmap = cmap,
                         **kwargs)
            
        plotter.add_axes()
        plotter.show()
        
        return plotter
    
    def plot_rt(self, sim_property, plotter=None,
                dt = 0.5, t=None, update_scale=True,
                **kwargs):
        
        var = self.getvar(sim_property).to_numpy()
        
        pv.UnstructuredGrid(self.assembly.export_vtk())
        
#        if not cmap: cmap = plt.cm.get_cmap("viridis", 5)
        
        grid = pv.UnstructuredGrid(self.assembly.export_vtk())
        grid.cell_arrays[sim_property]=var
        grid.set_active_scalar(sim_property)
        
        if not plotter:
            plotter = pv.BackgroundPlotter()
        
        plotter.add_mesh(grid,
                         scalars=sim_property,
                         stitle=sim_property,
#                         rng=[var.min(), var.max()],
                         lighting=False,
                         testure=True,
#                         cmap = cmap,
                         show_edges=True,
                         **kwargs
                         )
            
        plotter.add_axes()
#        plotter.show()
        plotter.view_isometric()
        
        def update(sim):
            t_c = 0
            
            while not t or t_c < t:
                var = sim.getvar(sim_property).to_numpy()
                grid.cell_arrays[sim_property]=var
                if update_scale:
                    plotter.update_scalar_bar_range([var.min(), var.max()])
                #this is not some critical task, good enough
                t_c = t_c + dt
                time.sleep(dt)
                
        thread = threading.Thread(target=update,
                                  args=(self,))
        thread.start()
        
        return plotter
        
#        thread.join()
        
    def plot_gif(self, sim_property, filename,
                dt = 0.5, t=20, **kwargs):
        
        print('Generating gif, please wait...')
        
        var = self.getvar(sim_property).to_numpy()
        
        pv.UnstructuredGrid(self.assembly.export_vtk())
        
#        if not cmap: cmap = plt.cm.get_cmap("viridis", 5)
        
        grid = pv.UnstructuredGrid(self.assembly.export_vtk())
        grid.cell_arrays[sim_property]=var
        grid.set_active_scalar(sim_property)
        
        plotter = pv.Plotter()
            
        plotter.open_gif(filename)
        
        plotter.add_mesh(grid, scalars=sim_property, stitle=sim_property,
#                         rng=[var.min(), var.max()],
                         lighting=False, texture=True,
                         show_edges=True, **kwargs)
            
        plotter.add_axes()
        plotter.view_isometric()
        
        t_c = 0
        plotter.write_frame()
        while t_c < t:
            var = self.getvar(sim_property).to_numpy()
            grid.cell_arrays[sim_property]=var
            #this is not some critical task, good enough
            t_c = t_c + dt
            time.sleep(dt)
            plotter.write_frame()
                
        plotter.close()
        
        print('Done.')
        
    
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
            
            self.start_time = time.time()
            self.sim_time = 0
            
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
            
    @staticmethod
    def _poll_data(sim, freq):
        while True:
            sim.update_database()
            #TODO: find a way to make it exact?
            time.sleep(freq)
        
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
        self.timestep = 0.1 #s
        
        return self.timestep
        
    def calculate(self, dt):
        """
        Calculates the conduction (currently dummy formula)
        """
        
        sim = self.simulation
        assembly = self.simulation.assembly
        
        # TODO: This is bogus math
        
        T = tf.constant(self.simulation.variables['T'].values, dtype=tf.float64)
#        Cp = tf.constant(self.simulation.variables['Cp'].values, dtype=tf.float64)
#        k = tf.constant(self.simulation.variables['k'].values, dtype=tf.float64)
#        T_neighbors = np.split(self.simulation.variables['T'].values \
#                               [assembly._adjacent_flat],
#                               assembly._adjacent_cell_starts[1:])
        
        T_n = tf.RaggedTensor.from_row_splits(values=sim.variables['T'].values[assembly._adjacent_flat],
                                              row_splits=assembly._adjacent_row_splits)
        
        dt = tf.constant(dt, dtype=tf.float64)
        c = tf.constant(0.1, dtype=tf.float64)
        
        T_n_means = tf.math.reduce_mean(T_n, axis=1)
        
        T_out = T-dt*(T-T_n_means)*c
        
        self.simulation.variables['T'] = T_out.numpy()
        
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
        
    
# %% Testing
    
if __name__ == '__main__':
    
    from pyfea.fea.geometry import SurfaceMesh, Part, Assembly

#    filename = '../../examples/testfiles/scramjet/Body.stl'
    filename = '../../examples/testfiles/cube.stl'

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
    
    sim.plot_rt('T')
    
#    sim.plot_gif('T', 'out.gif')
    
#    sim.set_boundary_conditions()