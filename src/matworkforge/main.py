
import typer
from typing_extensions import Annotated
import os
from dotenv import load_dotenv

from . import version

from .structures.bulk_to_sc import create_structure
from .structures.modifystructure import modify_structure
from .structures.remove_pairs import process_vasp_inputs
from .structures.remove_atoms import process_vasp_inputs_nosym
from .structures.add_pairs import process_vasp_dirs
from .structures.add_atoms import process_vasp_dirs_nosym
from .structures.list_sites import get_pairs

from .inputs.MagMom_recursive import process_poscar_files
from .inputs.POTCAR_cat import process_directories
from .inputs.VASP_input import generate_vasp_inputs_in_dir
from .inputs.modINCAR import update_incar_files_with_magmom
from .inputs.removed_pairs_INCARmod import process_pairs_mod_dirs

from .energies.get_e_pristine import get_all_e
from .energies.Calc_Evac import process_e_vac
from .energies.calc_Eads import process_e_ads

from .pdos.createPDOS import process_vasp_inputs as pdos_vasp_inputs
from .pdos.pdos_INCARmod import process_pdos_dirs
from .pdos.vasp_pdos import process_pdos_dirs as parse_pdos_dirs
from .pdos.integrate_pdos import integrate_all_pdos
from .pdos.tot_int import get_all_data
from .pdos.PDOS_plotter import plot_pdos

from .job_handling.err_check import err_fix
from .job_handling.status_check import print_status
from .job_handling.preflight import print_preflight
from .job_handling.new_submit import submit_calcs

from .descriptors.get_descriptors import extract_desc

from .charges.chg_diff import get_chgdiff

from .utils.settings import read_settings,update_settings
from .utils.prepare import prepare_dir
from .utils.initialize import init_settings

#load variables
load_dotenv()
#create app
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]},rich_markup_mode='rich')

#create callback for version
@app.callback(invoke_without_command=True)
def vrsn_callback(
        ctx: typer.Context,
        vrsn: Annotated[bool, typer.Option("--version", '-v')] = False
         ):
    if ctx.invoked_subcommand is None and vrsn == True:
        print(f'matworkforge version is {version}')
#create commands
##-------Structures-------##
@app.command(short_help='[cyan]Generate[/] surface structure from bulk.',rich_help_panel='Structure Gen & Modification')
def generate(
        bulk: Annotated[str | None, typer.Option('--bulk','-b', help='Path to bulk file or Material Project ID.',show_default=False)] = None,
        sc_size: Annotated[str | None, typer.Option('--sc-size','-s', help='Supercell size given as set of vectors or list of scaling factors.',show_default=False)] = None,
        miller: Annotated[str | None, typer.Option('--miller','-m', help='Miller index of facet, given as comma-separated list.',show_default=False)] = None, 
        vacuum: Annotated[int, typer.Option('--vacuum','-v',help='Thickness of vacuum layer, in angstrom (Å). Default is 10 Å.',show_default=False)] = 10,
        ):
    '''
    [cyan]Generate[/] surface structure based on bulk structure and user input. Bulk structure can be given as a file or as a Materials Project ID. Workflow will also prompt for supercell size and Miller index.
    \nIf command line options are provided, workflow will bypass input sections for the provided information. 
    \n[bold]Note:[/] If using Materials Project, an API key [bold]MUST[/] be provided. 
    '''
    create_structure(bulk,sc_size,miller,vacuum)

@app.command(short_help='[cyan]Modify[/] structure.',rich_help_panel='Structure Gen & Modification')
def modify(
        ignore_sym: Annotated[bool,typer.Option('--ignore-sym','-i',help='Modify structures, ignoring symmetry.')] = False
        ):
    '''[cyan]Modify[/] structure based on user input. '''
    settings = read_settings()
    if ignore_sym == True and settings['ignore-symmetry'] == False:
        update_settings({'ignore-symmetry':True,'incar-params':{'ISYM':-1}})
        settings = read_settings()
    modify_structure(os.getcwd(),settings,ignore_sym)
    process_poscar_files(settings,mod=None)
    process_directories(os.getenv('POT_PATH'), vac = False, add=False)
    generate_vasp_inputs_in_dir(os.getcwd(),settings)
    update_incar_files_with_magmom(os.getcwd(),settings)

@app.command(rich_help_panel='Structure Gen & Modification')
def vacancy(
        ignore_sym: Annotated[bool,typer.Option('--ignore-sym','-i',help='Create vacancies, ignoring symmetry.')] = False
        ):
    '''Create [red1]vacancies[/].'''
    settings = read_settings()
    if settings['ignore-symmetry'] == True:
        ignore_sym = True
    if ignore_sym == True:
        element_name = process_vasp_inputs_nosym(os.getcwd())
    elif ignore_sym == False:
        element_name = process_vasp_inputs(os.getcwd())
    process_pairs_mod_dirs(os.getcwd(), element_name, 'Removed',ignore_sym=ignore_sym)
    process_directories(os.getenv('POT_PATH'), vac = True, add=False)
        
@app.command(rich_help_panel='Structure Gen & Modification')
def adsorbate(
        ignore_sym: Annotated[bool,typer.Option('--ignore-sym','-i',help='Add adsorbate, ignoring symmetry.')] = False
        ):
    '''[green]Add[/] adsorbates to structures.'''
    settings = read_settings()
    if settings['ignore-symmetry'] == True:
        ignore_sym = True
    if ignore_sym == True:
        element_name = process_vasp_dirs_nosym(os.getcwd())
    elif ignore_sym == False:
        element_name = process_vasp_dirs(os.getcwd())
    process_pairs_mod_dirs(os.getcwd(), element_name, 'Added',ignore_sym=ignore_sym)
    process_directories(os.getenv('POT_PATH'), vac=False, add=True)

