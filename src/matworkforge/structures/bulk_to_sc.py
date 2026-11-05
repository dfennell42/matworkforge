#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create supercell given bulk structure
Author: Dorothea Fennell
Changelog:
    6-10-26: File created, comments added.
    6-11-26: Converted script to functions for workflow implementation.
    6-12-26: Rewrote functions to work for more crystal structures, added functions to pull from Mat. Proj API, rewrote layer check, changed write spin pairs. 
    6-15-26: Wrote user input section.
    7-1-26: Added line to convert list of spin pair tuples to strings
    7-6-26: Rewrote surface cleavage and symmetry checks.
    7-9-26: Fixed spin pairs not writing line breaks.
    11-2-26: Rewrote to assign inversion pairs using symmetry and to invert added layer in fix_layers.
"""
#import
import os
import sys
import dotenv
import numpy as np
from ase.build import cut,stack
from ase.build.tools import IncompatibleCellError
from pymatgen.core.structure import Structure
from pymatgen.core.surface import SlabGenerator
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.ext.matproj import MPRester
from pymatgen.io.vasp import Poscar
from .list_sites import identify_pairs
#define functions
def check_input(user_input):
    if user_input.lower() == 'exit':
        print('Exiting...')
        sys.exit()

def z_coord(site):
    en = site.species.average_electroneg
    y = site.frac_coords[1]
    z = site.frac_coords[2]
    return (en,z,y)

def set_mp_api():
    '''If MP API key can't be found, sets it in an dotenv env variable.'''
    pkgdir = sys.modules['lco_workflow'].__path__[0]
    print('Please input your Materials Project API key or type "exit" to quit.')
    api = input('Key:')
    check_input(api)
    dotenv.set_key(os.path.join(pkgdir,'.env'),'MP_API', api)
    
def get_from_mp(mp_id):
    '''Gets pymatgen Structure object directly from the Materials Project. Requires API key and material id.'''
    dotenv.load_dotenv()
    api_key = os.getenv('MP_API')
    if api_key == None:
        print('API key not found.')
        set_mp_api()
        dotenv.load_dotenv()
        print('Reloaded environment variables.')
        api_key = os.getenv('MP_API')
        if api_key == None:
            print('API key not found after reloading. Try setting explicitly using "export".')
            print('Exiting...')
            sys.exit()
    else:
        mpi = MPRester(os.getenv('MP_API'))
        struc = mpi.get_structure_by_material_id(mp_id)
        return struc

def fix_layers(struc):
    '''Fixes struc so cell is inversion symmetric.'''
    cell = struc.to_ase_atoms()
    layer = cut(cell,nlayers=1,tolerance=0.001)
    #flip layer to keep inversion symmetry
    coords = layer.get_scaled_positions(wrap=False)
    inv_coords = []
    for ar in coords:
        a = 1-ar[0]
        b = 1-ar[1]
        c = ar[2]
        new_coords = [a,b,c]
        inv_coords.append(new_coords)
    inv_coords = np.asarray(inv_coords)
    layer.set_scaled_positions(inv_coords)
    try:
        new_cell = stack(cell,layer)
    except IncompatibleCellError:
        return None
    #return structure
    new_struc = Structure.from_ase_atoms(new_cell)
    return new_struc

def write_poscar(base_dir,slab,formula,miller):
    '''Gets filename and writes POSCAR file.'''
    #convert miller index to str
    ms= ''.join([str(x) for x in miller])
    filename = f'{formula}-{ms}-slab.vasp'
    Poscar(slab).write_file(os.path.join(base_dir,filename))
    #print output
    print(f'POSCAR file {filename} written.')
    
def get_slab(base_dir,bulk,sc_size,miller,vacuum):
    '''Generates supercell based on user input and bulk structure.'''
    #read in file or pull from materials project
    if os.path.exists(bulk):
        struc = Structure.from_file(bulk)
    elif bulk.startswith('mp-'):
        struc = get_from_mp(bulk)
    else:
        print('Bulk structure not found, either as file or on the Materials Project. Please try again. \nExiting...')
        sys.exit(1)
    #set symmetry 
    sym = True
    #get refined structure
    ref_struc = SpacegroupAnalyzer(struc).get_refined_structure()
    #make supercell
    cell = ref_struc.make_supercell(sc_size,in_place=False,to_unit_cell=False)
    #get reduced formula for later
    formula = cell.composition.reduced_formula
    #surface cleavage
    slabgen = SlabGenerator(cell, miller, 1, vacuum,center_slab=True,primitive=False)
    slabs = slabgen.get_slabs()
    #check if slab is symmetric
    for s in slabs:
        if s.is_symmetric() == True:
            slab = s
            break
        else:
            slab = None
    #try to fix slab by adding layer
    if slab == None:
        new_struc = fix_layers(cell)
        if new_struc != None:
            new_slabgen = SlabGenerator(new_struc, miller, 1, vacuum,center_slab=True,primitive=False)
            new_slabs = new_slabgen.get_slabs()
            for s in new_slabs:
                if s.is_symmetric() == True:
                    slab = s
                    break
                else:
                    slab = None     
        if new_struc == None or slab == None:
            print('Slab inversion symmetry could not be enforced. Would you like to continue with structure generation?')
            cont = input('Please answer yes (y) or no (n):')
            if cont.lower().startswith('y'):
                sym = False
                slab = slabs[0]
                pass
            else:
                print('Exiting...')
                sys.exit()
    #sort structure first
    slab.sort(key=z_coord)
    #get reordered structure & write spin pairs if symmetric
    if sym == True:
        #get idx pairs
        idx_pairs = identify_pairs(slab)
        if type(idx_pairs) == bool:
            print('Due to lack of symmetry, SpinPairs.txt file not created.')
            reordered_cell = slab
        else:
            #reorder sites
            sites = slab.sites
            site_list = []
            for [i,j] in idx_pairs:
                site_list.append(sites[i])
                site_list.append(sites[j])
            #create reordered cell
            reordered_cell = Structure.from_sites(site_list)
            #write spin pairs if sym
            write_spin_pairs(base_dir, reordered_cell,formula)
    elif sym == False:
        print('Due to lack of symmetry, SpinPairs.txt file not created.')
    #write poscar
    write_poscar(base_dir, reordered_cell, formula, miller)

def write_spin_pairs(base_dir,reordered_cell,formula):
    '''Writes spin pairs file given organized structure. NOTE: Only writes the indices of the pairs, does not assign spin states.'''
    sites = reordered_cell.sites
    #get indices of non-alkali & non-alkaline metals
    indices = []
    for i,s in enumerate(sites):
        if s.specie.is_metal == True:
            if s.specie.is_alkali == False and s.specie.is_alkaline == False:
                indices.append(i)
    
    #get spin pairs
    spin_pairs = [(indices[i], indices[i + 1]) for i in range(0, len(indices), 2)] if len(indices) % 2 == 0 else []
    
    #check spin pairs isn't empty
    if not spin_pairs:
        print('Odd number of metals, cannot write create SpinPairs file.')
        return
    #convert tuple to str
    sp_str = [str(x).strip('()') for x in spin_pairs]
    sp_lines = [f'{x}\n' for x in sp_str]
    #write file
    with open(f'{base_dir}/SpinPairs-{formula}.txt','w') as f:
        f.writelines(sp_lines)
    print(f'SpinPairs-{formula}.txt file created. NOTE: Spin states (up,down) must be assigned by hand!')

def create_structure(bulk=None,sc_size=None,miller=None,vacuum=10):
    '''Generates surface structure based on bulk structure and user input. Bulk structure can be given as a file or as a Materials Project ID. Note: If using Materials Project, an API key MUST be provided. User input can be provided either through input prompts or using command line options.'''
    
    base_dir = os.getcwd()
    if not any((bulk,sc_size,miller)):
        print('\nIf you would like to exit at any point, type "exit" into any input prompt.')
    #check if bulk file/ID has been given
    if bulk == None:
        print('\nPlease provide a filepath (relative or absolute) or Materials Project ID for the bulk structure. Material IDs should start with "mp-".')
        bulk = input('Filepath or ID:')
        check_input(bulk)
    
    #check if sc_size has been given
    if sc_size == None:
        print('\nPlease provide the size of the desired supercell.The size can be provided as a full set of lattice vectors or as a list of scaling factors.')
        print('If inputing vectors, please provide a comma-separated list of vectors, with each vector in brackets. eg. [2,1,0],[0,2,0],[0,0,1].')
        print('If inputing scaling factors, please input as a comma-separated list. eg. a,b,c. ')
        #wrap input prompt in a while loop so it can repeat
        while True:
            sc = input('Supercell size:')
            check_input(sc)
            #check length of input to determine 
            sc = sc.strip()
            #if len = 5, it's a list of scaling factors
            if len(sc) == 5:
                sc_size = [int(x) for x in sc.split(',')]
                break
            elif len(sc) == 23:
                sc = sc.strip('[]')
                sc_ls = sc.split('],[')
                vecs = []
                for l in sc_ls:
                    ls = l.split(',')
                    v = [(int(x)) for x in ls]
                    vecs.append(v)
                sc_size = np.fromiter(vecs,dtype=np.dtype((int,3)))
                break
            else:
                print("Given input doesn't match required parameters. Please try again.")
    elif sc_size != None:
        #check length of input to determine 
        sc = sc_size.strip()
        #if len = 5, it's a list of scaling factors
        if len(sc) == 5:
            sc_size = [int(x) for x in sc.split(',')]
        elif len(sc) == 23:
            sc = sc.strip('[]')
            sc_ls = sc.split('],[')
            vecs = []
            for l in sc_ls:
                ls = l.split(',')
                v = [(int(x)) for x in ls]
                vecs.append(v)
            sc_size = np.fromiter(vecs,dtype=np.dtype((int,3)))
        
    #check for miller index
    if miller == None:
        print("Please provide the Miller index of the cell as a comma-separated list of 3 values. If no input is provided or input isn't a list, index will default to (001).")
        ml_str = input('Miller index:')
        check_input(ml_str)
        if len(ml_str) == 0:
            miller = (0,0,1)
        elif len(ml_str) == 5:
            miller = tuple(int(x) for x in ml_str.split(','))
        else:
            miller = (0,0,1)
    elif miller != None:
        if len(miller) == 5:
            miller = tuple(int(x) for x in miller.split(','))
        else:
            miller = (0,0,1)
    #now that all the params are set, build the supercell
    get_slab(base_dir,bulk,sc_size,miller,vacuum)
    






