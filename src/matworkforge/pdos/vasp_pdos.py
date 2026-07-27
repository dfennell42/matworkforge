'''
Create pdos .dat files for each atom recursively
Author: Dorothea Fennell
Modified from Blake's vasp_pdos.py script
Changelog: 
    4-30-25: Created, comments added. Broke original script up into functions so it can be applied recursively. 
    8-6-25: Modified fermi_energy to split accordingly
    7-22-26: Rewrote to accomodate for non-spin polarized calculations, and to use Dataframes instead
'''
#import modules
import os
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.core import Orbital,OrbitalType
import pandas as pd

#define functions

def tdos(pdos_dir,vpr):
    '''
    Constructs the Total Density of States and saves it to TotalDos.dat.
    '''
    tdos = vpr.tdos
    idos = vpr.idos
    en = tdos.energies
    #make dataframes
    energies = pd.DataFrame({'energies':en})
    tdf = pd.DataFrame(data=tdos.densities)
    idf = pd.DataFrame(data=idos.densities)
    for k in tdf.keys():
        tdf.rename(columns={k:f'DOS({k.name})'},inplace=True)
    for l in idf.keys():
        idf.rename(columns={l:f'integrated DOS({l.name})'},inplace=True)
    tdos_df = pd.concat([energies,tdf,idf],axis=1)
    tdos_df.to_csv(f'{pdos_dir}/TotalDos.dat',sep=' ',index=False)

def pdos(pdos_dir,vpr):
    '''Creates .dat and _total.dat files for each atom. _total.dat files have the orbitals summed (all p orbitals together, etc.), and the energy is fermi shifted.'''
    #complete dos
    dos = vpr.complete_dos
    energies = pd.DataFrame(data={'energies':dos.energies})
    #list sites to get file names
    sites = dos.structure.sites
    # .dat file first
    pd_list = vpr.pdos
    for idx,p in enumerate(pd_list):
        p = dict(p)
        df_list = [energies]
        #loop over orbitals
        for i in range(len(p)):
            df = pd.DataFrame(data=p[Orbital(i)])
            for label in df.keys():
                df.rename(columns={label:f'{Orbital(i).name}({label.name})'},inplace=True)
            df_list.append(df)
        #concat
        pdos_df = pd.concat(df_list,axis=1)
        #determine filename
        site = sites[idx]
        filename = f'{site.label}{idx}'
        #write file
        pdos_df.to_csv(f'{pdos_dir}/{filename}.dat',sep=' ',index=False)
        
        #write _total.dat file
        site_dos = dos.get_site_spd_dos(site)
        #get fermi-shifted energy
        fermi = vpr.efermi
        en_shift = energies.sub(fermi)
        dos_list = [en_shift]
        for l in range(len(site_dos)):
            data = site_dos[OrbitalType(l)].densities
            df = pd.DataFrame(data=data)
            for label in df.keys():
                df.rename(columns={label:f'{OrbitalType(l).name}({label.name})'},inplace=True)
            dos_list.append(df)
        #concat
        pdos_tot = pd.concat(dos_list,axis=1)
        #write file
        pdos_tot.to_csv(f'{pdos_dir}/{filename}_total.dat',sep=' ',index=False)
        

def process_pdos_dirs(base_dir):
    """Finds all PDOS directories and processes POSCAR & DOSCAR into a file for each individual atom."""
    pdos_dirs=[]
    for root, dirs, files in os.walk(base_dir):
        if root.endswith("/PDOS") and "DOSCAR" in files:
            pdos_dirs.append(root)
        elif root.endswith("/PDOS") and "DOSCAR" not in files:
            print("PDOS calculations haven't been run yet.")
            
    if not pdos_dirs:
        print('No PDOS directories found. Exiting...')
        return
    
    for pdos_dir in pdos_dirs:
        print(f'Processing {pdos_dir}')
        #get vasprun
        vpr = Vasprun(f'{pdos_dir}/vasprun.xml')

        #construct tdos
        tdos(pdos_dir,vpr)

        #construct pdos for each atom
        pdos(pdos_dir, vpr)
        print(f'PDOS files created for {pdos_dir}')
        
