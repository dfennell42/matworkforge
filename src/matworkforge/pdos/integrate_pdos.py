"""
Script to integrate PDOS for metal atoms
Author: Dorothea Fennell - dfennell1@bnl.gov
Changelog: 
    9-10-25: New version of integrate_pdos, using scipy.integrate.simpson instead of Blake's method.
    9-11-25: Updated integration bounds for d-block metals to -6 to 0, added section to integrate both s & p orbitals for p-block elements.
    7-22-26: Updated to generalize for v1.0, allow for non spin polarized calculations and use pandas.
"""
#import modules
import os
import numpy as np
import pandas as pd
from pymatgen.core.periodic_table import Element
from pymatgen.io.vasp import Incar
from scipy.integrate import simpson 
#define functions so program can operate recursively
def get_dirs(base_dir):
    '''Runs through all directories in base directory and returns list of pdos directories.'''
    pdos_dirs=[]
    for root, dirs, files in os.walk(base_dir):
        if root.endswith("/PDOS") and "TotalDos.dat" in files:
            pdos_dirs.append(root)
        elif root.endswith("/PDOS") and "TotalDos.dat" not in files:
            print("PDOS data hasn't been parsed yet.")
    return pdos_dirs

def get_files(pdos_dir):
    '''Gets files of all atoms from pdos directory'''
    filelist = [f'{pdos_dir}/{file}' for file in os.listdir(pdos_dir) if file.endswith('_total.dat')]
    filelist.sort()
    return filelist

def chk_spin(pdos_dir):
    '''Checks if PDOS calculations were spin polarized.'''
    incar = Incar.from_file(f'{pdos_dir}/INCAR')
    ispin = incar.get('ISPIN')
    if ispin == 1:
        return False
    elif ispin == 2:
        return True
    
def int_pdos(data,up_idx,lower,block,spin,down_idx=None):
    """Integrates PDOS in specified windows."""
    #slice arrays
    energy = data[:,0]
    up = data[:,up_idx]
    
    #get bottom of integration window
    for x in range(len(energy)):
        if energy[x] >= lower:
            a = x
            break
    #get top of integration window
    for x in range(len(energy)):
        if energy[x] > 0:
            b = x
            break
    
    #split arrays
    els = np.split(energy,[a,b])
    uls = np.split(up,[a,b])
    e_win = els[1]
    u_win = uls[1]
    #integrate
    up_e = simpson(u_win,x=e_win)
    #if p-block element, integrate s orbitals as well
    if block == 'p':
        s_up = data[:,1]
        s_uls = np.split(s_up,[b])
        se_win = np.concat((els[0],els[1]),axis=None)
        su_win = s_uls[0]
        sup_e = simpson(su_win,x=se_win)
        up_e += sup_e
    #if spin polarized
    if spin == True:
        down = data[:,down_idx]
        dls = np.split(down,[a,b])
        d_win = dls[1]
        down_e = simpson(d_win, x=e_win)
        tot_e = up_e + np.abs(down_e)
        if block == 'p':
            s_down = data[:,2]
            s_dls = np.split(s_down,[b])
            sd_win = s_dls[0]
            sdown_e = simpson(sd_win,x=se_win)
            down_e += sdown_e
            tot_e = up_e + np.abs(down_e)
        #calculate spin
        diff = up_e-down_e
        return (tot_e,diff)
    else:
        tota = up_e
        return (tota)

def get_os(ele,e_tot):
    """Gets oxidation state of metal."""
    valence = ele.valence[1]
    if ele.block != 's':
        #Add two to account for the fact that pymatgen only reports outermost orbital
        valence += 2
    oxs = valence - e_tot
    return oxs

def int_d_states(filelist,spin):
    """Integrates the d states of the metal atoms for the total number of electrons and d/p hybridization. """
    #create data lists
    datalist = []
    for file in filelist:
        #determine atom
        filename = os.path.basename(file)
        atom = filename.split('_')[0]
        index = ''
        for char in atom:
            if char.isdigit():
                index +=f'{char}'
        ele = atom.strip('0123456789')
        try:
            ele = Element(ele)
        except:
            pass
        else:
            if ele.block =='s':
                e_lower = -20
                if spin == True:
                    up_idx = 1
                    down_idx = 2
                elif spin == False:
                    up_idx = 1
            elif ele.block == 'p':
                e_lower = -10
                if spin == True:
                    up_idx = 3
                    down_idx = 4
                elif spin == False:
                    up_idx = 2
            elif ele.block == 'd':
                e_lower = -6
                if spin == True:
                    up_idx = 5
                    down_idx = 6
                elif spin == False:
                    up_idx = 3
            elif ele.block == 'f':
                e_lower = -15
                if spin == True:
                    up_idx = 7
                    down_idx = 8
                elif spin == False:
                    up_idx = 4
            #set down_idx to none if not spin pol
            if spin == False:
                down_idx = None
            data = np.genfromtxt(file,skip_header=1)
            
            #integrate from lower bound to 0 to get total # of electrons and net spin
            e_data = int_pdos(data,up_idx,e_lower,ele.block,spin,down_idx)
            
            #get os
            ox = get_os(ele,e_data[0])
            #make series
            e_ser = pd.Series({'Element':ele.symbol,'Atom index':index,'Val. e-':e_data[0],'OS':ox})
            if spin == True:
                e_ser = pd.concat([e_ser,pd.Series({'Spin':e_data[1]})])
            #append series to list
            datalist.append(e_ser)
    #make data frame
    df = pd.DataFrame(data=datalist)
    df.sort_values('Atom index',inplace=True, key=lambda x:x.astype(int))
    return df

def integrate_all_pdos(base_dir):
    '''Integrates pdos recursively through directories.'''
    #get pdos directories
    pdos_dirs = get_dirs(base_dir)

    if not pdos_dirs:
        print('No PDOS directories found. Exiting...')
        return
    
    for pdos_dir in pdos_dirs:
        #get filelists
        filelist = get_files(pdos_dir)
        #check spin
        spin = chk_spin(pdos_dir)
        #integrate
        df = int_d_states(filelist,spin)
        #write df to csv
        df.to_csv(f'{pdos_dir}/integrated-pdos.csv',index=False)



