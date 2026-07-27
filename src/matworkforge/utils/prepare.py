#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculation directory set up command - wf prep
Author: Dorothea Fennell
Changelog:
    7-8-26: File created, comments added. 
"""
#import
import os
import shutil

#def functions
def prepare_dir():
    '''Prepares directory to create a set of calculations.'''
    base_dir = os.getcwd()
    
    #get wf-user-files dir
    userdir = os.path.expanduser('~/wf-user-files')
    
    #copy settings file
    set_file = os.path.join(userdir,'base_settings.toml')
    dest_file = os.path.join(base_dir,'settings.toml')
    if os.path.exists(set_file):
        shutil.copy2(set_file, dest_file)
    else:
        print("Warning: Settings file not found in wf-user-files. Skipping...")
    
    #create Mods file
    try:
        m = open('Mods.txt','x')
    except:
        pass
    else:
        m.close()
    
    #print
    print("Directory ready for calculations. Use the settings.toml file to set file names and custom INCAR parameters if desired.")
    print("If INCAR parameters aren't set in settings.toml, parameters will default to values in custom_incar_params.toml and pdos_incar_params.toml.")