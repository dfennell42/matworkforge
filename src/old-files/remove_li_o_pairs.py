import os
import shutil
import copy
from ase.io import read, write

def copy_vasp_files(source_dir, dest_dir):
    """Copies essential VASP input files from source to destination."""
    os.makedirs(dest_dir, exist_ok=True)  # Ensure the target directory exists
    #list of files to copy
    FILES_TO_COPY = ["INCAR", "KPOINTS", "POTCAR"]
    for file in FILES_TO_COPY:
        src_file = os.path.join(source_dir, file)
        dest_file = os.path.join(dest_dir, file)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            print(f"Copied {file} to {dest_dir}")
        else:
            print(f"Warning: {file} not found in {source_dir}, skipping.")

def get_pairs(atoms, element):
    """Identifies inversion pairs for a given element."""
    indices = [i for i, atom in enumerate(atoms) if atom.symbol == element]
    return [(indices[i], indices[i + 1]) for i in range(0, len(indices), 2)] if len(indices) % 2 == 0 else []

def get_user_selection(pairs, element_name):
    """Asks the user to select pairs for removal."""
    print(f"\nAvailable {element_name} pairs:")
    for idx, pair in enumerate(pairs):
        print(f"{idx}: {pair}")

    pair_indices_to_remove = input(f"Enter the indices of {element_name} pairs to remove (comma-separated): ")
    return [int(idx) for idx in pair_indices_to_remove.split(',') if idx.isdigit()]

def remove_selected_pairs(atoms, pairs,removal_choice,selected_indices=None,pair_index=None):
    """Removes the selected pairs from the atom structure."""
    modified_atoms = copy.deepcopy(atoms)
    if removal_choice =='1':
        for pair_index in selected_indices:
            if pair_index < len(pairs):
                index1, index2 = pairs[pair_index]
                modified_atoms[index1].symbol = "X"  # Mark atoms for removal
                modified_atoms[index2].symbol = "X"
    elif removal_choice =='2':
        if pair_index < len(pairs):
            index1, index2 = pairs[pair_index]
            modified_atoms[index1].symbol = "X"  # Mark atoms for removal
            modified_atoms[index2].symbol = "X"

    # Remove atoms marked for deletion
    return modified_atoms[[atom.symbol != "X" for atom in modified_atoms]]

def process_removal(vasp_dir,pairs,selected_indices,removal_choice, element_name, i=None,index=None):
    """Creates POSCAR files with removed pairs, saves it, and copies it to new directory along with required files."""
    print(f"\nProcessing: {vasp_dir}")

    poscar_path = os.path.join(vasp_dir, "POSCAR")
    atoms = read(poscar_path)
    if removal_choice == '1':
        modified_atoms = remove_selected_pairs(atoms, pairs,removal_choice, selected_indices)
        name = f"{element_name}_Pairs"
    elif removal_choice == '2':
        pair_index = selected_indices[i]
        modified_atoms = remove_selected_pairs(atoms, pairs,removal_choice,pair_index= pair_index)
        name = f'{element_name}_Pair{index}'

    # Save the modified POSCAR
    output_dir = os.path.join(vasp_dir, f'{name}_Removed')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"POSCAR_removed_{name}.vasp")
    write(output_file, modified_atoms, format="vasp")
    print(f"Saved modified POSCAR: {output_file}")

    # Copy the modified POSCAR as just "POSCAR" for VASP
    final_poscar_path = os.path.join(output_dir, "POSCAR")
    shutil.copy2(output_file, final_poscar_path)
    print(f"Copied {output_file} to {final_poscar_path} for VASP.")

    # Copy required VASP files
    copy_vasp_files(vasp_dir, output_dir)

def process_vasp_inputs(base_directory):
    """Processes all VASP_inputs directories recursively, applying the same modifications to each."""
    all_dirs = []

    # Collect all VASP_inputs directories
    for root, dirs, files in os.walk(base_directory):
        if "VASP_inputs" in root and "POSCAR" in files:
            all_dirs.append(root)

    if not all_dirs:
        print("No VASP_inputs directories found.")
        return
    
    #ask user which structures they want to add to
    print("\nWould you like to remove pairs from pristine, vacancy, or adsorption structures?")
    print("1: Pristine")
    print("2: Vacancy")
    print("3: Adsorption")
    struc = input("Enter the number of your choice: ")
    vasp_dirs=[]
    
    for i in all_dirs:
        if struc == '1':
            if i.endswith('VASP_inputs'):
                vasp_dirs.append(i)
        elif struc == '2':
            if i.endswith('_Removed'):
                vasp_dirs.append(i)
        elif struc == '3':
            if i.endswith('_Added'):
                vasp_dirs.append(i)
                
    # Use the first POSCAR to get the pairs and user selection
    sample_poscar = os.path.join(vasp_dirs[0], "POSCAR")
    atoms = read(sample_poscar)

    # Identify Li and O pairs
    li_pairs = get_pairs(atoms, "Li")
    o_pairs = get_pairs(atoms, "O")

    # Ask user what they want to remove
    print("\nWhat would you like to do?")
    print("1: Remove Li pairs")
    print("2: Remove O pairs")
    choice = input("Enter the number of your choice: ")

    if choice == "1" and li_pairs:
        selected_indices = get_user_selection(li_pairs, "Li")
        element_name = "Li"
        pairs = li_pairs
    elif choice == "2" and o_pairs:
        selected_indices = get_user_selection(o_pairs, "O")
        element_name = "O"
        pairs = o_pairs
    else:
        print("Invalid choice or no pairs available. Exiting.")
        return
    
    #ask user if they would like to remove pairs from one structure or do separate structures
    print('\nWould you like to remove all pairs from one structure or create a separate structure for each pair removed?')
    print('1: Remove all pairs from same structure')
    print('2: Create a structure for each pair removal')
    removal_choice = input("Enter the number of your choice: ")

    # Apply the same modifications to all VASP_inputs directories
    for vasp_dir in vasp_dirs:
        if removal_choice == '1':
            process_removal(vasp_dir,pairs,selected_indices,removal_choice,element_name)
        elif removal_choice == '2':
            for i,index in enumerate(selected_indices):
                process_removal(vasp_dir,pairs,selected_indices,removal_choice, element_name,i,index)
      
    return element_name
