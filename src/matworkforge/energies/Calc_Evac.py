"""
Calculate Evac O and Li
Author: Dorothea Fennell
Changelog: 
    5-2-25: Created, comments added 
    5-5-25: Finished functions to get all values of E, calculate e-vac, and run the calc recursively.
    5-9-25: Reworked to add functionality for more than one pair removal.
    5-14-25: Made minor modifications to the section that pulls the modifications from ModsCo.txt so the csv didn't separate it weirdly
    5-21-25: Added function to get pristine energy from E_pristine.csv if OUTCAR for pristine structure can't be found. If more than one element has been removed, script calculates
            e-vac from pristine structure and from previous structure
    5-30-25: Modified get_pair_numbers in case of 0 Li or O. 
    7-9-25: Modified to sort by pair removed then by modification directory number, with sorting dir number by int rather than string to avoid 10 coming before 2. 
    2-26-26: Modified to add option to ignore symmetry. 
    3-2-26: Moved ignore_sym check so it can pull the right mods file. 
"""
#import modules
import os
import sys
from ase.io import read
#define functions
def get_dirs(mod_dir):
    '''Runs through all directories in base directory and returns list of vacancy directories.'''
    vac_dirs=[]
    for root, dirs, files in os.walk(mod_dir):
        if root.endswith('Removed') and 'OUTCAR' in files:
            vac_dirs.append(root)
    vac_dirs.sort()
    return vac_dirs

def read_file(r_dir, file):
    '''Reads given file in directory and returns list of lines'''
    F = open(os.path.join(r_dir,file),'r')
    lines = F.readlines()
    F.close()
    return lines

def get_pair_numbers(vac_dir):
    '''Get number of pairs removed.'''
    pris_dir = os.path.dirname(vac_dir)
    #pristine
    pris_atoms = read(os.path.join(pris_dir,'POSCAR'))
    pf = pris_atoms.symbols.formula
    p_counts = pf.count()
    #vacancy
    vac_atoms = read(os.path.join(vac_dir,'POSCAR'))
    vf = vac_atoms.symbols.formula
    v_counts = vf.count()
    #determine pairs removed
    ele_vacs = {}
    for key in p_counts:
        if key in v_counts:
            if p_counts.get(key) == v_counts.get(key):
                pass
            elif p_counts.get(key) != v_counts.get(key):
                num = float(p_counts.get(key))- float(v_counts.get(key))
                ele_vacs.update({f'{key}':num})
        elif key not in v_counts:
            ele_vacs.update({f'{key}':p_counts.get(key)})
    return ele_vacs

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
        
def get_all_e(mod_dir,mods,base_dir):
    '''Gets total energy of pristine and vacancy surfaces.Returns list of vacancy energies.'''
    #get total energy of pristine surface
    p = os.path.join(mod_dir,'VASP_inputs/')
    e_p = get_e(p)
    
    if e_p == None:
        e_p = get_ep(base_dir,mod_dir)
        
    #gets all vacancy dirs
    vac_dirs = get_dirs(mod_dir)
    #stops the program in no vacancy directories are found
    if not vac_dirs:
        print('No vacancy directories found. Exiting...')
        sys.exit()
     
    mod_name = os.path.basename(mod_dir)
    #gets e_vac for vac dirs
    vac_tot = []
    for vac_dir in vac_dirs:
        vac = get_e(vac_dir)
        ele_vacs = get_pair_numbers(vac_dir)
        e_vac = calc_e_vac(e_p,vac,vac_dir,ele_vacs)
        pair = os.path.basename(vac_dir).split('_')[1]
        element = os.path.basename(vac_dir).split('_')[0]
        dirname = os.path.dirname(vac_dir)
        if dirname.endswith('VASP_inputs'):
            for i, mod in enumerate(mods,1):
                if f'Modification_{i}' == f'{mod_name}':
                    mod = mod.strip('-')
                    vac_tot.append(f'\n{mod_name}/{mod},{element}_{pair},{vac},{e_vac},,')
        elif dirname.endswith('Removed'):
            prev_el = os.path.basename(dirname).split('_')[0]
            prev_pair = os.path.basename(dirname).split('_')[1]
            #get evac relative to previous structure 
            prev = get_e(dirname)
            if prev == None:
                prev = get_ep(base_dir,mod_dir)
            ev_from_prev = calc_e_vac(prev, vac, vac_dir,ele_vacs)
            for i, mod in enumerate(mods,1):
                if f'Modification_{i}' == f'{mod_name}':
                    mod = mod.strip('-')
                    vac_tot.append(f'\n{mod_name}/{mod},{prev_el}_{prev_pair}/{element}_{pair},{vac},{e_vac},{ev_from_prev}')
    
    return vac_tot
        
def calc_e_vac(e_p,vac,vac_dir,ele_vacs):
    '''Calculates vacancy energy'''
    userdir = os.path.expanduser('~/wf-user-files')
    bulk_dict = read_file(userdir, 'BulkE_dict.txt')
    vacancies=[]
    for ele in ele_vacs.keys():
        for i in bulk_dict:
            if i.startswith(ele):
                num = float(ele_vacs.get(ele))
                bulk = float(i.split(':')[1])
                vac_e = num * bulk
                vacancies.append((vac_e,num))
    tot_vac = 0
    tot_num = 0
    for (v,n) in vacancies:
        tot_vac += v
        tot_num += n
    ev = (vac+tot_vac - e_p)/tot_num
    return ev

def sort_data(data):
    '''Sorts data by atom_pair first then by dir number'''
    data_list = data.split(',')
    atom_pair = data_list[1]
    dirname = data_list[0].split('/')
    dir_num = dirname[0].split('_')[1]
    num = int(dir_num)
    return (atom_pair,num)

def process_e_vac(base_dir,settings):
    '''Gets e_vac recursively for all dirs and returns it in one csv '''
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

    #Calculate E_vac in each modification directory in 
    e_vac_tot = []
    for mod_dir in mod_dirs:
        ev = get_all_e(mod_dir,mods,base_dir)
        for e in ev:
            e_vac_tot.append(e)
    
    #check e_vac_tot for values      
    if e_vac_tot == None:
        print('No values found. Exiting...')
        sys.exit()
    #sort data
    e_vac_tot.sort(key=sort_data)
    #write file
    with open(f'{base_dir}/E_vac.csv','w',encoding=None) as f:
        f.write('Modification,Atom Pair,Total E,E_vac (pristine),E_vac (from prev vacancy)')
        f.writelines(e_vac_tot)
        f.close
