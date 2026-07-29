# Materials WorkForge CLI
#### Author: Dorothea Fennell (dfennell1@bnl.gov, dfennell37@gmail.com)
**Version**: 1.0.0
[![DOI](https://zenodo.org/badge/998980916.svg)](https://doi.org/10.5281/zenodo.21678725)
---
### Important Note:  
As the project has recently converted to v1.0, the documentation found in the [Workflow Guide](Workflow_Guide.md) is currently out of date. Updated documentation is in process and will be available soon!

---

Materials WorkForge (matworkforge) is a command-line interface (CLI) tool designed to simplify calculation set-up, submission, and post-processing for compositionally-tuned crystalline surfaces. Among its capabilities are:
- Create surface structures
- Modify composition
- Create vacancies
- Submit calculations
- Calculate vacancy energy
- Set up PDOS calculations
- Parse, integrate and plot PDOS
- Check calculations for errors, timeouts, and cancellations, fixes minor errors, and resubmits calculations
- Extract descriptors for machine learning

## Installing the Package:
Matworkforge can be installed in multiple ways, depending on your needs. If you want to use the package as-is, you can install it like any other package. This can be done by using the GitHub link and pip or by downloading the WHL file and installing it manually. 

#### Note about Pymatgen:
For whatever reason, the latest versions of pymatgen have not been uploaded to PyPi, and as such, pip will be unable to install the required version for matworkforge. If you are using conda to manage your environment, you can install the correct version (>=2026.0.0) with conda. For other installation methods, refer to Pymatgen's documentation.
| Note: It is *highly recommended* to install and use the package in a separate environment to minimize potential dependency conflicts.|
|:---|

**Editable Installation:**  
To create an editable installation, you will first need to install Poetry, which we use as a package builder and dependency manager. The Poetry docs are linked here for reference: [Poetry Docs](https://python-poetry.org/docs/). After installing Poetry, run `poetry self update`. This is the best way to make sure Poetry is up to date before setting up the installation. 

You can then install the package by either cloning the GitHub repository or by downloading the tar.gz file and un-tarring it in your home directory. Cloning the repository is probably the easiest way to get any updates made, but I (as of writing this) have not tried that method. It should work, but if you want to be one hundred percent certain it will work, I would recommend using the tar file. 

After installing, go into the package's head directory, which contains the *pyproject.toml* and *poetry.lock* files. Then run `poetry install` to install the package and all necessary dependencies. If Poetry returns an error, run `poetry self update` and then try again. 

## Matworkforge Commands (`wf`):

**Usage**:

```console
$ wf [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-v, --version`
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `generate`: <span style="color: #008080; text-decoration-color: #008080">Generate</span> surface structure from bulk.
* `modify`: <span style="color: #008080; text-decoration-color: #008080">Modify</span> structure.
* `vacancy`: Create <span style="color: #ff0000; text-decoration-color: #ff0000">vacancies</span>.
* `adsorbate`: <span style="color: #008000; text-decoration-color: #008000">Add</span> adsorbates to structures.
* `sites`: Generates lists of <span style="color: #008080; text-decoration-color: #008080">site pairs</span>.
* `preflight`: <span style="color: #af00ff; text-decoration-color: #af00ff">Verify</span> input files.
* `submit`: <span style="color: #af00ff; text-decoration-color: #af00ff">Submit</span> VASP calculations.
* `check`: <span style="color: #af00ff; text-decoration-color: #af00ff">Check</span> calculations for errors.
* `status`: Print <span style="color: #af00ff; text-decoration-color: #af00ff">status</span> of all calculations.
* `gete`: Get <span style="color: #d7d700; text-decoration-color: #d7d700">energies</span>.
* `chgdiff`: Generate and plot <span style="color: #d7d700; text-decoration-color: #d7d700">charge difference</span>.
* `pdos`: Set up <span style="color: #d70087; text-decoration-color: #d70087">PDOS</span> calculations.
* `parse`: <span style="color: #d70087; text-decoration-color: #d70087">Parse</span> PDOS data into...
* `integrate`: <span style="color: #d70087; text-decoration-color: #d70087">Integrate</span> already parsed PDOS files.
* `plot`: <span style="color: #d70087; text-decoration-color: #d70087">Plot</span> PDOS.
* `extract`: <span style="color: #ff8700; text-decoration-color: #ff8700">Extract</span> descriptors.
* `init`: <span style="color: #0087ff; text-decoration-color: #0087ff">Initialize</span> workflow...
* `prep`: <span style="color: #0087ff; text-decoration-color: #0087ff">Prepare</span> directory for set...

## `wf generate`

<span style="color: #008080; text-decoration-color: #008080">Generate</span> surface structure based on bulk structure and user input. Bulk structure can be given as a file or as a Materials Project ID. Workflow will also prompt for supercell size and Miller index.
    
If command line options are provided, workflow will bypass input sections for the provided information. 
    
<span style="font-weight: bold">Note:</span> If using Materials Project, an API key <span style="font-weight: bold">MUST</span> be provided.

**Usage**:

```console
$ wf generate [OPTIONS]
```

**Options**:

* `-b, --bulk TEXT`: Path to bulk file or Material Project ID.
* `-s, --sc-size TEXT`: Supercell size given as set of vectors or list of scaling factors.
* `-m, --miller TEXT`: Miller index of facet, given as comma-separated list.
* `-v, --vacuum INTEGER`: Thickness of vacuum layer, in angstrom (Å). Default is 10 Å.
* `--help`: Show this message and exit.

## `wf modify`

<span style="color: #008080; text-decoration-color: #008080">Modify</span> structure based on user input.

**Usage**:

```console
$ wf modify [OPTIONS]
```

**Options**:

* `-i, --ignore-sym`: Modify structures, ignoring symmetry.
* `--help`: Show this message and exit.

## `wf vacancy`

Create <span style="color: #ff0000; text-decoration-color: #ff0000">vacancies</span>.

**Usage**:

```console
$ wf vacancy [OPTIONS]
```

**Options**:

* `-i, --ignore-sym`: Create vacancies, ignoring symmetry.
* `--help`: Show this message and exit.

## `wf adsorbate`

<span style="color: #008000; text-decoration-color: #008000">Add</span> adsorbates to structures.

**Usage**:

```console
$ wf adsorbate [OPTIONS]
```

**Options**:

* `-i, --ignore-sym`: Add adsorbate, ignoring symmetry.
* `--help`: Show this message and exit.

## `wf sites`

Generates lists of <span style="color: #008080; text-decoration-color: #008080">site pairs</span>.

**Usage**:

```console
$ wf sites [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf preflight`

Runs pre-calculation checks to <span style="color: #af00ff; text-decoration-color: #af00ff">verify</span> VASP input files.

**Usage**:

```console
$ wf preflight [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf submit`

<span style="color: #af00ff; text-decoration-color: #af00ff">Submit</span> VASP calculations.

**Usage**:

```console
$ wf submit [OPTIONS] [CALC]
```

**Arguments**:

* `[CALC]`: The type of calculation to submit. Options: struc: Pristine or vacancy surface calculations. pdos: PDOS calculations  [default: struc]

**Options**:

* `-v, --vac`: Run only vacancy calculations. Does not work with calc = pdos
* `-a, --add`: Run only adsorption calculations. Does not work with calc = pdos
* `-f, --force`: Submits ALL calculations, including those that have been run before.
* `-s, --skip-preflight`: Skip input file verification.
* `--help`: Show this message and exit.

## `wf check`

<span style="color: #af00ff; text-decoration-color: #af00ff">Checks</span> calculations for errors and fixes and resubmits calculations if possible.

**Usage**:

```console
$ wf check [OPTIONS]
```

**Options**:

* `-n, --no-submit`: Use -n or --no-submit to run check without autosubmitting calculations
* `--help`: Show this message and exit.

## `wf status`

Print <span style="color: #af00ff; text-decoration-color: #af00ff">status</span> of all calculations in directory tree, including error codes.

**Usage**:

```console
$ wf status [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf gete`

Get <span style="color: #d7d700; text-decoration-color: #d7d700">energies</span> and generate E_pristine, E_vac, and E_ads CSV files.

**Usage**:

```console
$ wf gete [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf chgdiff`

Generates CHGDIFF.cube file from pristine and vacancy CHGCAR files and visualize the <span style="color: #d7d700; text-decoration-color: #d7d700">charge difference</span>. 
<span style="font-weight: bold">Note:</span> CHGCAR files <span style="font-weight: bold">MUST</span> have the same size real space grids.

**Usage**:

```console
$ wf chgdiff [OPTIONS]
```

**Options**:

* `-n, --no-show-image`: Do not display plot in X11 window after running command.
* `--help`: Show this message and exit.

## `wf pdos`

Set up <span style="color: #d70087; text-decoration-color: #d70087">PDOS</span> calculations.

**Usage**:

```console
$ wf pdos [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf parse`

<span style="color: #d70087; text-decoration-color: #d70087">Parse</span> PDOS data into individual files and integrates.

**Usage**:

```console
$ wf parse [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf integrate`

<span style="color: #d70087; text-decoration-color: #d70087">Integrate</span> the PDOS files. 
<span style="font-weight: bold">Note:</span> Files <span style="font-weight: bold">MUST</span> be parsed before integration. The parse command parses AND integrates, so this command should only be used if integration needs to be performed on already parsed files.

**Usage**:

```console
$ wf integrate [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf plot`

<span style="color: #d70087; text-decoration-color: #d70087">Plot</span> PDOS.

**Usage**:

```console
$ wf plot [OPTIONS]
```

**Options**:

* `-n, --no-show-image`: Do not display plot in X11 window after running command.
* `--help`: Show this message and exit.

## `wf extract`

<span style="color: #ff8700; text-decoration-color: #ff8700">Extract</span> ML descriptors from PDOS and optimization calculations.

**Usage**:

```console
$ wf extract [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf init`

<span style="color: #0087ff; text-decoration-color: #0087ff">Initialize</span> workflow settings.

**Usage**:

```console
$ wf init [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `wf prep`

<span style="color: #0087ff; text-decoration-color: #0087ff">Prepare</span> directory for set of calculations.

**Usage**:

```console
$ wf prep [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.
