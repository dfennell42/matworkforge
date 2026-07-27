"""
Extract electronic and structural decriptors for ML
Author: Dorothea Fennell
Changelog:
    7-23-26: Rewrote for v1.0
"""
#import modules
import os
import warnings
import pandas as pd
from pymatgen.io.vasp import Vasprun, Outcar
from matworkforge.utils.settings import read_settings
from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Structure
from pymatgen.electronic_structure.core import OrbitalType
import numpy as np
#define functions
def read_file(r_dir, file):
    '''Reads given file in directory and returns list of lines'''
    F = open(os.path.join(r_dir,file),'r')
    lines = F.readlines()
    F.close
    return lines

def sort_mods(data):
    num = data.split('_')[1]
    return int(num)

def get_dirs(base_dir):
    '''Gets list of PDOS directories.'''
    pdos_dirs=[]
    print("\nWhich structures would you like to extract descriptors for?")
    print('1: All')
    print("2: Pristine")
    print("3: Vacancy")
    print("4: Adsorption")
    struc = input("Enter the number of your choice: ")
    if struc == '1':
        base = '/PDOS'
    elif struc == '2':
        base = 'VASP_inputs/PDOS'
    elif struc == '3':
        base = '_Removed/PDOS'
    elif struc == '4':
        base = '_Added/PDOS'
    else:
        base = '/PDOS'
    
    for root, dirs, files in os.walk(base_dir):
        if root.endswith(base) and 'integrated-pdos.csv' in files:
            pdos_dirs.append(root)
        elif root.endswith(base) and "integrated-pdos.csv" not in files:
            print("PDOS calculations haven't been integrated yet.")
    def sort_dirs(data):
        path_list = data.split('/')
        for p in path_list:
            if p.startswith('Modification_'):
                num = p.split('_')[1]
                return int(num)
    pdos_dirs.sort(key=sort_dirs)
    return pdos_dirs,base

def band_gap(vasprun):
    '''Gets the band gap for the vasprun.xml file.'''
    # Get band structure and band gap
    band_struc = vasprun.get_band_structure()
    band_gap = band_struc.get_band_gap()
    fermi = band_struc.efermi
    cbm = band_struc.get_cbm()['energy']
    vbm = band_struc.get_vbm()['energy']
    return band_gap['energy'],fermi,cbm,vbm

def get_form_en(vasprun):
    '''Computes energy of formation.'''
    # Reference energies in eV/atom
    userdir = os.path.expanduser('~/wf-user-files')
    bulk_dict = read_file(userdir, 'BulkE_dict.txt')
    #create dict
    ref_energies={}
    for l in bulk_dict:
        #ignore comment line
        if l.startswith('#'):
            pass
        else:
            ls = l.split(':')
            ref_energies.update({ls[0].strip():float(ls[1].strip())})
    
    #read vasprun.xml, get final structure, energy & composition
    struc = vasprun.final_structure
    tot_en = vasprun.final_energy
    comp = struc.composition
    
    #get ref energy
    ref_energy = sum([amt * ref_energies[el.symbol] for el, amt in comp.items()])
    #get form energy
    form_en = tot_en - ref_energy
    return form_en

def get_species_desc(vasprun):
    '''Get descriptors for each species in structure.'''
    struc = vasprun.structures[-1]
    species = list(struc.chemical_system_set)
    species.sort()
    dos = vasprun.complete_dos
    spec_data = {}
    #loop over species
    for spec in species:
        ele = Element(spec)
        z = ele.Z
        chi = ele.X
        ion_e = ele.ionization_energy
        #get element band center/width
        ele_bc = dos.get_band_center(band=OrbitalType(ele.valence[0]),elements=[ele])
        ele_bw = dos.get_band_width(band=OrbitalType(ele.valence[0]),elements=[ele])
        #add to dict
        spec_data.update({f'{spec}_Z':z,f'{spec}_chi':chi,f'{spec}_ion_e':ion_e,f'{spec}_band_center':ele_bc,f'{spec}_band_width':ele_bw})
    #convert dict to series
    spec_ser = pd.Series(spec_data)
    return spec_ser

def chk_idxs(base_dir,pdos_dir,idxs):
    '''Adjusts idxs based on vacancies.'''
    #get path for pris dir
    parts = pdos_dir.split('/')
    new_path = ''
    for p in parts:
        new_path += f'{p}/'
        if p == 'VASP_inputs':
            break
    #get initial structure
    sites = Structure.from_file(f'{pdos_dir}/POSCAR').sites
    #get pris structure
    pris_sites = Structure.from_file(f'{new_path}CONTCAR').sites
    #check for vacancies
    vacs = [i for i,x in enumerate(pris_sites) if x not in sites]
    #if there are vacs, check if the indices are before or after the selected sites
    if len(vacs) >0:
        chk = [any(x>=v for x in idxs) for v in vacs]
        if any(chk) == True:
            #check if sites have been removed
            mis = []
            for x in idxs:
                if any(x==v for v in vacs):
                    print_path = pdos_dir.replace(f'{base_dir}','.')
                    print(f'Atom {x} has been removed from structure in {print_path} and will be skipped.')
                    mis.append(x) 
            if len(idxs) == len(mis):
                #if all sites are missing
                return None
            else:
                new_idxs = [(x-chk.count(True)) if x > np.array(vacs).min() else x for x in idxs if x not in mis]
        else:
            new_idxs = idxs            
    else:
         new_idxs = idxs
    return new_idxs

