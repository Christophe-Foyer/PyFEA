.. module:: pyfea.fea.geometry

pyfea.fea.geometry
==================

Tetrahedron
------------------

Base geometry, mainly for easy data output, more efficient data structures are used when calculating.

.. autoclass:: Tetrahedron
    :members:
    :undoc-members:

EntityMesh
------------------

Geometry definition class for tet meshes, groups tetrahedrons and the pointcloud matrix.

.. autoclass:: EntityMesh
    :members:
    :undoc-members:

SurfaceMesh
------------------

Geometry definition class for surface meshes, groups triangles and the pointcloud matrix.

.. autoclass:: SurfaceMesh
    :members:
    :undoc-members:
	
Part
------------------

Uses EntityMesh as a base, defines additional part information such as materials.

.. autoclass:: Part
    :members:
    :undoc-members:
	
Assembly
------------------

Uses EntityMesh as a base, groups multiple parts in an assembly.

.. autoclass:: Assembly
    :members:
    :undoc-members: