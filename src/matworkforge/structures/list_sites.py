#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command list-sites
Author: Dorothea Fennell
Changelog:
    7-27-26: File created, comments added
"""
#import
import os
import shutil

def save_pairs_to_file(pairs, filename):
    with open(filename, 'w') as file:
        filestr = filename.strip('.txt').replace('_',' ')
        file.write(f'#{filestr}\n')
        for i,pair in enumerate(pairs):
            file.write(f"{i}: {pair[0]},{pair[1]}\n")
            
def get_pairs(settings):
    '''Writes list of atom pairs for each species in the structure.'''
    base_dir = os.getcwd()
    #get poscar
    userdir = os.path.expanduser('~/wf-user-files')
    poscar = settings['poscar-file']
    fullpath = os.path.join(userdir, poscar)
    shutil.copy(fullpath, os.path.join(base_dir,'POSCAR'))
    # Define number of each element in POSCAR
    with open(os.path.join(base_dir,'POSCAR'), 'r') as P:
        P_lines = P.readlines()
    
    e_line = P_lines[5]
    elements = e_line.split()
    c_line = P_lines[6]
    counts = c_line.split()
    element_counts = {}
    pairs = {}
    for i,element in enumerate(elements):
        element_counts.update({f'{element}':float(f'{counts[i]}')})
        pairs.update({f'{element}_pairs':[]})
    # Store pairs by element
    index = 0  

    # Loop through each element and its count
    for element, count in element_counts.items():
        # Pair consecutive atoms of this element
        for i in range(int(count) // 2):
            # Append the pair to the appropriate list based on the element type
            pair = (index, index + 1)
            if f'{element}_pairs' in pairs:
                pairs[f'{element}_pairs'].append(pair)

            index += 2  # Move to the next pair
    #save pairs to file
    for element in pairs.keys(): 
        save_pairs_to_file(pairs[f'{element}'], f'{element}.txt')
        print(f"Pairs saved to {element}.txt.")

def read_pairs(base_dir,element):
    '''Read in pairs for wf modify.'''
    with open(os.path.join(base_dir,f'{element}_pairs.txt'),'r') as f:
        lines = f.readlines()
    
    #drop comment line
    lines = [l for l in lines if not l.startswith('#')]
    #get pairs
    pairs = {}
    for line in lines:
        parts = line.strip('\n').split(':')
        idx = parts[0]
        atoms = parts[1]
        atom_idxs = atoms.strip().split(',')
        pairs.update({idx:atom_idxs})
    
    #return pair dict
    return pairs