def get_site_desc(base_dir,pdos_dir,vasprun,idxs):
    '''get site descriptors'''
    struc = vasprun.structures[-1]
    sites = struc.sites
    dos = vasprun.complete_dos
    site_data = {}
    #check indices
    new_idxs = chk_idxs(base_dir, pdos_dir, idxs)
    if new_idxs == None:
        return None
    #get integrated pdos data
    pdos_df = pd.read_csv(f'{pdos_dir}/integrated-pdos.csv')
    #loop over sites
    for i in new_idxs:
        site = sites[i]
        spec = site.label
        ele = site.specie
        #get pdos data
        for row_idx,row in pdos_df.iterrows():
            if row['Atom index'] == i:
                e_tot = row['Val. e-']
                ox = row['OS']
                if 'Spin' in pdos_df.columns():
                    spin = row['Spin']
                    #add to dict
                    site_data.update({f'{i}_species':spec,f'{i}_val_e':e_tot,f'{i}_OS':ox,f'{i}_spin':spin})
                else:
                    site_data.update({f'{i}_species':spec,f'{i}_val_e':e_tot,f'{i}_OS':ox})
        #get bc & bw
        site_bc = dos.get_band_center(band=OrbitalType(ele.valence[0]),sites=[site])
        site_bw = dos.get_band_width(band=OrbitalType(ele.valence[0]),sites=[site])
        #add to dict
        site_data.update({f'{i}_band_center':site_bc,f'{i}_band_width':site_bw})
    #convert to Series
    site_ser = pd.Series(site_data)
    return site_ser

def extract_desc(base_dir):
    '''Extract descriptors.'''
    #get directories
    pdos_dirs,base = get_dirs(base_dir)
    
    if not pdos_dirs:
        print('No PDOS directories found. Exiting...')
        return
    
    #ask if they would like to extract site descriptors
    print('Would you like to extract descriptors for specific sites?')
    print('If yes, input comma-separated list of atom indices. Indices should come from the pristine structure.')
    print('If no, input either "no" or leave input prompt blank.')
    idx_choice = input('Enter indices:')
    
    if len(idx_choice) == 0:
        site_desc = False
    elif idx_choice.lower().startswith('n'):
        site_desc = False
    else:
        idls = idx_choice.strip().split(',')
        idxs = [int(x) for x in idls]
        site_desc = True
    
    #get modifications from Mods file
    #check for mod file name in settings
    settings = read_settings()
    mod_file = settings['mods-file']
    if os.path.exists(os.path.join(base_dir,mod_file)):
        mods = read_file(base_dir, mod_file)
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
    
    mod_data_list = []
    for pdos_dir in pdos_dirs:
        for i, mod in enumerate(mods,1):
            if f'Modification_{i}/' in pdos_dir:
                opt_dir = os.path.dirname(pdos_dir)
                #get vaspruns
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    opt_vpr = Vasprun(os.path.join(opt_dir,'vasprun.xml'))
                    pdos_vpr = Vasprun(os.path.join(pdos_dir,'vasprun.xml'))
                    
                #----Material level descriptors-----#
                #get formation energy
                form_en = get_form_en(opt_vpr)
                #get band gap & fermi energy
                bg_e,fermi,cbm,vbm = band_gap(pdos_vpr)
                #check cbm
                if cbm == None:
                    dos = pdos_vpr.complete_dos
                    fermi = dos.efermi
                    cbm,vbm = dos.get_cbm_vbm()
                #get nelect
                nelect = Outcar(f'{pdos_dir}/OUTCAR').nelect
                #create pandas series with modification and single value returns
                e_ser = pd.Series(data={'Modification':mod,'E_form':form_en,'E_fermi':fermi,'E_bg':bg_e,'VBM':vbm,'CBM':cbm,'nelect':nelect})
               
                #----Element level descriptors-----#
                #get species descriptors
                spec_ser = get_species_desc(pdos_vpr)
                
                #----Site level descriptors----#
                if site_desc == True:
                    site_ser = get_site_desc(base_dir, pdos_dir, pdos_vpr, idxs)
                    if type(site_ser) != None:
                        mod_ser = pd.concat([e_ser,spec_ser,site_ser])
                    else:
                        mod_ser = pd.concat([e_ser,spec_ser])
                else:
                    mod_ser = pd.concat([e_ser,spec_ser])
                mod_data_list.append(mod_ser)
    
    #create data frame from mod_data_list
    mod_data = pd.DataFrame(data=mod_data_list)
    #reindex dataframe to use modification
    
    if "_Removed" in base:
        prefix = 'vac'
    elif 'Added' in base:
        prefix = 'ads'
    elif "inputs" in base:
        prefix = 'pris'
    else:
        prefix = 'all'
    #print data to csv
    mod_data.to_csv(os.path.join(base_dir,f'{prefix}-descriptors.csv'),index=False)
    print('Descriptors extracted and descriptors.csv created.')
    
