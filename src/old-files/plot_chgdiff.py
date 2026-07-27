#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 10:33:26 2026

@author: dfennell
"""

#modules
from ase.io import read
from ase.data.colors import jmol_colors
from ase.data import covalent_radii
import pyvista as pv
import numpy as np

#read file & set up plotter
poscar = read('CONTCAR-3Al')
pos = poscar.positions
cell = poscar.cell
atomic_numbers = poscar.get_atomic_numbers()
pl = pv.Plotter()

#plot atoms
for i,center in enumerate(pos):
    atm_num = atomic_numbers[i]
    sph = pv.Sphere(radius=(covalent_radii[atm_num]*0.75),center=center)
    pl.add_mesh(sph,color=jmol_colors[atm_num],smooth_shading=True)


#plot charge transfer
grid = pv.read('chgdiff-3Al.cube')
cont = grid.active_scalars.max()*0.1
contours = grid.contour([cont],scalars=np.abs(grid.active_scalars))
contours = contours.interpolate(grid)
pts = contours.points
dim = np.array(grid.bounds_size)
contours.points[...] =np.dot(pts, cell / np.array(dim)[:, np.newaxis,])
pl.add_mesh(contours,cmap=['cyan','yellow'],opacity=0.6,label='charge density')
pl.show_axes()
pl.view_xz()
pl.show()

