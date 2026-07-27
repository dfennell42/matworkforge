#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 16:41:42 2025

@author: dfennell
"""

import os
import pandas as pd
def get_dirs(base_dir):
    '''Runs through all directories in base directory and returns list of pdos directories.'''
    pdos_dirs=[]
    for root, dirs, files in os.walk(base_dir):
        if root.endswith("PDOS") and "TotalDos.dat" in files:
            pdos_dirs.append(root)
        elif root.endswith("PDOS") and "TotalDos.dat" not in files:
            print("PDOS data hasn't been parsed yet.")
    return pdos_dirs

def get_all_data(base_dir):
    pdos_dirs = get_dirs(base_dir)

    if not pdos_dirs:
        print('No PDOS directories found. Exiting...')
        return
    def dir_sort(pdos_dir):
        pdir = pdos_dir.split('/')
        for p in pdir:
            if p.startswith('Modification_'):
                dir_num = p.split('_')[1]
                num = int(dir_num)
                return num
            
    tot_data = []
    #tot_data.append('Atom,e_tot,OS,spin,H d/p,Orbital')
    pdos_dirs.sort(key=dir_sort)
    for pdos_dir in pdos_dirs:
        pdir = pdos_dir.split('/')
        for p in pdir:
            if p.startswith('Modification_'):
                mod_name = p
                
        with open(os.path.join(pdos_dir,'integrated-pdos.csv'),'r') as p:
            lines = p.readlines()
        t_lines = lines[1:]
        t_data = [[mod_name,'e_tot','OS','spin','']]
        for x in t_lines:
            x_list = x.split(',')
            ele = x_list[0]
            idx = x_list[1]
            atom = f'{ele}{idx}'
            ser_list = [atom,x_list[2],x_list[3],x_list[4],x_list[5].strip('\n'),'']
            t_data.append(ser_list)
            
        
        tot_data.append(pd.DataFrame(t_data))
        
    df = pd.concat(tot_data,axis=1)
    df.to_csv('./total-integrated-pdos.csv',index=False, header=False)


