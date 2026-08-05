from ase.io import read, write
import os
import copy
import shutil
from .list_sites import read_pairs

# Replace Co according to ModsCo.txt
def modify_pairs(atoms,atom_pairs,mods_file,ignore_sym=False):
    def read_modifications(filename):
        modifications = []
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().replace(" ", "").split(',')
                pair_indices = list(map(int, parts[:-len(parts) // 2]))
                new_elements = parts[-len(parts) // 2:]
                modifications.append((pair_indices, new_elements))
        return modifications

    modifications = read_modifications(mods_file)

    for mod_index, (indices, new_elements) in enumerate(modifications):
        modified_atoms = copy.deepcopy(atoms)
        #modify based on symmetry
        if ignore_sym == False:
            for i, pair_index in enumerate(indices):
                if pair_index < len(atom_pairs):
                    index1, index2 = atom_pairs[str(pair_index)]
                    modified_atoms[int(index1)].symbol = new_elements[i]
                    modified_atoms[int(index2)].symbol = new_elements[i]
        elif ignore_sym == True:
            for i, idx in enumerate(indices):
                modified_atoms[idx].symbol = new_elements[i]
        
        # Make new directory for each new structure
        directory_name = f"Modification_{mod_index + 1}"
        os.makedirs(directory_name, exist_ok=True)
        
        output_filename = os.path.join(directory_name, f"POSCAR_modified_{mod_index + 1}.vasp")
        write(output_filename, modified_atoms, format="vasp")
        print(f"Modified POSCAR saved in directory {directory_name} as {output_filename}.")

def modify_structure(base_dir,settings,ignore_sym):
    '''Modifies structures based of user input. '''
    userdir = os.path.expanduser('~/wf-user-files')
    poscar = settings['poscar-file']
    fullpath = os.path.join(userdir, poscar)
    shutil.copy(fullpath, os.path.join(base_dir,'POSCAR'))
    # Read POSCAR 
    atoms = read(os.path.join(base_dir,'POSCAR'))
    #print('atoms read')
    sym = atoms.symbols
    elements = list(sym.species())
    elements.sort()
    #modify based on input
    print('Which element would you like to modify?')
    for i,element in enumerate(elements):
        print(f'{i+1}:{element}')
    choice = input("Enter the number of your choice: ")
    #read settings
    mods_file = settings['mods-file']
    #modify
    for i,element in enumerate(elements,1):
        if float(choice) == i:
            pairs = read_pairs(base_dir, element,settings)
            modify_pairs(atoms, pairs,mods_file,ignore_sym)
            
#if __name__ == "__main__":
   # base_dir = os.getcwd()
   # modify(base_dir)
