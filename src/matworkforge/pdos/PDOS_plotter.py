"""
Create PDOS plots from .dat file output from vasp_pdos.py
Author: Dorothea Fennell
Changelog: 
    4-14-25: Created, wrote file input section
    4-16-25: Wrote data parsing and plotting section, added checker for file path, added comments
    4-25-25: Added statement to change x range for Al, added section for one large plot with multiple subplots
    4-28-25: Added some minor changes to file names
    4-30-25: Added section so script functions recursively.
    8-6-25: Added gaussian smearing to the plotting. Fixed a couple other minor issues.
    9-10-25: Removed gaussian smearing now that gaussian method is used to compute PDOS.
    7-28-26: Updated for v1.0
"""
#import modules
import numpy as np
from plotly.subplots import make_subplots
from pathlib import Path
import sys
import os
from PIL import Image, ImageShow
#define functions
def make_plots(option=None, plot_choice=None, indices=None, titles=None):
    '''Makes subplots based on user input'''
    #make subplots for multiple pdos in one fig
    if plot_choice == '2':
        cols = len(indices)
        if cols<=6:
            columns = cols
            rows = 1
        elif cols > 6:
            columns = 6
            if cols%6 == 0:
                rows = int(cols/6)
            elif cols%6 >0:
                rows = int(cols/6)+1
        fig = make_subplots(rows = rows, cols = columns, subplot_titles=titles, shared_yaxes=True, vertical_spacing=0.1)
    #make individual plots
    else:
        fig = make_subplots()
    #colors
    if option == '1':
        colorlist = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
        fig.update_layout(colorway = colorlist)
    elif option == '2':
        colorlist = ['rgb(102,194,165)','rgb(27,158,119)','rgb(252,141,98)', 'rgb(217,95,2)', 'rgb(141,160,203)','rgb(117,112,179)','rgb(231,138,195)', 'rgb(231,41,138)','rgb(166,216,84)', 'rgb(102,166,30)', 'rgb(255,217,47)','rgb(230,171,2)','rgb(229,196,148)', 'rgb(166,118,29)','rgb(179,179,179)', 'rgb(102,102,102)']
        fig.update_layout(colorway = colorlist)
    #update layout and axes
    fig.update_layout(template='plotly_white',title =dict(x=0.5, xanchor='center', font_size=20), font_family = 'Nimbus Roman',margin=dict(b=20))
    fig.update_xaxes(title = 'DOS', showline = True, zeroline = True, zerolinewidth=1, zerolinecolor='#262626', showticklabels=False,linewidth=2, linecolor = '#262626',range=[-6,6])
    fig.update_yaxes(title = 'Energy (eV)', showline = True, zeroline = True, zerolinewidth=1, zerolinecolor='#262626',linewidth=2, linecolor = '#262626', ticks ='outside', range=[-10,6])
    fig.update_traces(line_width=3)

    return fig

def fermi_energy(base_dir):
    '''
    Determining fermi energy from given OUTCAR file. 
    Note: TotalDos and Atom files with individual orbitals are not fermi shifted but atom_total files are
    '''
    line=""
    for l in open(f'{base_dir}/OUTCAR',"r").readlines():
        if "Fermi energy:" in l:
            line=l
    if line.startswith(' BZINTS'):
        fermi = float(line.split()[3].strip(';'))
    else:
        fermi=float(line.split()[2])
    return fermi

def get_filelist(pdos_dir,indices, suffix):
    filelist =[]
    for i in indices:
        i = i.strip()
        file = list(Path(f'{pdos_dir}').glob(f'*[a-zA-Z]{i}{suffix}'))
        if Path(file[0]).exists() == True:
            filelist.append(file[0])
        else:
            print('File not found.')
    return filelist
    
def save_plot(fig, filename, base_dir,w=500, h=600, s=1.25, no_show_image=False):
    full_fname = f'{base_dir}/{filename}'
    fig.write_image(full_fname, width=w, height=h, scale=s)
    if no_show_image == False:
        plot = Image.open(full_fname)
        ImageShow.show(plot)
    elif no_show_image == True:
        print(f'{filename} saved.')

def get_orbs(file):
    '''Get list of orbitals'''
    with open(file,'r') as f:
        lines = f.readlines()
    header = lines[0].strip()
    orbs = header.split(' ')
    orbs = [o for o in orbs if not o == 'energies']
    return orbs

