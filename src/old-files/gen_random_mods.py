#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate random Mods file for HEO compositions
Author: Dorothea Fennell
Changelog:
    2-25-26: Created, comments added
"""
#import modules
import numpy as np
from ase.io import read
import os

#define functions
def get_atoms():
    '''Reads poscar file from ~/wf-user-files and returns ASE atoms object'''
    user_dir = os.path.expanduser('~/wf-user-files')
    poscar = f'{user_dir}/POSCAR-HEO'
    atoms = read(poscar)
    return atoms

def get_mods(user_dict,mod_num,atom_num):
    '''Generates random mods file.'''    
    #create empty lists
    mods_list = []
    atom_list = []
    
    #gen list of atoms
    for el in user_dict.keys():
        for i in range(user_dict[f'{el}']):        
            atom_list.append(f'{el}')
    
    if len(atom_list) <30:
        while len(atom_list) <30:
            atom_list.append('Co')
    
    #set up numpy rng
    rng = np.random.default_rng()
    #generate list of mods
    for x in range(int(mod_num)):
        mod = rng.permutation(atom_list)
        mod_str = ','.join(mod)
        if mod_str not in mods_list:
            mods_list.append(mod_str)
    
    #generate str of atom idx
    num = np.arange(atom_num)
    num_str = ','.join(map(str,num))
    
    #generate mods file
    full_list = []
    for m in mods_list:
        full_list.append(f'{num_str},{m}\n')
    
    #write mods file
    with open(os.path.join(os.getcwd(),'ModsIdx.txt'),'w') as f:
        f.writelines(full_list)

def generate_mods_file():
    '''Generates mods file based on user input.'''
    #get atoms
    atoms = get_atoms()
    form = atoms.symbols.formula
    atom_counts = form.count()
    atom_num = atom_counts['Co']
    
    #get user input
    print(f'There are {atom_num} Co atoms in the supercell.')
    print('Please list the replacement species followed by the number of atoms in a comma-separated list.')
    print('Example: Al,6,Fe,6,Co,6, etc.')
    print('If the number of replacement atoms is fewer than the number of Co atoms, the remaining atoms will remain Co.')
    user_input = input()
    
    #split user input to dict
    user_list = user_input.strip().split(',')
    user_dict = {}
    u = 0
    for i in range(len(user_list)//2):
        user_dict.update({f'{user_list[u]}':int(user_list[u+1])})
        u +=2 
    
    #get number of mods from user
    print('How many different modificiations would you like to make?')
    mod_num = int(input('Enter number of mods:'))
    
    #create mods file
    get_mods(user_dict, mod_num, atom_num)
    print('ModsIdx.txt file created.')