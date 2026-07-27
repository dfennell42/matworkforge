"""
Script to integrate PDOS for metal atoms
Author: Dorothea Fennell - dfennell1@bnl.gov
Changelog: 
    5-5-25: Created, comments added.
    5-9-25: Changed integration section based on Blake's script
    7-8-25: Changed script to pull selected data for M1, M2, and M3, adjusting indexes based on number of Li. Also added function to sort data 
            by index.
    7-23-25: Changed script to automatically add aluminum to csv of metal data with tot_e, spin, and hd/p = 0 and os = 3.
    8-6-25: Changed script to integrate Al & O p states with Al from -2 to 0 and O from -8 to 0.
NOTE: While this script uses 'integrate' to describe what's occuring, this is not technically an integration. The script takes
      the sum of the pdos from the lower limit of integration to positive infinity, divides each value in the integration window by this
      sum, then multiplies it by 5 to account for all 5 d orbitals. This is due to the need to normalize the occupied and unoccupied states
      (ask Blake for more details).
"""
#import modules
import os
import numpy as np
from pymatgen.core.periodic_table import Element
#define functions so program can operate recursively
def get_dirs(base_dir):
    '''Runs through all directories in base directory and returns list of pdos directories.'''
    pdos_dirs=[]
    for root, dirs, files in os.walk(base_dir):
        if root.endswith("PDOS") and "TotalDos.dat" in files:
            pdos_dirs.append(root)
        elif root.endswith("PDOS") and "TotalDos.dat" not in files:
            print("PDOS data hasn't been parsed yet.")
    return pdos_dirs

def get_files(pdos_dir):
    '''Gets files of all atoms from pdos directory'''
    m_filelist = []
    o_filelist = []
    li_filelist = []
    for file in os.listdir(pdos_dir):
        if file.endswith('_total.dat'):
            filepath = os.path.join(pdos_dir,file)
            if file.startswith('O'):
                o_filelist.append(filepath)
            elif file.startswith('Al'):
                m_filelist.append(filepath)
            elif file.startswith('Li'):
                li_filelist.append(filepath)
            else:
                m_filelist.append(filepath)
    m_filelist.sort()
    o_filelist.sort()
    li_filelist.sort()

    return m_filelist, o_filelist,li_filelist

def int_pdos(data,up_idx,down_idx,lower,upper, orbs,diff=True):
    """Integrates PDOS in specified windows."""
    #slice arrays
    energy = data[:,0]
    up = data[:,up_idx]
    down = data[:,down_idx]
    #set up variables for next section
    up_e = 0.0
    down_e = 0.0
    tot_e = 0.0
    up_sum = 0.0
    down_sum = 0.0
    #integrate
    for x in range(len(energy)):
        if energy[x] > lower:
            up_sum += up[x]
            down_sum += down[x]
            
    for x in range(len(energy)):
        if energy[x] > lower and energy[x] < upper:
            up_e += up[x]/up_sum * orbs
            down_e += down[x]/down_sum * orbs
            tot_e += up[x]/up_sum * orbs + down[x]/down_sum * orbs
    if diff == True:
        diff = np.abs(up_e-down_e)
        return tot_e, diff
    else:
        tota = tot_e
        return tota
    
def get_os(ele,e_tot):
    """Gets oxidation state of metal."""
    valence = ele.valence[1]
    if ele.block != 's':
        valence += 2
    oxs = valence - e_tot
    return oxs

def int_d_states(filelist):
    """Integrates the d states of the metal atoms for the total number of electrons and d/p hybridization. """
    #create data lists
    m_data = []
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
                orbs = 1
                up_idx = 1
                down_idx = 2
            elif ele.block == 'p':
                orbs = 3
                up_idx = 3
                down_idx = 4
                e_lower = -8
                if ele.symbol == 'Al':
                    e_lower = -2
            elif ele.block == 'd':
                orbs = 5
                up_idx = 5
                down_idx = 6
                e_lower = -2
            elif ele.block == 'f':
                orbs = 7
                up_idx = 7
                down_idx = 8
            #the atom_total.dat files have to be unpacked because they're made with np.savetext
            data = np.genfromtxt(file,skip_header=1,unpack=True)
            
            #integrate from -2 to 0 to get total # of electrons and net spin
            e_tot, spin = int_pdos(data,up_idx,down_idx,e_lower,0,orbs)
            
            #integrate from -8 to -2 to get d/p hybridization
            if ele.block == 'd':
                tot_win = int_pdos(data,up_idx,down_idx,-8,0,orbs,diff=False)
                hdp = tot_win - e_tot
            else:
                hdp = 0
            #get os
            ox = get_os(ele,e_tot)
            #append data to list
            m_data.append(f'\n{ele},{index},{e_tot},{ox},{spin},{hdp},{ele.block}')
    return m_data

def print_data(pdos_dir,data,fname,header):
    '''Prints data to csv file. '''
    with open(f'{pdos_dir}/{fname}.csv','w',encoding=None) as f:
        f.write(header)
        f.writelines(data)
        f.close
    print(f'{pdos_dir} csv created.')

def integrate_all_pdos(base_dir):
    '''Integrates pdos recursively through directories.'''
    #get pdos directories
    pdos_dirs = get_dirs(base_dir)

    if not pdos_dirs:
        print('No PDOS directories found. Exiting...')
        return
    
    selected_data = []
    for pdos_dir in pdos_dirs:
        #get filelists
        m_filelist, o_filelist, li_filelist = get_files(pdos_dir)
        #integrate d states
        m_data = int_d_states(m_filelist)
        #determine index numbers for m1, m2 & m3
        li_rem = 18 - len(li_filelist)
        m1 = str(21 - li_rem)
        m2 = str(23 - li_rem)
        m3 = str(25 - li_rem)
        o1 = str(41 - li_rem)
        o2 = str(43 - li_rem)
        o3 = str(45 - li_rem)
        #get file for oxygen
        o_files = []
        for file in o_filelist:
            filename = os.path.basename(file)
            f = filename.split('_')[0]
            o_num = f.strip('O')
            if o_num in [o1,o2,o3]:
                o_files.append(file)
        o_data = int_d_states(o_files)
        #get selected data
        m_data.extend(o_data)
        for x in m_data:
            x = x.strip('\n')
            atom_index = x.split(',')[1]
            if atom_index in [m1,m2,m3,o1,o2,o3]:
                pdir = pdos_dir.split('/')
                for p in pdir:
                    if p.startswith('Modification_'):
                        mod_name = p
                selected_data.append(f'\n{mod_name},{x}')
        #print data to csv
        mod_header = 'Element,Atom index,e_tot,OS,spin,H d/p,Orbital'
        m_data.sort(key=sort_by_index)
        print_data(pdos_dir,m_data,'integrated-pdos',mod_header)
    selected_header = 'Modification dir,Element,Atom index,e_tot,OS,spin,H d/p,Orbital'
    selected_data.sort(key=sort_by_index)
    print_data(base_dir,selected_data,'selected-int-pdos',selected_header)

def sort_by_index(data):
    '''For sorting the lists of data by the atom index rather than by element'''
    data_list = data.split(',')
    if len(data_list) == 7:
        index = int(data_list[1])
        return index
    elif len(data_list) == 8:
        index = int(data_list[2])
        dirname = data_list[0].strip('\n')
        dir_num = dirname.split('_')[1]
        num = int(dir_num)
        return (index, num)
