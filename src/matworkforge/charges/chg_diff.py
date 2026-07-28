#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate and visualize charge transfer
Author: Dorothea Fennell
Changelog:
    6-3-26: File created, comments added. Struggling with making this run recursively, due to the necessity for unrelaxed structures.
    6-8-26: Finished plotting function.
"""
#import modules
import os
import sys
import numpy as np
from pymatgen.io.vasp.outputs import Chgcar, VolumetricData
from ase.io import read
from ase.data.colors import jmol_colors
import pyvista as pv

def calc_chgdiff(base_dir,pris_file, vac_files):
    '''Gets CHGCAR for pristine and vacancy structures and returns CHGDIFF'''
    #get pristine CHGCAR
    if os.path.exists(pris_file):
        try:
            pris_chg = Chgcar.from_file(f'{pris_file}')
        except:
            print('Cannot read pristine CHGCAR. Exiting...')
            sys.exit()
    else:
        print('Cannot find pristine CHGCAR. Please check given path and try again. Exiting...')
        sys.exit()
    
    #Get vacancy CHGCAR(s)
    vacs = []
    for vac in vac_files:
        if os.path.exists(vac.strip()):
            try:
                vac_chg = Chgcar.from_file(f'{vac}')
                vacs.append(vac_chg)
            except:
                print('Cannot read vacancy/adsorption CHGCAR. Skipping...')
                continue
        else:
            print('Cannot find vacancy/adsorption CHGCAR. Skipping...')
            continue
    
    #check list isn't empty
    if not vacs:
        print('Vacancy/adsorption CHGCAR(s) not found or cannot be read. Exiting...')
        sys.exit()
    
    #Subtract data
    diff_data = pris_chg.data['total']
    for v in vacs:
        try:
            diff_data -= v.data['total']
        except:
            print('Real space grids are of different sizes. Please use an unrelaxed calculation for the vacancy structure.')
            sys.exit()
    
    #write data to cube file
    struc = vac_chg.poscar
    vol_data = VolumetricData(structure=struc.structure, data={'total':diff_data})
    vol_data.to_cube(f'{base_dir}/CHGDIFF.cube')    
    print('CHGDIFF.cube file created.')
    return 

def plot_chgdiff(base_dir):
    '''Plots calculated CHGDIFF.'''
    #get structure info
    struc = read(f'{base_dir}/CHGDIFF.cube')
    pos = struc.positions
    cell = struc.cell
    atomic_numbers = struc.get_atomic_numbers()
    atomic_symbols = struc.get_chemical_symbols()
    #set up plotter
    pl = pv.Plotter()
    
    #plot atoms
    for i,center in enumerate(pos):
        atm_num = atomic_numbers[i]
        sph = pv.Sphere(radius=0.6,center=center) #set atoms to 0.75x normal radius so chg data is easier to read
        pl.add_mesh(sph,color=jmol_colors[atm_num],smooth_shading=True,name=f'{atomic_symbols[i]}_{i}')
    
    #read chg data & define contours
    grid = pv.read('CHGDIFF.cube')
    sargs = dict(height=0.2,title='Δe-',vertical=True,title_font_size=25,bold=True,n_labels=3)
    color_table = pv.LookupTable(cmap='plasma',n_values=2,scalar_range = (-100,100))
    def adjust_contours(value):
        if 'contours' in pl.actors.keys():
            pl.remove_actor('contours',render=False)
        cont = grid.active_scalars.max()*value
        contours = grid.contour([cont],scalars=np.abs(grid.active_scalars))
        contours = contours.interpolate(grid)
        pts = contours.points
        dim = np.array(grid.bounds_size)
        contours.points[...] =np.dot(pts, cell / np.array(dim)[:, np.newaxis,])
        pl.add_mesh(contours,cmap=color_table,opacity=0.6,label='charge density',scalar_bar_args=sargs,name='contours',annotations={60:'+',-40:'-'})

    slider_style = pv.global_theme.slider_styles.classic
    slider_style.tube_color = (0,0,0)
    slider_style.slider_color = (0,0,0)
    slider_style.slider_width = 0.03
    slider_style.slider_length = 0.02
    pl.add_slider_widget(adjust_contours,[0.05,0.75],title='Adjust isosurface level',pointa=(0.7,0.9),pointb=(0.95,0.9),title_height=0.02,style='classic')
    pl.show_axes()
    pl.show()
    return

def check_input(user_input):
    if user_input.lower() == 'exit':
        print('Exiting...')
        sys.exit()
        
def get_chgdiff(no_show_img=False):
    '''Gets user input for CHGCAR files and returns CHGDIFF.cube and plots the charge difference.'''
    #get user input
    base_dir = os.getcwd()
    print('\nIf you would like to exit at any point, type "exit" into any input prompt.')
    print('\nPlease input the path of the pristine CHGCAR file.')
    pris_file = input('Pristine CHGCAR:')
    check_input(pris_file)
    print('\nPlease input the path to the vacancy or adsorption CHGCAR file(s). If there are multiple files, please input the paths as a comma-separated list.')
    vacs = input('Vacancy/Adsorption CHGCAR(s):')
    check_input(vacs)
    vac_files = vacs.split(',')
    #calc chgdiff
    calc_chgdiff(base_dir, pris_file, vac_files)
    #plot chgdiff
    if no_show_img == False:
        plot_chgdiff(base_dir)
    elif no_show_img == True:
        print('Skipping visualization...')