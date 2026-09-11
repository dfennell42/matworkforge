import os
import sys
import toml
import shutil
from pymatgen.io.vasp import Kpoints, Poscar, Incar
from pymatgen.io.vasp.sets import MPRelaxSet
from pymatgen.core.structure import Structure

# Function to generate VASP inputs from a POSCAR file
def generate_vasp_inputs(vasp_file, custom_incar_params,kpoints):
    # Read the structure from the VASP POSCAR file
    structure = Structure.from_file(vasp_file)

    # Prepare the necessary VASP input files
    poscar = Poscar(structure)
    incar = Incar.from_dict(MPRelaxSet(structure).incar)
    #create kpoints file
    if kpoints['style'].lower() == 'gamma':
        kpt_file = Kpoints.gamma_automatic(kpoints['kpoint-grid'],kpoints['shift'])
    elif kpoints['style'].lower() == 'monkhorst' or kpoints['style'].lower() == 'monkhorst-pack':
        kpt_file = Kpoints.monkhorst_automatic(kpoints['kpoint-grid'],kpoints['shift'])  # could specify a different kgrid

    # Apply custom INCAR parameters if provided
    if custom_incar_params:
        incar.update(custom_incar_params)
    
    #Update LDAU params if necessary
    if 'LDAU' in incar.keys():
        if incar['LDAU'] == False:
            new_incar = incar.copy()
            for key in incar.keys():
                if key.startswith('LDAU'):
                    new_incar.pop(key)
            #add ldau = false back in 
            new_incar.update({'LDAU':False})
            incar = new_incar
        elif incar['LDAU'] == True:
            config = MPRelaxSet(structure).config_dict
            #have to update LDAUU, LDAUJ, & LDAUL because the way pymatgen writes them
            new_params = ldau_tags(poscar, config, custom_incar_params)
            incar.update(new_params)
    else:
        pass

    # Define output directory
    input_dir = os.path.join(os.path.dirname(vasp_file), "VASP_inputs")
    os.makedirs(input_dir, exist_ok=True)

    # Write the files
    poscar.write_file(os.path.join(input_dir, "POSCAR"))
    incar.write_file(os.path.join(input_dir, "INCAR"))
    kpt_file.write_file(os.path.join(input_dir, "KPOINTS"))

    # Copy the POTCAR file from the same directory as the POSCAR file to the new VASP_inputs directory
    potcar_file = os.path.join(os.path.dirname(vasp_file), "POTCAR")
    if os.path.exists(potcar_file):
        shutil.copy(potcar_file, os.path.join(input_dir, "POTCAR"))
        print(f"POTCAR copied from {os.path.dirname(vasp_file)} to {input_dir}")
    else:
        print(f"No POTCAR file found in {os.path.dirname(vasp_file)}")

    print(f"VASP inputs generated in: {input_dir}")

def get_incar_params():
    '''Gets custom incar parameters from wf-user-files directory'''
    userdir = os.path.expanduser('~/wf-user-files')
    param_file = os.path.join(userdir,'opt_incar_params.toml')
    custom_incar_params = toml.load(param_file)
    return custom_incar_params

def ldau_tags(poscar,config,custom_incar_params):
    '''gets proper ldau tags for incar'''
    #get incar config
    incar_config = config['INCAR']
    #set tags
    tags = ['LDAUU','LDAUJ','LDAUL']
    #symbols
    sym = poscar.site_symbols
    #loop over tags
    new_params = {}
    for tag in tags:
        #get tag from incar params or config
        if tag in custom_incar_params.keys():
            t = custom_incar_params[tag]
            if 'dict' in str(type(t)).lower():
                t = dict(t)
            else:
                pass
        else:
            t = dict(incar_config[tag]['O'])
        #write str for tag
        tstr = ''
        if type(t) == dict:
            for s in sym:
                i = t.get(s,0)
                tstr += f'{i} '
        elif type(t) == list:
            for l in t:
                tstr += f'{l} '
        elif type(t) == str:
            #strip trailing whitespace or commas
            t = t.strip(' ,')
            #split if comma-separated
            if t.find(',') > -1:
                t = t.split(',')
                for l in t:
                    tstr += f'{l} '
            else:
                tstr = t
        #check str length against # of symbols
        ls = tstr.strip().split(' ')
        if len(ls) != len(sym):
            print(f'Length of provided {tag} does not match number of symbols in POSCAR (line 6). Please adjust tag by either adjusting length or providing a dictionary of values. ')
            sys.exit()
        #update params with new tag
        new_params.update({f'{tag}':tstr})
    #return new params
    return new_params

# Function to search for .vasp files and generate VASP inputs
def generate_vasp_inputs_in_dir(root_dir,settings):
    set_params = settings['incar-params']
    custom_incar_params = get_incar_params()
    kpoints = settings['kpoints']
    if len(set_params) > 0:
        custom_incar_params.update(set_params)
    #check if ignore sym = true
    ignore_sym = settings['ignore-symmetry']
    if ignore_sym == True:
        custom_incar_params.update({'ISYM':-1})
    # Walk through all subdirectories of the root directory
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".vasp"):  # Check if file ends with .vasp
                vasp_file = os.path.join(subdir, file)
                generate_vasp_inputs(vasp_file, custom_incar_params,kpoints)
    



