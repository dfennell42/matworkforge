import os
import shutil
import toml
# Define element-specific magnetic moments

def read_poscar(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Extract element names and counts
    elements = lines[5].split()
    num_atoms = list(map(int, lines[6].split()))

    # Map each atom index to its element
    atom_to_element = []
    for elem, count in zip(elements, num_atoms):
        atom_to_element.extend([elem] * count)

    return elements, num_atoms, atom_to_element

def read_spin_pairs(filename, ignore_sym = False):
    spin_pairs = {}
    with open(filename, 'r') as f:
        for line in f:
            if not line.strip().startswith('#') and len(line) >1:
                parts = line.strip().split(',')
                if ignore_sym == False:
                    atom1, atom2 = int(parts[0]), int(parts[1])
                    spin = parts[2].strip()
                    if '#' in spin:
                        spin_parts = spin.split('#')
                        spin = spin_parts[0].strip()
                    spin_pairs[(atom1, atom2)] = spin
                elif ignore_sym == True:
                    idx = int(parts[0])
                    spin = parts[1].strip()
                    if '#' in spin:
                        spin_parts = spin.split('#')
                        spin = spin_parts[0].strip()
                    spin_pairs[idx] = spin
    return spin_pairs

def assign_magnetic_moments(atom_to_element, spin_pairs, ignore_sym = False):
    """
    Assign magnetic moments to atoms based on spin pairs and element type.
    """
    userdir = os.path.expanduser('~/wf-user-files')
    with open(os.path.join(userdir,'MagMom_dict.txt'),'r') as mm:
        mm_lines = mm.readlines()
        
    magnetic_moments = {}
    for x in mm_lines:
        x_split = x.split(':')
        y = x_split[1].strip('\n')
        magnetic_moments.update({f'{x_split[0]}':float(f'{y}')})
        
    magmom = [magnetic_moments.get(element, 0.6) for element in atom_to_element]  # Default all moments
    if ignore_sym == False:
        for (atom1, atom2), spin in spin_pairs.items():
            moment1 = magnetic_moments.get(atom_to_element[atom1], 0.6)  # Atom1 moment
            moment2 = magnetic_moments.get(atom_to_element[atom2], 0.6)  # Atom2 moment
    
            if spin == "up":
                magmom[atom1] = moment1
                magmom[atom2] = moment2
            elif spin == "down":
                magmom[atom1] = -moment1
                magmom[atom2] = -moment2
    elif ignore_sym == True:
        for idx, spin in spin_pairs.items():
            moment = magnetic_moments.get(atom_to_element[idx],0.6)
            if spin == 'up':
                magmom[idx] = moment
            elif spin == 'down':
                magmom[idx] = -moment
    
    return magmom

def generate_magmom_line(elements, num_atoms, magmom):
    """
    Create the `MAGMOM` line preserving the element order in POSCAR.
    """
    magmom_line = []
    index = 0

    for elem, count in zip(elements, num_atoms):
        element_moments = magmom[index:index + count]

        # Group consecutive identical moments
        group_start = 0
        while group_start < len(element_moments):
            group_moment = element_moments[group_start]
            group_count = 0

            for i in range(group_start, len(element_moments)):
                if element_moments[i] == group_moment:
                    group_count += 1
                else:
                    break

            magmom_line.append(f"{group_count}*{group_moment:.1f}")
            group_start += group_count

        index += count

    return " ".join(magmom_line)

def find_files_recursive(pattern, mod):
    """
    Recursively find files matching the given pattern.
    """
    matched_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if mod != None:
                if root.endswith(mod) and pattern in file:
                    matched_files.append(os.path.join(root, file))
            elif mod == None:
                if pattern in file:
                    matched_files.append(os.path.join(root, file))
    return matched_files

def get_incar_params():
    '''Gets custom incar parameters from wf-user-files directory'''
    userdir = os.path.expanduser('~/wf-user-files')
    param_file = os.path.join(userdir,'opt_incar_params.toml')
    custom_incar_params = toml.load(param_file)
    return custom_incar_params

def process_poscar_files(settings,mod = None):
    # Find all POSCAR files with the pattern POSCAR_modified_*.vasp
    poscar_files = find_files_recursive("POSCAR_",mod)
    poscar_files = [file for file in poscar_files if file.endswith(".vasp")]
    
    if not poscar_files:
        print("No POSCAR_*.vasp files found!")
        return

    print(f"Found {len(poscar_files)} files.")
    
    #check INCAR params to see if running spin polarized
    custom_incar_params = get_incar_params()
    set_params = settings['incar-params']
    if len(set_params) >0:
        custom_incar_params.update(set_params)
    
    if 'ISPIN' in custom_incar_params.keys():
        if custom_incar_params.get('ISPIN') == 1:
            print('Calculations are not spin polarized. MAGMOM not required.')
            return
        
    ignore_sym = settings['ignore-symmetry']
    spin_file = settings['spin-file']
    
    #copy SpinPairs file to dir
    userdir = os.path.expanduser('~/wf-user-files')
    fullpath = os.path.join(userdir, spin_file)
    shutil.copy(fullpath, os.getcwd())
    
    if not os.path.exists(spin_file):
        print(f"{spin_file} not found in the directory.")
        return

    for poscar_file in poscar_files:
        #print(f"Processing {poscar_file}...")

        # Read POSCAR and SpinPairs
        elements, num_atoms, atom_to_element = read_poscar(poscar_file)
        spin_pairs = read_spin_pairs(spin_file, ignore_sym)

        # Assign magnetic moments
        magmom = assign_magnetic_moments(atom_to_element, spin_pairs, ignore_sym)

        # Generate MAGMOM line
        magmom_line = generate_magmom_line(elements, num_atoms, magmom)

        # Write output MAGMOM line to file
        output_file = f"{poscar_file.replace('.vasp', '_MAGMOM.txt')}"
        with open(output_file, "w") as f:
            f.write(f"MAGMOM = {magmom_line}\n")
        
        print(f"Generated MAGMOM line saved to {output_file}.")
