#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Submit calculations - conversion from bash script
Author: Dorothea Fennell
Changelog:
    6-24-26: File created, comments added
    6-25-26: Command finished.
    7-21-26: Updated to pull submission script name from settings
"""
#import 
import os
import toml
import shutil
import subprocess as sp
from rich import print
from .preflight import check_inputs
#define funcs
def get_dirs(base_dir,calc_type):
    '''Gets list of directories.'''
    calc_dirs = []
    for root,dirs,files in os.walk(base_dir):
        if root.endswith(calc_type):
            calc_dirs.append(root)
    return calc_dirs

def submit_calcs(calc_type,force=False,skip_preflight=False):
    '''Submits calculations.'''
    #get dirs
    base_dir = os.getcwd()
    if calc_type == 'all':
        all_dirs = []
        calcs = ['VASP_inputs','_Removed','_Added']
        for calc in calcs:
            calc_dirs = get_dirs(base_dir,calc)
            all_dirs.extend(calc_dirs)
    else:
        all_dirs = get_dirs(base_dir,calc_type)
    #check if calculation has been run
    not_run = all_dirs.copy()
    if force != True:
        for d in all_dirs:
            name = d.replace(f'{base_dir}','.')
            if 'OUTCAR' in os.listdir(d):
                print(f'Skipping {name}, calculation has already been run.')
                not_run.remove(d)
    
    if not not_run:
        print('All calculations have been run. Exiting...')
        return
    
    #preflight check
    chk_passed = not_run.copy()
    failed = []
    if skip_preflight != True:
        for d in not_run:
            name = d.replace(f'{base_dir}','.')
            prechk = check_inputs(base_dir, d)
            if not prechk.empty:
                print(f'[red1]Preflight Error:[/] Error with input files in {name}. Skipping...')
                failed.append(name)
                chk_passed.remove(d)
    
    if not chk_passed:
        print('No calculations to submit. Exiting...')
        return
    
    #check settings for submission script name
    if os.path.exists(f'{base_dir}/settings.toml'):
        settings = toml.load(f'{base_dir}/settings.toml')
        script_name = settings['submit-file']
    else:
        script_name = 'vasp.sh'
    #copy vasp.sh to base_dir
    filedir = os.path.expanduser('~/wf-user-files')
    fullpath = os.path.join(filedir, script_name)
    shutil.copy(fullpath, base_dir)
    
    for d in chk_passed:
        sh_path = os.path.join(base_dir,script_name)
        shutil.copy(sh_path,d)
        print(f'Submitting calculation in {d}...')
        os.chdir(d)
        sp.run(['sbatch',f'{script_name}'], check=True)
        os.chdir(base_dir)
    
    print('All jobs submitted.')
    