def option1(f,fig,plot_choice, r=1, c =1):
    #this one needs to be unpacked because it's saved by numpy.savetxt rather than .write()
    data = np.genfromtxt(f, skip_header=1)
    #generate name for plot & file
    filename = str(f).split('/')
    name=str(filename[-1]).split('.')
    name=str(name[0]).split("_")
    #data
    energy = data[:,0]
    orbs = get_orbs(f)
    for i, orb in enumerate(orbs,1):
        if not(i==1 or i==2):
            if i%2 == 0:
                #multiply the down values by -1 to show pdos by spin
                x = data[:,i]*-1
                fig.add_scatter(x=x, y=energy, mode='lines',fill='tozerox', name = f'{orb}',row = r, col = c)
            else:
                fig.add_scatter(x=data[:,i], y=energy, mode='lines',fill='tozerox', name = f'{orb}',row = r, col = c)
    #add plot title
    if plot_choice == '1':
        plot_title = f'PDOS of {name[0]}'
    elif plot_choice == '2':
        plot_title = f'{name[0]}'
    fig.update_layout(title_text = plot_title)
    fig.update_yaxes(minor=dict(ticks='outside',tickcolor='black',dtick=1))
    return fig, name

def option2(f,fig,fermi,plot_choice,r=1,c=1):
    data = np.genfromtxt(f, skip_header=1)
    #generate name for plot & file
    filename = str(f).split('/')
    name=str(filename[-1]).split('.')
    name=str(name[0]).split("_")
    #data
    energy = data[:,0]-fermi
    orbs = get_orbs(f)
    for i, orb in enumerate(orbs,1):
        if not(i==1 or i==2):
            if i%2 == 0:
                #multiply the down values by -1 to show pdos by spin
                x = data[:,i]*-1
                fig.add_scatter(x=x, y=energy, mode='lines', name = f'{orb}',row = r, col = c)
            else:
                fig.add_scatter(x=data[:,i], y=energy, mode='lines', name = f'{orb}',row = r, col = c)

        #update axes if necessary
        #if str(name[0]).startswith('Al'):
            #fig.update_xaxes(range =[-0.2,0.2], row =r, col=c)
        #add plot title
        if plot_choice == '1':
            plot_title = f'PDOS of {name[0]}'
        elif plot_choice == '2':
            plot_title = f'{name[0]}'
        fig.update_layout(title_text = plot_title)
        #fig.add_hline(y=fermi,line_width=2, line_dash="dash",line_color='purple',annotation_text='E_fermi',annotation_font_color = 'purple',annotation_font_size=12)
    return fig, name

def check_input(user_input):
    if user_input.lower() == 'exit':
        print('Exiting...')
        sys.exit()

