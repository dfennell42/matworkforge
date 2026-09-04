import os
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
    
    #Remove LDAU parameters if LDAU=False because MPRelax set auto includes them
    if 'LDAU' in incar.keys():
        if incar['LDAU'] == False:
            new_incar = incar.copy()
            for key in incar.keys():
                if key.startswith('LDAU'):
                    new_incar.pop(key)
            #add ldau = false back in 
            new_incar.update({'LDAU':False})
            incar = new_incar
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
    



