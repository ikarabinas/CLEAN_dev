import os
import pandas as pd
import configparser
import subprocess

'''
Runs CLEAN batch preprocessing on EEG data

Requires:
    CSV listing participant IDs corresponding to data that needs preprocessing
    Path to the data folder
'''
# Set data paths
eeg_datapath = '/Users/Bella/Desktop/Grosenick_Lab/eeg_data/eeg_patient_data/'
#to_preprocess_datapath = '/athena/grosenicklab/store/tms_eeg/mdd_dlpfc/'
#savepath = '/home/imk2003/Desktop/eeg_data/preprocessed_CLEAN_dev/'
savepath = '/Users/Bella/Desktop/Grosenick_Lab/slurm_and_cluster_scripts/'
subject_list_csv = '/Users/Bella/Desktop/Grosenick_Lab/slurm_and_cluster_scripts/subject_list_test.csv'
#subject_list_csv = '/home/imk2003/Documents/subject_list_short.csv'

# Read participant record_ids from csv
subjects_df = pd.read_csv(subject_list_csv)
ppt_ids = list(subjects_df['record_id'])


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


# Load and modify the config file
def update_config(ppt_id, day, preprocess_path, savepath=savepath):
    config_file = 'test_config.cfg'  # Specify the path to your config file
    config = configparser.ConfigParser()
    config.read(config_file)

    # Update the input_path and results_path in the config file
    config['paths']['input_path'] = preprocess_path
    results_path = os.path.join(savepath, ppt_id, day)
    config['paths']['results_path'] = results_path
    print(f'Cleaned data save path: {results_path}')

    # Write the updated config back to the file
    with open(config_file, 'w') as configfile:
        config.write(configfile)


# Run preprocessing.py with updated config
def run_preprocessing():
    try:
        subprocess.run(['python', 'preprocessing.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f'Error during preprocessing: {e}')


# Run preprocessing for participant IDs in subject_list_csv
for subject in ppt_ids:
    day_paths = get_eeg_daypaths(subject)
    try:
        for day_path in day_paths:
            day = day_path.split('_')[-1]
            print(f'Preprocessing subject {subject}, {day}')
            update_config(subject, day, day_path)
            #run_preprocessing()
            print(f'Completed preprocessing for {subject}, {day}')

    # Exception handling for missing data
    except TypeError:
        continue
