#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command list-sites
Author: Dorothea Fennell
Changelog:
    7-27-26: File created, comments added
    7-30-26: Updated to put try loop in read_pairs
    11-2-26: Updated to get pairs via inversion symmetry
    11-4-26: Updated to add loop to try wrapping middle layer to unit cell if pairs can't be identified the first time
"""
#import
import os
import sys
import shutil
from pymatgen.core.structure import Structure
import numpy as np

def save_pairs_to_file(pairs, filename):
    with open(filename, 'w') as file:
        filestr = filename.strip('.txt').replace('_',' ')
        file.write(f'#{filestr}\n')
        for i,pair in enumerate(pairs):
            file.write(f"{i}: {pair[0]},{pair[1]}\n")

def identify_pairs(struc):
    '''Gets inversion pairs for structure using symmetry.'''
    #center structure at origin
    centered_struc = struc.copy()
    centered_struc.translate_sites(range(len(centered_struc.sites)),(-0.5,-0.5,-0.5),frac_coords=True, to_unit_cell=False)
    #get sites
    sites = struc.sites
    #define lists for middle layer (z=0) and index pairs
    mid_sites = []
    mid_idx = []
    idx_pairs = []
    #create list for skipped idxs
    skipped_idxs = []
    #get idx pairs
    for i,site in enumerate(centered_struc.sites):
        coords = site.frac_coords * -1
        if np.abs(coords[2]) <= 1e-06:
            #if z=0, add to middle layer lists
            mid_sites.append(site)
            mid_idx.append(i)
            continue
        else:
            for j, inv_site in enumerate(centered_struc.sites):
                #get the inverse coordinates
                inv_coords = inv_site.frac_coords
                dist, image = centered_struc.lattice.get_distance_and_image(coords,inv_coords)
                if dist < 1e-03 and i!=j:
                    if any(j in [x,y] for [x,y] in idx_pairs):
                        continue
                    else:
                        idx_pairs.append([i,j])
    pairs_no_mid = idx_pairs.copy()
    #handle middle layer
    mid_layer = Structure.from_sites(mid_sites)
    #find center of mass
    weights = [site.species.weight for site in mid_layer.sites]
    com = np.average(mid_layer.frac_coords, weights=weights, axis=0)
    #invert middle layer through center of mass
    for i,site in enumerate(mid_sites):
        coords = (site.frac_coords - com) * -1
        for j, inv_site in enumerate(mid_sites):
            inv_coords = inv_site.frac_coords - com
            dist, image = mid_layer.lattice.get_distance_and_image(coords,inv_coords)
            if dist < 1e-03 and i!=j:
                og_i = mid_idx[i]
                og_j = mid_idx[j]
                if any(og_j in [x,y] for [x,y] in idx_pairs):
                    continue
                else:
                    idx_pairs.append([og_i,og_j])
    #check to see if middle layer got added and try wrapping middle layer to unit cell if it didn't work
    if len(idx_pairs) != len(sites)/2:
        idx_pairs = pairs_no_mid.copy()
        mid_layer = Structure.from_sites(mid_sites, to_unit_cell=True)
        #find center of mass
        weights = [site.species.weight for site in mid_layer.sites]
        com = np.average(mid_layer.frac_coords, weights=weights, axis=0)
        #invert middle layer through center of mass
        for i,site in enumerate(mid_sites):
            coords = (site.frac_coords - com) * -1
            for j, inv_site in enumerate(mid_sites):
                inv_coords = inv_site.frac_coords - com
                dist, image = mid_layer.lattice.get_distance_and_image(coords,inv_coords)
                if dist < 1e-03 and i!=j:
                    og_i = mid_idx[i]
                    og_j = mid_idx[j]
                    if any(og_j in [x,y] for [x,y] in idx_pairs):
                        continue
                    else:
                        idx_pairs.append([og_i,og_j])
    #sort list
    idx_pairs.sort(key=sort_by_idx)
    
    #check indices in list
    for i,site in enumerate(centered_struc.sites):
        if any(i in [x,y] for [x,y] in idx_pairs):
            continue
        else:
            skipped_idxs.append(i)
    
    #ensure list is correct length
    if len(idx_pairs) != (len(sites)/2):
        print(f"Symmetry pairs couldn't be identified for {len(skipped_idxs)} atoms.")
        print(f"Skipped indices: {skipped_idxs}")
        return False
    #ensure site pairs are the same species
    for [i,j] in idx_pairs:
        ele_i = sites[i].species_string
        ele_j = sites[j].species_string
        if ele_i != ele_j:
            print(f'Sites {i} and {j} are not the same element and your structure is NOT inversion symmetric.')
            return False
    #return idx pairs
    return idx_pairs

def get_pairs(settings):
    '''Writes list of atom pairs for each species in the structure.'''
    base_dir = os.getcwd()
    #get poscar
    userdir = os.path.expanduser('~/wf-user-files')
    poscar = settings['poscar-file']
    fullpath = os.path.join(userdir, poscar)
    shutil.copy(fullpath, os.path.join(base_dir,'POSCAR'))
    #get structure
    struc = Structure.from_file(os.path.join(base_dir,'POSCAR'))
    #print(type(struc))
    #get inversion pairs
    idx_pairs = identify_pairs(struc)
    #check if pairs were written
    if type(idx_pairs) == bool:
        print('Due to lack of symmetry, atom pairs could not be identified. Please check your structure and try again.')
        sys.exit()
    #get pairs for each element
    element_pairs = {}
    for e in struc.chemical_system_set:
        pair_list = []
        for pair in idx_pairs:
            ele = struc.sites[pair[0]].species_string
            if e == ele:
                pair_list.append(pair)
        element_pairs.update({f'{e}_pairs':pair_list})
    #save pairs to file
    for ep in element_pairs.keys(): 
        save_pairs_to_file(element_pairs[f'{ep}'], f'{ep}.txt')
        print(f"Pairs saved to {ep}.txt.")

def read_pairs(base_dir,element,settings):
    '''Read in pairs for wf modify.'''
    try:
        with open(os.path.join(base_dir,f'{element}_pairs.txt'),'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        get_pairs(settings)
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

def sort_by_idx(pair):
    return pair[0]