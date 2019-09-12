# -*- coding: utf-8 -*-

from pyfea.fea.simulation import Simulation, Thermal_Conduction, Stress_Strain
from pyfea.fea.geometry import SurfaceMesh, Part, Assembly
from pyfea.fea.materials import Material

import numpy as np

#filename = 'testfiles/scramjet/Body.stl'
filename = 'testfiles/cube.stl'

sm = SurfaceMesh(filename = filename)

m = Material('AISI 6000 steel',
             E=207*10**9,
             Cp=0.475*10**-3,
             k=46.6)

em = Part(surface_mesh=sm, material=m)

em.gen_mesh_from_surf(meshing='gmsh', element_size=(5.0,10.0**22))
em.get_adjacent()

assembly = Assembly([em])

sim = Simulation(assembly, physics_effects = [Thermal_Conduction, Stress_Strain])
#sim = Simulation(assembly, physics_effects = [Stress_Strain])

#To set some random temps between 10C and 40C 
sim.variables.T = sim.variables.T.apply(lambda x: np.random.rand()*30+10)

sim.run()

#sim.plot_rt('T', dt=0.1, t=20)

sim.plot_gif('T', 'out.gif', dt=0.1, t=30)