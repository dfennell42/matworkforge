"""
Script to collect all CONTCAR files
Author: Dorothea Fennell
Changelog: 
    7-28-25: Created
    7-30-25: Wrote functions to get list of files and copy them.
"""

#import modules
import os
import shutil
import tarfile
from datetime import date
from ase.io import read
from ase.formula import Formula
#def functions
def get_files(base_dir):
    '''Gets list of CONTCAR files.'''
    filelist = []
    for root, dirs, files in os.walk(base_dir):
        if 'CONTCAR' in files:
            #check if file is empty
            with open(os.path.join(root,'CONTCAR'),'r') as c:
                if c.readlines():
                    filelist.append(os.path.join(root,'CONTCAR'))
                else:
                    print(f'CONTCAR in {root} empty. Skipping...')
    return filelist

def get_atoms(file):
    '''Determine atome indices'''
    #read file
    atoms = read(file)
    #get formula
    sym = atoms.get_chemical_formula()
    f = Formula(sym)
    atom_counts = f.count()
    #determine number of removed atoms
    if 'Li' in atom_counts.keys():
        li_rem = 18 - atom_counts.get('Li')
    else:
        li_rem = 18
    if 'O' in atom_counts.keys():
        o_rem = 36 - atom_counts.get('O')
    else:
        o_rem = 36
    li_pairs = int(li_rem/2)
    o_pairs = int(o_rem/2)
    return li_pairs, o_pairs
    
def copy_all_files(base_dir, force=False, parent=None, group=None):
    '''Copies all CONTCAR file to directory.'''
    #get files
    filelist = get_files(base_dir)
    
    #check if filelist is empty
    if not filelist:
        print('No CONTCAR files found.')
        return
    
    #get date for tarball
    today = date.today()
    date_str = today.strftime('%b_%d')
    
    for file in filelist:
        #get removed pairs
        li_pairs, o_pairs = get_atoms(file)
        #split path to determine naming
        path_list = file.split('/')
        for p in path_list:
            #get parent
            if p.startswith('LCO'):
                par = 'LCO'
            elif p.startswith('NMC'):
                par = 'NMC'
            #get group and modification number
            elif p.startswith('Modification'):
                idx = path_list.index(p)
                grp = path_list[idx-1]
                num = p.split('_')[1]
        #determine if structure is pristine or vac and where to put it
        if path_list[-2] == 'VASP_inputs':
            dir_path = '/hpcgpfs01/scratch/CTCMO-2025/Structures/Pristine'
            struc = 'pris'
        elif path_list[-2].endswith('Removed'):
            if path_list[-3] == 'VASP_inputs':
                if path_list[-2].startswith('Li_'):
                    dir_path = '/hpcgpfs01/scratch/CTCMO-2025/Structures/Li-vac'
                    struc = f'{li_pairs}Li_vac'
                elif path_list[-2].startswith('O_'):
                    dir_path = '/hpcgpfs01/scratch/CTCMO-2025/Structures/O-vac'
                    struc = f'{o_pairs}O_vac'
            elif path_list[-3].endswith('Removed'):
                dir_path = '/hpcgpfs01/scratch/CTCMO-2025/Structures/Both-vac'
                struc = f'{li_pairs}Li_{o_pairs}O_vac'
        elif path_list[-2] == 'PDOS':
            dir_path = '/hpcgpfs01/scratch/CTCMO-2025/Structures/PDOS'
            if path_list[-3] == 'VASP_inputs':
                struc = 'PDOS'
            elif path_list[-3].startswith('Li_'):
                struc = f'{li_pairs}Li_PDOS'
            elif path_list[-3].startswith('O_'):  
                struc = f'{o_pairs}O_PDOS'
                
        #construct new file name
        #check user input
        if parent == None:
            parent = par
        if group == None:
            group = grp
        new_name = f'{parent}_{group}_Mod{num}_{struc}_CONTCAR'
        dest_path = os.path.join(dir_path,new_name)
        
        #copy file
        #check if file is in directory if force not set to true
        if force == True:
            shutil.copy(file,dest_path)
        elif force == False:
            if new_name in os.listdir(dir_path):
                pass
            else:
                shutil.copy(file,dest_path)
        
        #open tar file and append file
        tar_name = f'{parent}_{group}_{date_str}.tar'
        output_dir = f'/hpcgpfs01/scratch/CTCMO-2025/Structures/Tarfiles/{date_str}'
        os.makedirs(output_dir,exist_ok=True)
        tar_path = os.path.join(output_dir,tar_name)
        if os.path.isfile(tar_path) == True:
            tar_mode = 'a'
        else:
            tar_mode = 'w'
        with tarfile.open(tar_path,tar_mode) as tar:
            if tar_mode == 'w':
                tar.add(file,arcname=new_name)
            elif tar_mode == 'a':
                if new_name not in tar.getnames():
                    tar.add(file,arcname=new_name)
    
    #when done
    print('All CONTCAR files copied.')