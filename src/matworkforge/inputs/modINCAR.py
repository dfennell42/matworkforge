import os

# Find _MAGMOM.txt file in the current Modification_# directory
def find_magmom_file(modification_dir):
    # Look for the _MAGMOM.txt file in the current directory
    for file in os.listdir(modification_dir):
        if file.endswith("_MAGMOM.txt"):
            return os.path.join(modification_dir, file)
    return None

# Function to update the INCAR file: delete the existing MAGMOM line and add the new one
def update_incar_with_magmom(incar_path, magmom_file):
    with open(incar_path, "r") as incar:
        incar_lines = incar.readlines()

    # Read the MAGMOM line from the _MAGMOM.txt file
    with open(magmom_file, "r") as magmom:
        magmom_line = magmom.read().strip()  # Read the full line (including 'MAGMOM =')

    # Remove any existing MAGMOM line
    updated_lines = [line for line in incar_lines if not line.strip().startswith("MAGMOM")]
        
    # Add the new MAGMOM line at the end of the file
    updated_lines.append(f"{magmom_line}\n")

    # Write the updated INCAR file back
    with open(incar_path, "w") as incar:
        incar.writelines(updated_lines)

    print(f"Updated MAGMOM in: {incar_path}")

# Function to recursively find INCAR files in VASP_inputs and update them
def update_incar_files_with_magmom(root_dir):
    # Walk through subdirectories in the ROOT directory
    for subdir, dirs, files in os.walk(root_dir):
        # Check if the subdirectory is a "Modification_#" directory
        if "Modification_" in subdir:
            vasp_inputs_dir = os.path.join(subdir, "VASP_inputs")
            if os.path.exists(vasp_inputs_dir):
                # Search for INCAR files inside the VASP_inputs subdirectory
                for file in os.listdir(vasp_inputs_dir):
                    if file == "INCAR":  # If INCAR file is found
                        incar_path = os.path.join(vasp_inputs_dir, file)
                        magmom_file = find_magmom_file(subdir)  # Find the _MAGMOM.txt in the current Modification_# directory
                        if magmom_file:
                            update_incar_with_magmom(incar_path, magmom_file)
                        else:
                            print(f"No _MAGMOM.txt file found in {subdir}")