def plot_pdos(base_dir, no_show_img):
    print('\n If you would like to exit, type "exit" into any input prompt.')
    print('\nWould you like this to run recursively?')
    print('\nEntire either "y" for all directories, or input the number(s) of the directories (comma-separated).')
    rec = input()
    check_input(rec)
    print("\nWould you like to plot the PDOS of all structures, the pristine structures, or the vacancy structures?")
    print("1: All")
    print("2: Pristine")
    print("3: Vacancy")
    print("4: Adsorption")
    struc = input('Enter the number of your choice: ')
    check_input(struc)
    pdos_dirs = []
    if rec == 'y':
        for root, dirs, files in os.walk(base_dir):
            dirname = os.path.dirname(root)
            prev_dir = os.path.basename(dirname)
            if struc =='1':
                if root.endswith('PDOS'):
                    pdos_dirs.append(root)
            elif struc =='2':
                if root.endswith('VASP_inputs/PDOS'):
                    pdos_dirs.append(root)
            elif struc =='3':
                if root.endswith('_Removed/PDOS'):
                    pdos_dirs.append(root)
            elif struc=='4':
                if root.endswith('_Added/PDOS'):
                    pdos_dirs.append(root)
    else:
        dir_num = rec.split(',')
        for num in dir_num:
            num = num.strip()
            for root, dirs, files in os.walk(base_dir):
                if f'Modification_{num}/' in root:
                    dirname = os.path.dirname(root)
                    prev_dir = os.path.basename(dirname)
                    if struc =='1':
                        if root.endswith('PDOS'):
                            pdos_dirs.append(root)
                    elif struc =='2':
                        if root.endswith('VASP_inputs/PDOS'):
                            pdos_dirs.append(root)
                    elif struc =='3':
                        if root.endswith('_Removed/PDOS'):
                            pdos_dirs.append(root)
    
    print("\nPlease input the files you'd like to plot")
    print("If plotting PDOS for single atoms, input atom index. Multiple indices should be comma-separated.")
    print("If plotting total DOS, input 'TotalDos'")
    choice = input()
    check_input(choice)
    if choice == 'TotalDos':
       #moved this to the for loop
       fname='TotalDos.dat'
    else:
        indices = choice.split(',')
        print("\nWould you like to plot the PDOS with the orbitals summed by type (all d summed, etc.) or with individual orbitals (dxy,dxz,etc.)?")
        print("1: Summed")
        print("2: Individual")
        option = input('Enter the number of your choice: ')
        check_input(option)
        if option == '1':
            suffix = '_total.dat'
        elif option == '2':
            suffix = '.dat'
        else:
            print("Invalid choice. Exiting.")
            sys.exit()
                
        if len(indices) >= 2:
        #option for one large plot with multiple subplots together
            print("\nWould you like individual plots or one large plot with multiple subplots?")
            print("1: Individual")
            print("2: One Plot")
            plot_choice = input('Enter the number of your choice: ')
            check_input(plot_choice)
        elif len(indices) < 2:
            plot_choice = '1'
            
    for pdos_dir in pdos_dirs:
        #get fermi energy
        fermi = fermi_energy(pdos_dir)
        #generating data & plotting
        if choice == 'TotalDos':
            file = Path(f'{pdos_dir}/{fname}').resolve()
            #setting up plot
            fig = make_plots()
            #gettin data
            data = np.genfromtxt(file, skip_header=1)
            #defines x(dos) and y(energy) values
            #multiply the down values by -1 to show pdos by spin
            energy = data[:,0]-fermi
            up = data[:,1]
            down = data[:,2]*-1
            fig.add_scatter(x=up, y = energy, mode = 'lines', fill = 'tozerox')
            fig.add_scatter(x=down, y = energy, mode = 'lines', fill = 'tozerox')
            fig.update_layout(title_text = 'Total Density of States', showlegend=False)
            fig.update_xaxes(range=None,showticklabels=True,ticks='outside')
            fig.update_yaxes(range=None)
            #save image
            save_plot(fig,'TotalDos.png',pdos_dir,no_show_image=no_show_img)
        else:
            #creating list of files
            filelist = get_filelist(pdos_dir,indices, suffix)
            if plot_choice == '1':
                for f in filelist:
                    #setting up individual plots
                    fig = make_plots(option,plot_choice,indices)
                    if option == '1':
                        fig, name = option1(f,fig,plot_choice)
                        fname = f'{name[0]}.png'
                    elif option == '2':
                        fig, name = option2(f,fig,fermi,plot_choice)
                        fname = f'{name[0]}_indiv.png'
                    save_plot(fig,fname,pdos_dir,no_show_image=no_show_img) 
            #for one large plot
            elif plot_choice == "2":
                #empty list for subplot titles
                titles =[]
                txt = " "
                for f in filelist:
                    filename = str(f).split('/')
                    name=str(filename[-1]).split('.')
                    name=str(name[0]).split("_")
                    #add name to titles list 
                    titles.append(str(name[0]))
                    #add atom to file name
                    txt = txt + str(name[0])
                txt = txt.strip()
                filename = str(txt+'.png')
                #set up plot
                fig = make_plots(option,plot_choice,indices,titles)
                #run through the enumerated filelist so we can assign each one a row & column
                for i, f in enumerate(filelist, 1):
                    #determine row & column number
                    if i<=6:
                        cl = i
                        cw = i
                        rw = 1
                    elif i>6:
                        cl = i - 6
                        cw = 6
                        if i%6 == 0:
                            rw = int(i/6)
                        elif i%6 >0:
                            rw = int(i/6)+1
                    #option sets summed or individual orbitals
                    if option == '1':
                        fig, name = option1(f,fig,plot_choice,rw,cl)
                        #hide legend for everything other than 1st subplot as colors will be the same
                        #fig.update_layout(title_text = f'PDOS of Selected Atoms')
                        if rw > 1 or cl > 1:
                            fig.update_traces(showlegend=False, row=rw, col=cl)
                        if cl>1:
                            fig.update_yaxes(title = " ", row=rw, col=cl)
                    elif option == '2':
                        fig,name = option2(f,fig,fermi,plot_choice,rw,cl)
                        #hide legend for everything other than 1st subplot as colors will be the same
                        #fig.update_layout(title_text = f'PDOS of Selected Atoms')
                        if rw > 1 or cl > 1:
                            fig.update_traces(showlegend=False, row=rw, col=cl)
                        if cl>1:
                            fig.update_yaxes(title = " ", row=rw, col=cl)
                title_input=input(f"{pdos_dir}:What would you like to title this plot?")
                check_input(title_input)
                fig.update_layout(title_text = f'{title_input}')
                save_plot(fig,filename,pdos_dir,w=(cw*150),h=(rw*400),no_show_image=no_show_img)
