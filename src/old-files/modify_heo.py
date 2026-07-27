#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modify structure while ignoring symmetry.
Author: Dorothea Fennell
Changelog:
    2-25-26: Created, comments added
"""
#import modules
from ase.io import read, write
import os
import copy
import shutil

#define functions
def read_modifications(filename):
    modifications = []
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().replace(" ", "").split(',')
            indices = list(map(int, parts[:-len(parts) // 2]))
            new_elements = parts[-len(parts) // 2:]
            modifications.append((indices, new_elements))
    return modifications

def mod_structure(atoms):
    '''Modifies atoms in structure based on ModsIdx.txt file.'''
    mods = read_modifications('ModsIdx.txt')
    for mod, (indices, new_elements) in enumerate(mods):
        modified_atoms = copy.deepcopy(atoms)
        for i, idx in enumerate(indices):
            modified_atoms[idx].symbol = new_elements[i]
                
        # Make new directory for each new structure
        directory_name = f"Modification_{mod + 1}"
        os.makedirs(directory_name, exist_ok=True)
        
        output_filename = os.path.join(directory_name, f"POSCAR_modified_{mod + 1}.vasp")
        write(output_filename, modified_atoms, format="vasp")
        print(f"Modified POSCAR saved in directory {directory_name} as {output_filename}.")

def modify_without_sym(base_dir):
    '''Creates modification directories based on ModsIdx.txt while ignoring symmetry.'''
    userdir = os.path.expanduser('~/wf-user-files')
    fullpath = os.path.join(userdir, 'POSCAR-HEO')
    shutil.copy(fullpath, f'{base_dir}/POSCAR')
    # Read POSCAR 
    atoms = read(os.path.join(base_dir,'POSCAR'))
    #modify structure
    mod_structure(atoms)
    