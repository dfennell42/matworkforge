from ase.io import read, write
import os
import copy
import shutil


# Save pairs to text files
def save_pairs_to_file(pairs, filename):
    with open(filename, 'w') as file:
        for pair in pairs:
            file.write(f"{pair[0]},{pair[1]}\n")

# Replace Co according to ModsCo.txt
def modify_co_pairs(atoms,co_pairs):
    def read_modifications(filename):
        modifications = []
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().replace(" ", "").split(',')
                pair_indices = list(map(int, parts[:-len(parts) // 2]))
                new_elements = parts[-len(parts) // 2:]
                modifications.append((pair_indices, new_elements))
        return modifications

    modifications = read_modifications("ModsCo.txt")

    for mod_index, (pair_indices, new_elements) in enumerate(modifications):
        modified_atoms = copy.deepcopy(atoms)
        for i, pair_index in enumerate(pair_indices):
            if pair_index < len(co_pairs):
                index1, index2 = co_pairs[pair_index]
                modified_atoms[index1].symbol = new_elements[i]
                modified_atoms[index2].symbol = new_elements[i]
        
        # Make new directory for each new structure
        directory_name = f"Modification_{mod_index + 1}"
        os.makedirs(directory_name, exist_ok=True)
        
        output_filename = os.path.join(directory_name, f"POSCAR_modified_{mod_index + 1}.vasp")
        write(output_filename, modified_atoms, format="vasp")
        print(f"Modified POSCAR saved in directory {directory_name} as {output_filename}.")

def modify_lco():
    '''Modifies structures based of user input. '''
    userdir = os.path.expanduser('~/wf-user-files')
    fullpath = os.path.join(userdir,'POSCAR')
    shutil.copy(fullpath, os.getcwd())
    # Read POSCAR 
    atoms = read(os.path.join(os.getcwd(),'POSCAR'))

    # Define number of each element in POSCAR
    element_counts = {"Li": 18, "Co": 18, "O": 36}  

    # Store pairs by element
    li_pairs = []
    co_pairs = []
    o_pairs = []
    index = 0  

    # Loop through each element and its count
    for element, count in element_counts.items():
        # Pair consecutive atoms of this element
        for i in range(count // 2):
            # Append the pair to the appropriate list based on the element type
            pair = (index, index + 1)
            if element == "Li":
                li_pairs.append(pair)
            elif element == "Co":
                co_pairs.append(pair)
            elif element == "O":
                o_pairs.append(pair)

            index += 2  # Move to the next pair
    
    save_pairs_to_file(li_pairs, "li_pairs.txt")
    save_pairs_to_file(co_pairs, "co_pairs.txt")
    save_pairs_to_file(o_pairs, "o_pairs.txt")
    print("Pairs saved to li_pairs.txt, co_pairs.txt, and o_pairs.txt.")
    
    modify_co_pairs(atoms,co_pairs)
    print("Modifications created.")