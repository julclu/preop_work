#!/usr/bin/env python

import os
import glob
import argparse 
import subprocess as sub
import shlex 
from subprocess import PIPE, Popen
import pandas as pd

## in this script we want to 
## 0. Create the argument parser
## 1. import a single bnum and tnum 
## 2. run the archive_exam perl script on it 
##    e.g archive_exam -e E7641/ --raw_prefix t --study po1_preop_recur
## 3. run dcm_qr perl script on it in its new location 
##

print('creating argument parser')
########### Create an argument parser 
parser = argparse.ArgumentParser(description='In this script we will import a single bnum/tnum, run the archive_exam perl script, and then dcm_qr to desired location.')
parser.add_argument('bnum', type=str, nargs=1, help='Input the b-number of the patient.')
parser.add_argument('tnum', metavar = 'C', type =str, nargs = 1, help = 'Input the t-number of the scan.')
parser.add_argument('--NewLocation', metavar = 'N', default = '/data/RECglioma/archived', type = str, nargs = 1, help = 'New location for your de-identified exam.')
parser.add_argument('--StudyName', metavar = 'S', default = 'po1_preop_recur', type = str, nargs = 1, help = "Study Identifier")
# args = parser.parse_args('b2292 t6929'.split())
args = parser.parse_args()

print('parsing the arg')
########### Create strings of the arguments 
bnum = ''.join(args.bnum)
tnum = ''.join(args.tnum)
newloc = ''.join(args.NewLocation)
studytag = ''.join(args.StudyName)

print('changing path')
########### Function for creating pathname and changing to directory name: 
preop_path_root = "/data/bioe4/po1_preop_recur/"
def change_path(pathname_root):
    pathname = pathname_root+bnum+'/'+tnum
    os.chdir(pathname)
    
change_path(preop_path_root)

########### Use glob to capture the Enum 
Enum = glob.glob('E*')
Enum = Enum[0]

print('differentiating snums in preop Efolder and SNums in archive')
########### ########### ########### ########### ########### ########### ########### ########### 
########### Differentiating Snums in preop E folder and Snums in the archive to see what still 
########### needs to be archived: 
########### ########### ########### ########### ########### ########### ########### ########### 
## in preop: 
series_nums_in_preopEfolder = os.listdir(Enum)
series_nums_in_preopEfolder = [Snum for Snum in series_nums_in_preopEfolder if len(Snum)<3]
## in archive: 
dxit_command = 'dcm_exam_info -'+tnum
print('set dxit command')
dxit_output = sub.check_output(dxit_command, shell=True)
print('executed dxit command')
dxit_lines = dxit_output.decode('utf-8').splitlines()
indices = [i for i, s in enumerate(dxit_lines) if '-----' in s]
indices= indices[0]
indices+=1
dxit_lines = dxit_lines[indices:]
dxit_series_lines = [l.split()[0] for l in dxit_lines]
series_nums_in_archive = [l for l in dxit_series_lines if len(l) < 3]
## difference between series numbers 
series_to_archive = [snum for snum in series_nums_in_preopEfolder if snum not in series_nums_in_archive]
## if series_to_archive is > 1, then we must try to archive the exam; but not if there are other 
## files that begin with t in the folder. Let's find all the files that begin with t. 
## if so, then we must move the files that begin with t to another folder called "moved"
## -----------------------------------------------------------------------------------------------
## moving files beginning with t that re not the spec files to a "moved" folder:
print('moving files beginning w/ t that are not in spec files to a "moved" folder')
files_beginning_with_t = glob.glob('t*')
make_dir = sub.call('mkdir moved', shell = True)
files_ending_with_dat = glob.glob("*.dat")
files_to_move = [file for file in files_beginning_with_t if file != tnum]
files_to_move = [file for file in files_to_move if file not in files_ending_with_dat]
for file in files_to_move: 
    print("moving file"+ file )
    mv_command = 'mv '+file+' moved'
    sub.call(mv_command, shell=True)
## archive the exam (if you need to)
print('archiving exam if we need to')
if len(series_to_archive)>0: 
    print('archiving exam')
    arc_exam_command = 'archive_exam -e '+Enum+' --raw_prefix t '+'--study '+studytag+' -p cjUCSF\!1'
    arc_exam = sub.call(arc_exam_command, shell = True)
    print('done_archiving_exam')

########### ########### ########### ########### ########### ########### ########### ########### ########### 
########### Differentiating Snums in the archive from the Snums that are present in the recgli/archived 
########### folder
########### ########### ########### ########### ########### ########### ########### ########### ###########
## in archive:  
dxit_lines = dxit_output.decode('utf-8').splitlines()
indices = [i for i, s in enumerate(dxit_lines) if '-----' in s]
indices= indices[0]
indices+=1
dxit_lines = dxit_lines[indices:]
dxit_series_lines = [l.split()[0] for l in dxit_lines]
series_nums_in_archive = [l for l in dxit_series_lines if len(l) < 3]
## snums in recgli folder: 
recgli_path_root = '/data/RECglioma/archived/'
os.chdir(recgli_path_root)
## does the bnum already exist in here? if not, stay and pull archive: 
bnums_in_archived = glob.glob('b*')
print('pulling exam from archive')
if bnum in bnums_in_archived: 
    os.chdir(os.path.abspath(bnum))
    os.chdir(os.path.abspath(
    ## find the snums in the folder:
    snums_previously_pulled = os.listdir(Enum)
    snums_to_pull = [series for series in series_nums_in_archive if series not in snums_previously_pulled]
else: 
    snums_to_pull = series_nums_in_archive
os.chdir(recgli_path_root)
for snum in snums_to_pull:
    print('pulling exam series number:'+snum)
    dcm_qr_command = "dcm_qr -"+tnum+" -s "+snum+" -p cjUCSF\!1"
    sub.call(dcm_qr_command, shell=True)



