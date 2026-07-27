"""
Modify INCAR for PDOS calculations
Author: Dorothea Fennell
Changelog: 
    4-23-25: Created, comments added
    7-21-26: Updated to use Incar class & pull from pdos_incar_params.toml
"""
#import modules
import os
import toml
from pymatgen.io.vasp import Incar

def get_pdos_params():
    userdir = os.path.expanduser('~/wf-user-files')
    fullpath = os.path.join(userdir, 'pdos_incar_params.toml')
    pdos_params = toml.load(fullpath)
    return pdos_params

#Modify the INCAR file for PDOS calculations
def modify_incar(base_dir,incar_path, pdos_params):
    """Modifies the INCAR file for PDOS calculations"""
    with open(incar_path, "r") as incar:
        incar_lines = incar.readlines()
    
    #Gets params from settings.toml file
    settings = toml.load(f'{base_dir}/settings.toml')
    set_params = settings['pdos-params']
    if len(set_params) > 0:
        pdos_params.update(set_params)
    
    #create incar file
    incar = Incar(pdos_params)
    
    #Saves magmom line from current INCAR file
    for line in incar_lines:
        if line.strip().startswith("MAGMOM"):
            magmom_line = line.strip(' \n')
    
    #convert magmom line
    mm = magmom_line.split('=')
    #update incar
    incar.update({'MAGMOM':str(mm[1].strip())})
    
    #checks if INCAR contains ISYM
    for line in incar_lines:
        if line.strip().startswith('ISYM'):
            ls = line.strip(' \n').split('=')
            incar.update({'ISYM':ls[1].strip()})
    
    print(f"Updated INCAR in {incar_path}")
    #print(magmom_line)

#Modify all INCAR files recursively
def process_pdos_dirs(base_directory):
    """Finds all PDOS directories and edits their INCAR files."""
    for root, dirs, files in os.walk(base_directory):
        if "INCAR" in files:
            if root.endswith("PDOS"):
                pdos_params = get_pdos_params()
                modify_incar(base_directory,os.path.join(root, "INCAR"), pdos_params)
                