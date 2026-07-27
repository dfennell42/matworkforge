"""
Extract Bader Charges
Author: Dorothea Fennell
Changelog: 
    8-27-15: Created, comments added
"""
#import modules
from pymatgen.command_line.bader_caller import BaderAnalysis
import pandas as pd
import os

#define functions
def read_file(r_dir, file):
    '''Reads given file in directory and returns list of lines'''
    F = open(os.path.join(r_dir,file),'r')
    lines = F.readlines()
    F.close
    return lines

def get_dirs(base_dir):
    '''Gets list of PDOS directories.'''
    pdos_dirs=[]
    for root, dirs, files in os.walk(base_dir):
        if root.endswith("VASP_inputs/PDOS") and 'CHGCAR' in files:
            pdos_dirs.append(root)
        elif root.endswith("VASP_inputs/PDOS") and "CHGCAR" not in files:
            print("PDOS calculations haven't been run yet.")
    def sort_dirs(data):
        path_list = data.split('/')
        for p in path_list:
            if p.startswith('Modification_'):
                num = p.split('_')[1]
                return int(num)
    pdos_dirs.sort(key=sort_dirs)
    return pdos_dirs

def sort_mods(data):
    num = data.split('_')[1]
    return int(num)

def bader_chg(base_dir):
    '''Calculates bader charges from CHGCAR files. Returns csv file.'''
    pdos_dirs = get_dirs(base_dir)
    
    if not pdos_dirs:
        print('No PDOS directories found. Exiting...')
        return
    
    #get modifications from ModsCo.txt
    if os.path.exists(os.path.join(base_dir,'ModsCo.txt')):
        mods = read_file(base_dir, 'ModsCo.txt')
        #convert the commas to dashes so the csv won't separate incorrectly
        mods_str = []
        for m in mods:
            ml= m.strip('\n').split(',')
            ms = ''
            for i in ml:
                ms += f'{i}-'
            ms = ms.strip('-')
            mods_str.append(ms)
        mods = mods_str
    else:
        #if no ModsCo.txt file, pulls mod dir names
        mods = []
        for root, dirs, files in os.walk(base_dir):
            if os.path.basename(root).startswith('Modification_'):
                mods.append(os.path.basename(root))
        mods.sort(key=sort_mods)
        
    bader_chg_list = []
    atoms = [21,23,25,43]
    for pdos_dir in pdos_dirs:
        for i, mod in enumerate(mods,1):
            if f'Modification_{i}/' in pdos_dir:
                #create bader analysis
                bd = BaderAnalysis(chgcar_filename=f'{pdos_dir}/CHGCAR',potcar_filename=f'{pdos_dir}/POTCAR')
                bd_chg = {'Modification':mod}
                #get charge for three metals and oxygen
                for idx in atoms:
                    chg = bd.get_charge(idx)
                    bd_chg.update({f'{idx}':chg})
                bd_ser = pd.Series(data=bd_chg)
                #append series to list
                bader_chg_list.append(bd_ser)
    #create data frame from list of series & reindex by modification
    bader_chg_df = pd.DataFrame(data=bader_chg_list)
    bader_chg_df = bader_chg_df.set_index('Modification')
    bader_chg_df = bader_chg_df.rename(columns = {'21':'M21','23':'M23','25':'M25','43':'O43'})
    #print data to csv
    bader_chg_df.to_csv(f'{base_dir}/bader_charges.csv')
    print('Bader charges extracted.')
    