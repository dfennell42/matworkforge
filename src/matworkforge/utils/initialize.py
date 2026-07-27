"""
Script to set up directory of base files for workflow
Author: Dorothea Fennell
Changelog: 
    6-23-25: Created, comments added
    6-18-26: Updated to accommodate script reorganization.
    7-9-26: Updated to include BulkE & MagMom dicts, incar parameter files, and base settings, as well as create an example files dir.
    7-17-26: Updated to set pseudopotential path as env variable.
"""
#import modules
import os
import shutil
import sys
import dotenv
#define functions
def copy_files(source_dir, dest_dir):
    """Copies files from source to destination."""
    os.makedirs(dest_dir, exist_ok=True)  # Ensure the target directory exists
    # List of files to copy
    FILES_TO_COPY = ["BulkE_dict.txt", "MagMom_dict.txt", "pdos_incar_params.toml","custom_incar_params.toml", "base_settings.toml"]
    for file in FILES_TO_COPY:
        src_file = os.path.join(source_dir, file)
        dest_file = os.path.join(dest_dir, file)
        if os.path.exists(src_file):
            shutil.copy2(src_file, dest_file)
            #print(f"Copied {file} to {dest_dir}")
        else:
            print(f"Warning: {file} not found in package, skipping.")

def make_wf_dir(source_dir):
    '''Makes directory with base files for workflow tools.'''
    user_dir = os.path.expanduser('~/')
    wf_dir = f'{user_dir}/wf-user-files'
    os.makedirs(wf_dir,exist_ok=True)
    
    #copy files
    copy_files(source_dir, wf_dir)
    ex_files = os.path.join(source_dir,'example_files')
    wf_ex = os.path.join(wf_dir,'example_files')
    shutil.copytree(ex_files,wf_ex)
    
def init_settings():
    '''Initialize settings and files'''
    #set up source dir
    pkgdir = sys.modules['matworkforge'].__path__[0]
    #set psuedo path
    print('\n Please input path to VASP pseudopotentials.')
    pot_path = input('Path:')
    dotenv.set_key(os.path.join(pkgdir,'.env'),'POT_PATH',pot_path)
    #print info
    print('\nAll base files (POSCAR, SpinPairs.txt, vasp.sh, etc.) should be added to directory "~/wf-user-files".\nAny edits to these files should be done in that directory.')
    #make dir
    make_wf_dir(f'{pkgdir}/text_files')