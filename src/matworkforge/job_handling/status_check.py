#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command to check status of calculations.
Author: Dorothea Fennell
Changelog: 
    6-18-26: Created, comments added.
    6-22-26: Finished StatusCheck class, added command to wf. 
"""
#import
import os
import warnings
import pandas as pd
import subprocess as sp
from typing import ClassVar
from pymatgen.io.vasp.outputs import Vasprun
from tabulate import TableFormat,Line,DataRow
#define class
class StatusCheck:
    '''Custom class to check status of calculations. Separate from ErrorHandler.'''
    vasp_msgs: ClassVar = {
        "tet": ["Tetrahedron method fails","tetrahedron method fails","Routine TETIRR needs special values","Tetrahedron method fails (number of k-points < 4)",],
        "ksymm": ["Fatal error detecting k-mesh","Fatal error: unable to match k-point",],
        "inv_rot_mat": ["rotation matrix was not found (increase SYMPREC)"],
        "brions": ["BRIONS problems: POTIM should be increased"],
        "pricel": ["internal error in subroutine PRICEL"],
        "zbrent": ["ZBRENT: fatal internal in", "ZBRENT: fatal error in bracketing","ZBRENT: fatal error: bracketing interval incorrect"],
        "pssyevx": ["ERROR in subspace rotation PSSYEVX"],
        "pdsyevx": ["ERROR in subspace rotation PDSYEVX"],
        "edddav": ["Error EDDDAV: Call to ZHEGV failed"],
        "zheev": ["ERROR EDDIAG: Call to routine ZHEEV failed!"],
        "eddiag": ["ERROR in EDDIAG: call to ZHEEV/ZHEEVX/DSYEV/DSYEVX failed"],
        "rhosyg": ["RHOSYG"],
        "posmap": ["POSMAP"],
        "point_group": ["group operation missing"],
        "pricelv": ["PRICELV: current lattice and primitive lattice are incommensurate"],
        "symprec_noise": ["determination of the symmetry of your systems shows a strong"],
        "bravais": ["Inconsistent Bravais lattice"],
        "hnform": ["HNFORM: k-point generating"],
        "set_core_wf": ["internal error in SET_CORE_WF"],
        "read_error": ["Error reading item", "Error code was IERR= 5"],
        "ibzkpt": ["not all point group operations"],
        "fexcf": ["supplied exchange-correlation table"],
        "spin_polarized_harris": ["Spin polarized Harris functional dynamics is a good joke"],
        }
    
    def __init__(self):
        '''Initialize StatusCheck.'''
        self.vasp_errors = dict(StatusCheck.vasp_msgs)
    
    def __get_calc_dirs(self,base_dir):
        '''Gets list of calculation directories.'''
        calc_dirs = []
        for root,dirs,files in os.walk(base_dir):
            fileset = set(files)
            if {"POSCAR","INCAR"}.issubset(fileset):
                calc_dirs.append(root)
        
        return calc_dirs
    
    def __get_calc_type(self,calc_dir):
        '''Gets calculation type.'''
        if calc_dir.endswith('PDOS'):
            calc_type = 'PDOS'
        elif calc_dir.endswith('_Removed'):
            basename = os.path.basename(calc_dir)
            species = basename.split('_')[0].title()
            pair = basename.split('_')[1].title()
            if pair[-1].isdigit() == True:
                calc_type = f'{species} {pair} Vacancy'
            else:
                calc_type = f'{species} Vacancy'
        elif calc_dir.endswith('_Added'):
            basename = os.path.basename(calc_dir)
            species = basename.split('_')[0].title()
            calc_type = f'{species} Adsorption'
        elif calc_dir.endswith('VASP_inputs'):
            calc_type = 'Pristine'
        
        for p in calc_dir.split('/'):
            if p.startswith('Modification_'):
                mod = p
        
        return mod, calc_type
    
    def __get_outcar(self,calc_dir):
        '''Finds OUTCAR'''
        files = os.listdir(calc_dir)
        if 'OUTCAR' in files:
            file = f'{calc_dir}/OUTCAR'
            return file
        else:
            return None
    
    def __get_slurm_file(self,calc_dir):
        slurm_files=[]
        for file in os.listdir(calc_dir):
            if file.startswith('slurm-'):
                slurm_files.append(os.path.join(calc_dir,file))

        if not slurm_files:
            return None
        
        slurm_files.sort()
        latest_file = slurm_files[-1]
        return latest_file
    
    def __get_slurm_status(self,calc_dir,latest_file):
        if latest_file != None:
            filename = os.path.basename(latest_file)
            jid = filename.split('-')[1].split('.')[0]
            try:
                codes = sp.check_output(['sacct','-n','-j',f'{jid}','-o','State'],stderr=sp.DEVNULL,text=True)
            except:
                pass
        
            if codes:
                job_state = codes.split('\n')[0].strip()
                state = job_state.title()
        else:
            pend_chk = sp.check_output(['sacct','-n','-s','pending','-o','State,WorkDir%500'],stderr=sp.DEVNULL,text=True)
            if pend_chk:
                jobs = pend_chk.split('\n')
                for j in jobs:
                    j = j.strip()
                    if calc_dir in j:
                        state = 'Pending'
            else:
                state = 'Not run'
        return state
    
    def get_status(self,base_dir):
        '''Prints status of all calculations in directory tree.'''
        #get dirs
        calc_dirs = self.__get_calc_dirs(base_dir)
        def sort_dirs(data):
            path_list = data.split('/')
            for p in path_list:
                if p.startswith('Modification_'):
                    num = p.split('_')[1]
                    return int(num)
        calc_dirs.sort(key=sort_dirs)
        #get status
        calc_list = []
        for calc in calc_dirs:
            #get mod, dir & type
            mod,calc_type = self.__get_calc_type(calc)
            #get slurm file & outcar
            latest_file = self.__get_slurm_file(calc)
            outcar = self.__get_outcar(calc)
            #check slurm status
            state = self.__get_slurm_status(calc, latest_file)
            #check for errors & convergence
            errors = set()
            if state.lower() == 'failed':
                if outcar != None:
                    with open(outcar,'rt') as file:
                        try:
                            text = file.read()
                        except:
                            errors.add('OUTCAR not read')
                        else:
                            #check for vasp errors
                            for err in self.vasp_errors:
                                for msg in self.vasp_errors[err]:
                                    if text.find(msg) != -1:
                                        errors.add(err)
                elif outcar == None:
                    errors.add('OUTCAR not found')
            elif state.lower() == 'completed':
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    vpr = Vasprun(f'{calc}/vasprun.xml')
                ion_con = vpr.converged_ionic
                elec_con = vpr.converged_electronic
                if elec_con == False:
                    if ion_con == False:
                        errors.add('Not electronically or ionically converged')
                    elif ion_con == True:
                        errors.add('Not electronically converged')
                elif elec_con == True:
                    if ion_con == False:
                        errors.add('Not ionically converged')
            #convert set to str
            err_str = ''
            for e in errors:
                err_str += e + ', '
            err_str = err_str.strip(', ')
            #create series
            calc_ser = pd.Series({'Modification':mod,'Type': calc_type,'Status':state,'Errors':err_str})
            calc_list.append(calc_ser)
        #convert to df
        df = pd.DataFrame(calc_list)
        #custom table format
        table = TableFormat(
            lineabove=Line("", "", "", ""),
            linebelowheader=Line("", "─", "┼", ""),
            linebetweenrows=None,
            linebelow=None,
            headerrow=DataRow("", "│", ""),
            datarow=DataRow("", "│", ""),
            padding=2,
            with_header_hide=None,
            )
        print(df.to_markdown(index=False,tablefmt=table))

#define function
def print_status():
    '''Gets status of jobs in directory tree and prints to command line.'''
    stat_chkr = StatusCheck()
    stat_chkr.get_status(os.getcwd())