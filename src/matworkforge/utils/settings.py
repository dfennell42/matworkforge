#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create/Read calculation-specific settings. 
Author: Dorothea Fennell
Changelog:
    7-8-26: File created, comments added.
    7-21-26: Updated to use toml instead of tomllib, added ability to update settings
"""
#import modules
import toml
import os
import shutil

#def functions
def read_settings():
    '''Reads settings from settings.toml file and returns dictionary.'''
    base_dir = os.getcwd()
    #set defaults
    default = {'poscar-file':'POSCAR',
               'mods-file': 'Mods.txt',
               'spin-file':'SpinPairs.txt',
               'submit-file':'vasp.sh',
               'ignore-symmetry':False,
               'kpoints':{'style':'gamma','kpoint-grid':[2,2,2],'shift':[0,0,0]},
               'incar-params':{},
               'pdos-params':{}
               }
    
    #get settings
    if os.path.exists(f'{base_dir}/settings.toml'):
        settings = toml.load('settings.toml')
    
    #if settings file doesn't exist
    if 'settings' not in locals():
        userdir = os.path.expanduser('~/wf-user-files')
        set_file = os.path.join(userdir,'base_settings.toml')
        dest_file = os.path.join(base_dir,'settings.toml')
        if os.path.exists(set_file):
            shutil.copy2(set_file, dest_file)
            settings = toml.load(dest_file)
        else:
            settings = default.copy()
            #write new settings file
            with open('settings.toml','w') as w:
                toml.dump(settings,w)
    
    #if keys are missing
    for k in default.keys():
        settings.setdefault(k, default[k])
    
    #return settings
    return settings

def update_settings(new_settings):
    '''Updates settings.toml given a dictionary of values.'''
    base_dir = os.getcwd()
    #check if settings file exists
    if os.path.exists(f'{base_dir}/settings.toml'):
        pass
    else:
        userdir = os.path.expanduser('~/wf-user-files')
        set_file = os.path.join(userdir,'base_settings.toml')
        dest_file = os.path.join(base_dir,'settings.toml')
        if os.path.exists(set_file):
            shutil.copy2(set_file, dest_file)
        else:
            print("Warning: Settings file not found in ~/wf-user-files.")
    #read settings file
    settings = toml.load('settings.toml')
    #update
    settings.update(new_settings)
    #write new settings file
    with open('settings.toml','w') as w:
        toml.dump(settings,w)