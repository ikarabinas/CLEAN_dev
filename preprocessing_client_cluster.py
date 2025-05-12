import os
import configparser
import subprocess
import argparse
import re
import tempfile

'''
Runs CLEAN batch preprocessing of all EEG data from one participant
Can be used in conjunction with a SLURM submission script for parallel processing of participant data
'''
# Set data paths
# Change eeg_datapath to reflect tms_target: mdd_dlpfc, mdd_dmpfc, ocd_dmpfc, ocd_rofc, ocd_lofc, ocd_dlpfc
eeg_datapath = '/athena/grosenicklab/store/tms_eeg/mdd_dlpfc/'
savepath = '/home/imk2003/Desktop/eeg_data/preprocessed_CLEAN_dev/'

# Parse ppt_id variable provided by submission script
parser = argparse.ArgumentParser()
parser.add_argument('--ppt_id', required=True)
args = parser.parse_args()
ppt_id = args.ppt_id


# Returns a list of paths corresponding to tx day data for the specified partipant
def get_eeg_daypaths(ppt_id):
    subject_day_paths = []
    try:
        # Filter eeg_datapath directories that match the specified participant ID
        ppt_dir = str([folder for folder in os.listdir(eeg_datapath) if ppt_id in folder][0])
        ppt_dir_path = os.path.join(eeg_datapath, ppt_dir)

        # Create a list of directory names within the participant folder and sort in order of days
        ppt_day_data = [folder for folder in os.listdir(ppt_dir_path) if ppt_id in folder and 'day' in folder]
        ppt_day_data.sort(key=lambda x: x.split('_')[-1])  # selects 'dayx' portion of dir name for sorting

        for day_dir in ppt_day_data:
            day_dir = str(day_dir)
            day_path = os.path.join(eeg_datapath, ppt_dir, day_dir)
            subject_day_paths.append(day_path)
        return subject_day_paths

    except IndexError:
        print(f'No data directory found for ppt_id {ppt_id} in {eeg_datapath}')


# Load the config file and modify a temp config file for each parallel run
def update_config(ppt_id, day, preprocess_path, savepath=savepath):
    base_config = 'test_config.cfg'
    config = configparser.ConfigParser()
    config.read(base_config)

    config['paths']['input_path'] = preprocess_path
    results_path = os.path.join(savepath, ppt_id, day)
    config['paths']['results_path'] = results_path
    print(f'Cleaned data save path: {results_path}')

    # Write to a temp config file (unique for each run)
    temp_config = os.path.join(tempfile.gettempdir(), f'{ppt_id}_{day}_config.cfg')
    with open(temp_config, 'w') as configfile:
        config.write(configfile)
    return temp_config


# Run preprocessing.py with updated config
def run_preprocessing():
    try:
        subprocess.run(['python', 'preprocessing.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error during preprocessing: {e}')


# Run preprocessing on all resting state data for one participant (ppt_id),
# Looping through days of treatment
day_paths = get_eeg_daypaths(ppt_id)
for day_path in day_paths:
    try:
        day_regex_matching = lambda x: re.search(r'day\d+', x).group() if re.search(r'day\d+', x) else None
        day = day_regex_matching(day_path)
        print(f'Preprocessing subject {ppt_id}, {day}')
        update_config(ppt_id, day, day_path)
        run_preprocessing()
        print(f'Completed preprocessing for {ppt_id}, {day}')

    # Exception handling for missing data
    except TypeError as e:
        print(e)
        continue
