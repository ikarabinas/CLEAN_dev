#!/bin/bash
# Batch preprocess EEG with CLEAN pipeline for a list of participant IDs

SUBJECT_LIST="/home/imk2003/Documents/subject_list_test.csv"
PREPROCESSING_CLIENT_SCRIPT="/home/imk2003/Documents/GitHub/CLEAN_dev/preprocessing_client_cluster.py"
SAVEPATH="/home/imk2003/Desktop/eeg_data/preprocessed_CLEAN_dev/"
LOG_DIR="/home/imk2003/Desktop/eeg_data/preprocessed_CLEAN_dev/logs/"
TRACKING_FILE="clean_preprocessing_job_tracking.tsv"

# Modify to filter for treatment target: DLPFC, DMPFC, ROFC, LOFC (case sensitive)
TMS_TARGET="DLPFC"

# Set to true to simulate submission without running sbatch
DRY_RUN=true 

mkdir -p "$LOG_DIR"
echo -e "subject_id\tjob_id\ttimestamp" > "$TRACKING_FILE"

# Read and filter subjects
csvcut -c 2,5 "$SUBJECT_LIST" | tail -n +2 | while IFS=',' read -r subject_id tms_target; do
    subject_id=$(echo "$subject_id" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    tms_target=$(echo "$tms_target" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Skip entries with blank record_id or tms_target
    if [ -z "$subject_id" ] || [ -z "$tms_target" ]; then
        continue

    fi

    # Skip already-processed subjects
    if [ -d "${SAVEPATH}/${subject_id}" ]; then
        echo "Skipping ${subject_id}, already exists in 'eeg_data/preprocessed_CLEAN_dev'."
        continue
    fi

    # Build SLURM command. Allocate 16G of memory and 4 CPU cores per subject.
    SLURM_CMD="sbatch --mem=16G --cpus-per-task=4 \
        --job_name=clean_{subject_id} \
        --partition=sackler-cpu,scu-cpu \
        --time=12:00:00 \
        --output=${LOG_DIR}/${subject_id}_%j.out \
        --error=${LOG_DIR}/${subject_id}_%j.err \
        --wrap=\"python ${PREPROCESSING_CLIENT_SCRIPT} --ppt_id ${subject_id}\""

    # Submit job or test with dry run
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would submit: $SLURM_CMD"
    else
        job_output=$(eval "$SLURM_CMD")

        # Job tracking
        if [[ "$job_output" != Submitted* ]]; then
            echo "ERROR submitting ${subject_id}. sbatch said: $job_output"
            continue
        fi

        job_id=$(echo "$job_output" | awk '{print $4}')
        timestamp=$(date +"%Y-%m-%d %H:%M:%S")
        echo -e "${subject_id}\t${job_id}\t${timestamp}" >> "$TRACKING_FILE"
        echo "Submitted ${subject_id} as Job ${job_id}"
    fi

done
