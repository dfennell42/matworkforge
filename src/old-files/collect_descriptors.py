#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract all descriptors and collect in one file.
Author: Dorothea Fennell
Changelog:
    1-27-26: Created, comments added.
    2-3-26: Added line to set index of total data frame to the modification.
    2-18-26: Changed extraction command to run function from get_descriptors.py rather than running the command in the terminal. 
"""
#import modules
import os
import pandas as pd
from datetime import date
from .get_descriptors import extract_desc

#define functions
def get_date():
    '''gets current date.'''
    today = date.today()
    date_str = today.strftime('%b%d')
    return date_str

def check_file(head_dir):
    '''checks for existing descriptors.csv'''
    #check if file exists
    date = get_date()
    for root,dirs,files in os.walk(head_dir):
        if 'descriptors.csv' in files:
            try:
                os.replace(f'{head_dir}/descriptors.csv',f'{head_dir}/descriptors-{date}.csv')
            except:
                return False
            else:
                return True
        else:
            return True

def run_extract(head_dir):
    '''Runs wf extract command.'''
    #check descriptors.csv
    file_chk = check_file(head_dir)
    if file_chk == True:
        os.chdir(head_dir)
        try:
            extract_desc(head_dir,ask=False)
        except:
            return False
        else:
            os.chmod(f'{head_dir}/descriptors.csv',0o777)
            df = pd.read_csv(f'{head_dir}/descriptors.csv')
            return df
    elif file_chk == False:
        return False

def collect_descriptors():
    '''Runs wf extract and collects all descriptors in one giant csv file.'''
    #define dir list
    dir_list = ['/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/1M2Co',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/2M1Co',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/3Msame',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/3site-NMCperm', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/patterns', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/2CompSurf', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/copied-Ternary-Thea/NiCoM',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/copied-Ternary-Thea/NiMnM',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/copied-Ternary-Thea/MnCoM', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/copied-Ternary-Thea/FeAlM', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/4M-vars/123-ABA/pristine', 
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/NMC-NPA/jlb',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/3Co',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Natalia/NiMnVars-newpdos',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/kailey/NMC_Middle/Kai/check',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Patterns/CLEAN',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Natalia/compsurf-copy', 
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/NMCperm/new-pdos',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/ternary/NiCoM',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/ternary/NiMnM',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/ternary/MnCoM',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/ternary/FeAlM',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/4M-vars/123-ABA/pris-copy', 
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Natalia/enrich-copy',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/kailey/Enriched_Modifications/first_delithiation/CLEAN',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi/1pair/1M2Co', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi/1pair/2M1Co',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi/1pair/3Msame',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/NMC-NPA/1deLi',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Natalia/123M-Delithiation/First_Delithiation/deLi-1-reorg',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/kailey/NMC_Middle/123M-Delithiation/first_delithiation/deLi-reorg',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi/2pairs/1M2Co', 
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi/2pairs/2M1Co',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi/2pairs/3Msame',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/NMC-NPA/2deLi/dup',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Natalia/123M-Delithiation/Second_Delithiation/deLi-2-reorg',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/kailey/NMC_Middle/123M-Delithiation/second_delithiation/deLi-reorg-pdos',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi-all/3pairs/1M',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi-all/3pairs/2M',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/deLi-all/3pairs/3M',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Thea/NMC-NPA/3deLi/dup',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/Natalia/123M-Delithiation/Third_Delithiation/reorg',
                '/hpcgpfs01/scratch/CTCMO-2025/NMC-middle/kailey/NMC_Middle/123M-Delithiation/third_delithiation',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/Ga-struc/pristine',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/Ga-struc/1pair',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/Ga-struc/2pair',
                '/hpcgpfs01/scratch/CTCMO-2025/LCO-middle/Ga-struc/3pair',
                ]
    #create lists 
    desc_tot = []
    fail_list = []
    #get dataframes
    for d in dir_list:
        extract_chk = run_extract(d)
        typ = str(type(extract_chk))
        if 'bool' in typ:
            if extract_chk == False:
                fail_list.append(d)
                pass
        elif 'DataFrame' in typ:
            df = extract_chk
            lix = float(df.at[0,"Lix"])
            li = int((100-(lix*100))/5.5)
            m1 = str(21 - li)
            m2 = str(23 - li)
            m3 = str(25 - li)
            cols = df.columns.to_list()
            rename = {}
            for c in cols:
                if m1 in c:
                    new = c.replace(m1,'M1')
                    rename.update({f'{c}':new})
                if m2 in c:
                    new = c.replace(m2,'M2')
                    rename.update({f'{c}':new})
                if m3 in c:
                    new = c.replace(m3,'M3')
                    rename.update({f'{c}':new})
            df = df.rename(columns=rename)
            desc_tot.append(df)
    
    #concat dfs
    tot_df = pd.concat(desc_tot)
    tot_df.set_index('Modification',inplace=True)
    date = get_date()
    tot_df.to_csv(f'/hpcgpfs01/scratch/CTCMO-2025/Descriptors/all-descriptors-{date}.csv')
    
    if len(fail_list) >0:
        print('Descriptors not extracted for the following directories:')
        for f in fail_list:
            print(f'{f}')
    
    print('All descriptors extracted and saved to CTCMO Descriptors directory.')
    
        