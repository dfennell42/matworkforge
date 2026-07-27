"""
Update command for workflow
Author: Dorothea Fennell
Changelog: 
    8-6-25: Created, comments added.
    12-9-25: Rewrote to pull from Github. 
"""
#import modules
from matworkforge import version
import os
import sys
import subprocess as sp
#define functions
def check_gh():
    '''checks to see if gh cli is installed.'''
    cp = sp.run(['gh'], capture_output=True)
    if "command not found" in str(cp.stdout):
        print('Please install the GitHub CLI package to use wf update.')
        print('The package can be found at https://github.com/cli/cli.')
        sys.exit()
    else:
        return
        
def check_gh_ext():
    '''checks to see if gh extension is installed.'''
    cp = sp.run(['gh','ext','list'], capture_output=True)
    if "gh-cp" in str(cp.stdout):
        return
    else:
        sp.check_call(['gh','ext','install','mislav/gh-cp'])

def get_pkg(suffix):
    '''get files from repository.'''
    cp = sp.run(['gh','api','-H','accept:application/vnd.github.v3.raw','repos/dfennell42/LCO-Workflow/contents/dist/','--jq','.[].name'],capture_output=True)
    out = str(cp.stdout).strip(r"b'\n")
    filelist = out.split(r"\n")
    sel_files = []
    for f in filelist:
        if suffix in f:
            sel_files.append(f)
    sel_files.sort()
    latest_file = sel_files[-1]
    vname = latest_file.split('-')[1].strip('.targz')
    return vname, latest_file
    
def check_vrsn(suffix):
    '''checks current version. Installs new version if necessary.'''
    current_vrsn = version
    check_gh()
    check_gh_ext()
    new_vrsn, latest_file = get_pkg(suffix)
    if current_vrsn == new_vrsn:
        print('Workflow is up to date!')
        return
    elif current_vrsn != new_vrsn:
        destpath = os.path.expanduser('~/')
        sp.check_call(['gh','cp','dfennell42/LCO-Workflow',f'dist/{latest_file}',f'{destpath}'])
        if suffix == '.whl':
            try:
                sp.check_call(['pip','install',f'{destpath}/{latest_file}'])
            except:
                print('Updated wheel file has been downloaded but not installed.')
            else:
                print('Workflow has been updated!')
        elif suffix == '.tar.gz':
            print('Updated tar file has been downloaded.')
            
