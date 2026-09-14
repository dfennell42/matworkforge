"""
Modify INCAR for PDOS calculations
Author: Dorothea Fennell
Changelog: 
    4-23-25: Created, comments added
    7-21-26: Updated to use Incar class & pull from pdos_incar_params.toml
    9-14-26: Updated to keep LDAU tags from optimization incar & to actually write the file (got dropped during update to 1.0)
"""
#import modules
import os
import toml
from pymatgen.io.vasp import Incar, Poscar
from matworkforge.inputs.VASP_input import ldau_tags

def get_pdos_params():
    userdir = os.path.expanduser('~/wf-user-files')
    fullpath = os.path.join(userdir, 'pdos_incar_params.toml')
    pdos_params = toml.load(fullpath)
    return pdos_params

#Modify the INCAR file for PDOS calculations
def modify_incar(base_dir,incar_path, pdos_params):
    """Modifies the INCAR file for PDOS calculations"""
    opt_incar = Incar.from_file(incar_path)
    
    #Gets params from settings.toml file
    settings = toml.load(f'{base_dir}/settings.toml')
    set_params = settings['pdos-params']
    if len(set_params) > 0:
        pdos_params.update(set_params)
    
    #create incar file
    pdos_incar = Incar(pdos_params)
    
    #get magmom from opt incar
    magmom = opt_incar['MAGMOM']
    pdos_incar.update({'MAGMOM':magmom})
    
    #checks if INCAR contains specific tags
    tags = ['ISYM','LASPH','LMAXMIX']
    for t in tags:
        if t in opt_incar.keys():
            pdos_incar.update({f'{t}':opt_incar[t]})
    #check for LDAU tags
    for k in opt_incar.keys():
        if k.startswith('LDAU'):
            pdos_incar.update({f'{k}':opt_incar[k]})
    #check to make sure LDAU params updated properly
    if 'LDAUU' in pdos_incar.keys():
        if 'dict' in str(type(pdos_incar['LDAUU'])).lower():
            poscar = Poscar.from_file('POSCAR')
            new_params = ldau_tags(poscar, pdos_params)
            pdos_incar.update(new_params)
    #write file, dummy
    pdos_incar.write_file(incar_path)
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
                