@app.command(rich_help_panel='Structure Gen & Modification')
def sites():
    '''Generates lists of [cyan]site pairs[/].'''
    settings = read_settings()
    get_pairs(settings)
    
##------Job Handling------##

@app.command(short_help='[purple]Verify[/] input files.',rich_help_panel='Job Handling & Submission')
def preflight():
    '''Runs pre-calculation checks to [purple]verify[/] VASP input files.'''
    print_preflight()
    
@app.command(rich_help_panel='Job Handling & Submission')
def submit(
        calc: Annotated[str, typer.Argument(help='The type of calculation to submit. Options: struc: Pristine or vacancy surface calculations. pdos: PDOS calculations')] = 'struc',
        vac:Annotated[bool,typer.Option("--vac","-v",help='Run only vacancy calculations. Does not work with calc = pdos')] = False,
        add: Annotated[bool,typer.Option("--add","-a",help='Run only adsorption calculations. Does not work with calc = pdos')] = False,
        force: Annotated[bool, typer.Option("--force","-f",help="Submits ALL calculations, including those that have been run before.")] = False,
        skip_preflight: Annotated[bool,typer.Option('--skip-preflight','-s',help='Skip input file verification.')] = False
        ):
    '''[purple]Submit[/] VASP calculations.'''
    if calc.lower() == 'struc':
        if vac:
            calc_type = "_Removed"
        elif add:
            calc_type = "_Added"
        else:
            calc_type = "all"
    elif calc.lower() == 'pdos':
        calc_type = "PDOS"
    submit_calcs(calc_type,force=force,skip_preflight=skip_preflight)
       
@app.command(short_help='[purple]Check[/] calculations for errors.',rich_help_panel='Job Handling & Submission')
def check(
        no_submit:Annotated[bool,typer.Option("--no-submit","-n",help='Use -n or --no-submit to run check without autosubmitting calculations',show_default=False)] = False
        ):
    '''[purple]Checks[/] calculations for errors and fixes and resubmits calculations if possible.'''
    err_fix(os.getcwd(),no_submit)

@app.command(short_help='Print [purple]status[/] of all calculations.',rich_help_panel='Job Handling & Submission')
def status():
    '''Print [purple]status[/] of all calculations in directory tree, including error codes.'''
    print_status()

##-------Energies-------##

@app.command(short_help='Get [yellow3]energies[/].',rich_help_panel='Energies & Charges')
def gete():
    '''Get [yellow3]energies[/] and generate E_pristine, E_vac, and E_ads CSV files.'''
    settings = read_settings()
    get_all_e(os.getcwd(),settings)
    process_e_vac(os.getcwd(),settings)
    process_e_ads(os.getcwd(),settings)

@app.command(short_help='Generate and plot [yellow3]charge difference[/].',rich_help_panel='Energies & Charges')
def chgdiff(
        no_show:Annotated[bool,typer.Option('--no-show-image','-n',help='Do not display plot in X11 window after running command.',show_default=False)] = False,
        ):
    '''
    Generates CHGDIFF.cube file from pristine and vacancy CHGCAR files and visualize the [yellow3]charge difference[/]. 
    [bold]Note:[/] CHGCAR files [bold]MUST[/] have the same size real space grids.
    '''
    get_chgdiff(no_show)

##-------PDOS--------##

@app.command(rich_help_panel='PDOS')
def pdos():
    '''Set up [deep_pink3]PDOS[/] calculations.'''
    settings = read_settings()
    pdos_vasp_inputs(os.getcwd(),settings)
    process_pdos_dirs(os.getcwd())
    
@app.command(rich_help_panel='PDOS')
def parse():
    '''[deep_pink3]Parse[/] PDOS data into individual files and integrates.'''
    parse_pdos_dirs(os.getcwd())
    integrate_all_pdos(os.getcwd())
    get_all_data(os.getcwd())
    
@app.command(short_help='[deep_pink3]Integrate[/] already parsed PDOS files.',rich_help_panel='PDOS')
def integrate():
    '''
    [deep_pink3]Integrate[/] the PDOS files. 
    [bold]Note:[/] Files [bold]MUST[/] be parsed before integration. The parse command parses AND integrates, so this command should only be used if integration needs to be performed on already parsed files.
    '''
    integrate_all_pdos(os.getcwd())
    get_all_data(os.getcwd())
    
@app.command(rich_help_panel='PDOS')
def plot(
        no_show:Annotated[bool,typer.Option('--no-show-image','-n',help='Do not display plot in X11 window after running command.',show_default=False)] = False,
        ):
    '''[deep_pink3]Plot[/] PDOS.'''
    plot_pdos(os.getcwd(),no_show)

##------Descriptors------##

@app.command(short_help='[dark_orange]Extract[/] descriptors.',rich_help_panel='Descriptors')
def extract():
    '''[dark_orange]Extract[/] ML descriptors from PDOS and optimization calculations.'''
    extract_desc(os.getcwd())
    
##-------Utils--------##
    
@app.command(rich_help_panel='Utils')
def init():
    '''[dodger_blue1]Initialize[/] workflow settings.'''
    init_settings()

@app.command(rich_help_panel='Utils')
def prep():
    '''
    [dodger_blue1]Prepare[/] directory for set of calculations.
    '''
    prepare_dir()

