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
# Set save path for cleaned data
savepath = '/athena/grosenicklab/scratch/imk2003/preprocessed_CLEAN_dev/'

# Parse ppt_id and tms_target variables provided by submission script
parser = argparse.ArgumentParser()
parser.add_argument('--ppt_id', required=True)
parser.add_argument('--tms_target', required=True)
args = parser.parse_args()

ppt_id = args.ppt_id
tms_target = args.tms_target.lower()


def define_data_dir(ppt_id, tms_target):
    if ppt_id[0].lower() == 'm':
        diagnosis = 'mdd'
    elif ppt_id[0].lower() == 'c':
        diagnosis = 'ocd'
    else:
        raise ValueError(f'Unrecognized diagnosis prefix in ppt_id: {ppt_id}')

    dir_name = f'{diagnosis}_{tms_target}'
    return os.path.join('/athena/grosenicklab/store/tms_eeg', dir_name)


# Dynamically set EEG data path
eeg_datapath = define_data_dir(ppt_id, tms_target)
print(f'[INFO] ppt_id: {ppt_id}, tms_target: {tms_target}')
print(f'[INFO] eeg data path: {eeg_datapath}')


# Returns a list of paths corresponding to tx day data for the specified partipant
def get_eeg_daypaths(ppt_id):
    subject_day_paths = []

    # Account for ppt_ids with crossover naming
    if 'crossover' in ppt_id:
        subject = ppt_id.split('_')[0]
    else:
        subject = ppt_id

    try:
        # Filter eeg_datapath directories that match the specified participant ID
        ppt_dir = str([folder for folder in os.listdir(eeg_datapath) if subject in folder][0])
        ppt_dir_path = os.path.join(eeg_datapath, ppt_dir)

        # Create a list of directory names within the participant folder and sort in order of days
        ppt_day_data = [folder for folder in os.listdir(ppt_dir_path) if subject in folder and 'day' in folder]
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
    results_path = os.path.join(savepath, f'{ppt_id}_{tms_target}', day)
    config['paths']['results_path'] = results_path
    print(f'Cleaned data save path: {results_path}')

    # Write to a temp config file (unique for each run)
    temp_config = os.path.join(tempfile.gettempdir(), f'{ppt_id}_{day}_config.cfg')
    with open(temp_config, 'w') as configfile:
        config.write(configfile)
    return temp_config


# Run preprocessing.py with updated temp config
def run_preprocessing(config_path):
    try:
        subprocess.run(['python', 'preprocessing.py', '--config', config_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f'[ERROR] Error during preprocessing: {e}')


# Run preprocessing on all resting state data for one participant (ppt_id),
# Looping through days of treatment
day_paths = get_eeg_daypaths(ppt_id)
for day_path in day_paths:
    try:
        # Extract treatment day from path
        match = re.search(r'day\d+', day_path)  # matches 'day1' etc in path name
        if not match:
            print(f'[WARNING] Could not extract tx day info from path: {day_path}')
            continue
        day = match.group()
        print(f'Preprocessing subject {ppt_id}, {day}')

        # Update temp config and run preprocessing
        config_path = update_config(ppt_id, day, day_path)
        run_preprocessing(config_path)
    except Exception as e:
        print(f'[ERROR] Skipping preprocessing for {ppt_id} {day}. Error: {e}')
        continue
