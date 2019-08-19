<h1 id="pyfea">PyFEA</h1>

<table>
  <tbody>
    <tr>
      <td>Christophe Foyer 2019</td>
      <td><a href="https://www.cfoyer.com">www.cfoyer.com</a></td>
    </tr>
  </tbody>
</table>

<p><strong>Note:</strong> PyFEA is currently in the early stages of development and will evolve significantly over the course of the next few months.</p>

<h2 id="about">About</h2>
<p>PyFEA is built to be an extendable suite for FE analysis in python, as this is a work in progress, no real documentation is currently provided but examples will be added to the examples folder as they are created. 
The focus will be on explicit FEM applied to transient simulations (and therefore will support steady-state, albeit at a maybe larger computation time).</p>

<h2 id="current-progress">Current progress</h2>
<ul>
  <li>Interface with the <a href="https://gitlab.onelab.info/gmsh/gmsh/blob/master/api/gmsh.py">gmsh api</a> for meshing</li>
  <li>Interface with <a href="https://github.com/pyvista/tetgen/tree/master/tetgen">tetgen</a> for meshing (some issues, but basic functionality exists)</li>
  <li>Generating meshes from STP files</li>
  <li>Generating meshes from STL files</li>
</ul>

<div>
  <img src="project_files/screenshots/meshing2.png" height=220></img>
  <img src="project_files/screenshots/meshing.png" height=220></img>
</div>

<h2 id="to-do">To Do</h2>
<ul>
  <li>[In progress] Create easy way to interact with elements and set up multi-sim problems</li>
  <li>Support multiphysics extensions</li>
  <li>Improve neighboring cell finder performance</li>
  <li>Fix interface (outer faces) between entitymeshes in assemblies</li>
</ul>

<h2 id="dependencies">Dependencies</h2>
<h3 id="required">Required:</h3>
<ul>
  <li>numpy</li>
  <li>pyvista</li>
  <li>tensorflow</li>
  <li><a href="https://gmsh.info/">gmsh</a></li>
</ul>

<h3 id="optional">Optional:</h3>
<ul>
  <li>Interfaces with <a href="https://github.com/peterdsharpe/AeroSandbox">AeroSandbox</a> (WIP)</li>
  <li><a href="https://github.com/pyvista/tetgen/tree/master/tetgen">tetgen</a> (currently inferior to gmsh)</li>
</ul>

<hr />

<h3 id="documentation-wip"><a href="http://pyfea.cfoyer.com/docs/build/html/index.html">Documentation (WIP)</a></h3>

<hr />

<h3 id="mit-license">MIT License</h3>

<p>Copyright © 2019 Christophe Foyer</p>

<p>Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:</p>

<p>The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.</p>

<p>The software is provided "As is", without warranty of any kind, express or
Implied, including but not limited to the warranties of merchantability,
Fitness for a particular purpose and noninfringement. In no event shall the
Authors or copyright holders be liable for any claim, damages or other
Liability, whether in an action of contract, tort or otherwise, arising from,
Out of or in connection with the software or the use or other dealings in the
Software.</p>
