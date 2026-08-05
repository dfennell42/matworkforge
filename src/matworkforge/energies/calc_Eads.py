#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate Adsorbtion energy.
Author: Dorothea Fennell
Changelog: 
    3-3-26: Created, comments added. 
    7-28-26: Modified to pull mods file name from settings.toml
"""
#import modules
import os
import sys
from ase.io import read

#define functions
def get_dirs(mod_dir):
    '''Runs through all directories in base directory and returns list of vacancy directories.'''
    ads_dirs=[]
    for root, dirs, files in os.walk(mod_dir):
        if root.endswith('Added') and 'OUTCAR' in os.listdir(root):
            ads_dirs.append(root)
    ads_dirs.sort()
    return ads_dirs

def read_file(r_dir, file):
    '''Reads given file in directory and returns list of lines'''
    F = open(os.path.join(r_dir,file),'r')
    lines = F.readlines()
    F.close()
    return lines

def get_pair_numbers(ads_dir):
    '''Get number of pairs added.'''
    pris_dir = os.path.dirname(ads_dir)
    #pristine
    pris_atoms = read(os.path.join(pris_dir,'POSCAR'))
    pf = pris_atoms.symbols.formula
    p_counts = pf.count()
    #vacancy
    ads_atoms = read(os.path.join(ads_dir,'POSCAR'))
    af = ads_atoms.symbols.formula
    a_counts = af.count()
    #determine pairs removed
    ele_ads = {}
    for key in a_counts:
        if key in p_counts:
            if p_counts.get(key) == a_counts.get(key):
                pass
            elif p_counts.get(key) != a_counts.get(key):
                num = float(p_counts.get(key)) + float(a_counts.get(key))
                ele_ads.update({f'{key}':num})
        elif key not in p_counts:
            ele_ads.update({f'{key}':a_counts.get(key)})
    return ele_ads

def get_e(e_dir):
    '''Gets final energy from OUTCAR file.'''
    if 'OUTCAR' in os.listdir(e_dir):
        lines = read_file(e_dir,'OUTCAR')
        toten = []
        for l in lines:
            if "TOTEN" in l:
                toten.append(l)
        e = toten[-1].split()
        e = float(e[4])
        return e
    
def get_ep(base_dir,mod_dir):
    '''If pristine structures are not calculated. '''
    if "E_pristine.csv" in os.listdir(base_dir):
        lp = read_file(base_dir,'E_pristine.csv')
        mod_name = os.path.basename(mod_dir)
        for ep in lp:
            sep = ep.split(',')
            if f'{sep[0]}' == f'{mod_name}':
                e_p = float(sep[2])
                return e_p
    else:
        print("Pristine structures or E_pristine.csv not found. If pristine structures haven't been calculated, copy E_pristine.csv into this directory.")
        print('Exiting...')
        sys.exit()

def calc_e_ads(e_p,ads,ads_dir,ele_ads):
    '''Calculates vacancy energy'''
    userdir = os.path.expanduser('~/wf-user-files')
    bulk_dict = read_file(userdir, 'BulkE_dict.txt')
    adsorptions=[]
    for ele in ele_ads.keys():
        for i in bulk_dict:
            if i.startswith(ele):
                num = float(ele_ads.get(ele))
                bulk = float(i.split(':')[1])
                ads_e = num * bulk
                adsorptions.append((ads_e,num))
    tot_num = 0
    tot_ads = 0
    for (a,n) in adsorptions:
        tot_ads += a
        tot_num += n
    ea = (ads-tot_ads - e_p)/tot_num
    return ea

def sort_data(data):
    '''Sorts data by atom_pair first then by dir number'''
    data_list = data.split(',')
    atom_pair = data_list[1]
    dirname = data_list[0].split('/')
    dir_num = dirname[0].split('_')[1]
    num = int(dir_num)
    return (atom_pair,num)

def get_all_e(mod_dir,mods,base_dir,ignore_sym=False):
    '''Gets total energy of pristine and vacancy surfaces.Returns list of vacancy energies.'''
    #get total energy of pristine surface
    p = os.path.join(mod_dir,'VASP_inputs/')
    e_p = get_e(p)
    
    if e_p == None:
        e_p = get_ep(base_dir,mod_dir)
    
    #get adsorption directories
    ads_dirs = get_dirs(mod_dir)
    #stops the program in no adsorption directories are found
    if not ads_dirs:
        print('No adsorption directories found. Exiting...')
        return
    
    mod_name = os.path.basename(mod_dir)
    #get e_ads for ads dirs
    ads_tot = []
    for ads_dir in ads_dirs:
        ads = get_e(ads_dir)
        ele_ads = get_pair_numbers(ads_dir)
        e_ads = calc_e_ads(e_p, ads, ads_dir, ele_ads)
        pair = os.path.basename(ads_dir).split('_')[1]
        element = os.path.basename(ads_dir).split('_')[0]
        dirname = os.path.dirname(ads_dir)
        if dirname.endswith('VASP_inputs'):
            for i, mod in enumerate(mods,1):
                if f'Modification_{i}' == f'{mod_name}':
                    mod = mod.strip('-')
                    ads_tot.append(f'\n{mod_name}/{mod},{element}_{pair},{ads},{e_ads},,')
        elif dirname.endswith('Removed') or dirname.endswith('Added'):
            prev_el = os.path.basename(dirname).split('_')[0]
            prev_pair = os.path.basename(dirname).split('_')[1]
            #get eads relative to previous structure 
            prev = get_e(dirname)
            if prev == None:
                prev = get_ep(base_dir,mod_dir)
            ea_from_prev = calc_e_ads(prev, ads, ads_dir,ele_ads)
            for i, mod in enumerate(mods,1):
                if f'Modification_{i}' == f'{mod_name}':
                    mod = mod.strip('-')
                    ads_tot.append(f'\n{mod_name}/{mod},{prev_el}_{prev_pair}/{element}_{pair},{ads},{e_ads},{ea_from_prev}')
    
    return ads_tot

def process_e_ads(base_dir,settings):
    '''Gets e_ads recursively for all dirs and returns it in one csv '''
    mod_dirs = []
    for root, dirs, files in os.walk(base_dir):
        if os.path.basename(root).startswith('Modification_'):
            mod_dirs.append(root)

    if not mod_dirs:
        print('No modification directories found.')
        return
    
    mod_file = settings['mods-file']
    #get modifications from ModsCo.txt
    mods = read_file(base_dir, mod_file)
    #convert the commas to dashes so the csv won't separate incorrectly
    mods_str = []
    for m in mods:
        ml= m.strip('\n').split(',')
        ms = ''
        for i in ml:
            ms += f'{i}-'
        mods_str.append(ms)
    mods = mods_str
    
    #calculate E_ads for each directory
    e_ads_tot = []
    for mod_dir in mod_dirs:
        ea = get_all_e(mod_dir, mods, base_dir)
        for e in ea:
            e_ads_tot.append(e)
    
    #check for values
    if e_ads_tot == None:
        return
    
    #sort data
    e_ads_tot.sort(key=sort_data)
    #write file
    with open(f'{base_dir}/E_ads.csv','w',encoding=None) as f:
        f.write('Modification,Atom Pair,Total E,E_ads (pristine),E_vac (from prev vacancy/adsorption)')
        f.writelines(e_ads_tot)
        f.close

        