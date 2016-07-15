#!/usr/bin/env bash

# Vincent Dowling
# Watson Ecosystem
#
# usage: bin/bash/experiment.sh <path_to_experiment_cfg> <path_to_experiment_directory>
# description: Given an experiment configuration file and an output directory, this script runs a test file
#   through a script that writes the output of that scripts to a relevance file

# PARAMETER: <path_to_python_script>, <base_url>, <username>, <password>, <cluster_id>
# Exits if it doesn't exist
cluster_exists_and_is_ready () {
    local PRINT_CLUSTER_INFO_SCRIPT=$1
    file_exists $PRINT_CLUSTER_INFO_SCRIPT
    CLUSTER_STATE=$(python $PRINT_CLUSTER_INFO_SCRIPT $2 $3 $4 $5)
    if [[ "$CLUSTER_STATE" != "READY" ]]; then
        echo "[unix] Solr Cluster with URL=$2, USERNAME=$3, PASSWORD=$4, CLUSTER_ID=$5 does not exist or is not ready"
        echo "[unix] Exiting with status code 1"
        exit 1
    fi
}


# PARAMETER: <path_to_python_script>, <base_url>, <username>, <password>, <ranker_id>
# Tests whether the ranker exists and is available
ranker_exists_and_is_available () {

    # Get the ranker status
    local PRINT_RANKER_INFO_SCRIPT=$1
    file_exists $PRINT_RANKER_INFO_SCRIPT
    RANKER_STATUS=$(python $1 $2 $3 $4 $5)

    # Exit if status is not available
    if [[ "$RANKER_STATUS" != "Available" ]]; then
        if [[ "$RANKER_STATUS" = "FAILED" ]]; then
            echo "[unix] Could not resolve status for ranker with URL=$2, USERNAME=$3, PASSWORD=$4, RANKER_ID=$5"
        else
            echo "[unix] Ranker with URL=$2, USERNAME=$3, PASSWORD=$4, RANKER_ID=$5 has status=$RANKER_STATUS"
        fi
        echo "[unix] Exiting with status code 1"
        exit 1
    fi
}

# Exit if a variable does not exist
variable_exists () {
    local VARIABLE_NAME=$1
    local VARIABLE=$2
    if [ ! -n "$VARIABLE_NAME" ]; then
        echo "[unix] No variable name passed in..."
    fi
    if [ ! -n "$VARIABLE" ]; then
        echo "[unix] variable=$VARIABLE_NAME does not exists. Usage : bin/bash/experiment.sh <path_to_experiment_cfg> <path_to_experiment_directory>. Exiting with status code 1"
        exit 1
    fi
}


# Source the config file and check to see that the expected variables exist
source_config_file () {
    local CFG_FILE=$1
    variable_exists "CONFIG_FILE" $CFG_FILE
    file_exists $CFG_FILE
    source $CFG_FILE
    variable_exists "RETRIEVE_AND_RANK_BASE_URL" $RETRIEVE_AND_RANK_BASE_URL
    variable_exists "RETRIEVE_AND_RANK_USERNAME" $RETRIEVE_AND_RANK_USERNAME
    variable_exists "RETRIEVE_AND_RANK_PASSWORD" $RETRIEVE_AND_RANK_PASSWORD
    variable_exists "SOLR_CLUSTER_ID" $SOLR_CLUSTER_ID
    variable_exists "SOLR_COLLECTION_NAME" $SOLR_COLLECTION_NAME
    variable_exists "RANKER_ID" $RANKER_ID
    variable_exists "TEST_RELEVANCE_FILE" $TEST_RELEVANCE_FILE
    file_exists $TEST_RELEVANCE_FILE
}


# Exits if the first argument doesn't point to an existing file
file_exists () {
    local FILE=$1
    if [ ! -e $FILE ]; then
        echo "[unix] file=$FILE does not exist. Usage : bin/bash/experiment.sh <path_to_experiment_cfg> <path_to_experiment_directory>"
        exit 1
    fi
}


# Exits if the first argument doesn't point to an existing directory
directory_exists () {
    local DIR_NAME=$1
    if [ ! -d "$DIR_NAME" ]; then
        echo "[unix] directory=$DIR_NAME does not exist. Usage : bin/bash/experiment.sh <path_to_experiment_cfg> <path_to_experiment_directory>"
        exit 1
    fi
}


# Prompt for a variable
prompt_for_variable () {
    echo $1
    read $2
}


# Preliminaries
echo "[unix] Starting script experiment.sh..."
set -e


# Validate contents in the binary directory
BIN_DIRECTORY=bin
PYTHON_DIRECTORY=$BIN_DIRECTORY/python
PRINT_CLUSTER_INFO_SCRIPT=$PYTHON_DIRECTORY/print_solr_cluster_status.py
PRINT_RANKER_STATUS_INFO_SCRIPT=$PYTHON_DIRECTORY/print_ranker_status.py
PRINT_OBJECT_SCRIPT=$PYTHON_DIRECTORY/print_json_object.py
TEST_SCRIPT=$PYTHON_DIRECTORY/test.py
directory_exists $BIN_DIRECTORY
directory_exists $PYTHON_DIRECTORY
file_exists $PRINT_CLUSTER_INFO_SCRIPT
file_exists $PRINT_RANKER_STATUS_INFO_SCRIPT
file_exists $PRINT_OBJECT_SCRIPT
file_exists $TEST_SCRIPT


# Validate command line arguments
CFG_FILE=$1
DATA_DIRECTORY=$2
CONTENT_FILE=$DATA_DIRECTORY/content.json
source_config_file $CFG_FILE
cluster_exists_and_is_ready $PRINT_CLUSTER_INFO_SCRIPT $RETRIEVE_AND_RANK_BASE_URL $RETRIEVE_AND_RANK_USERNAME \
    $RETRIEVE_AND_RANK_PASSWORD $SOLR_CLUSTER_ID
ranker_exists_and_is_available $PRINT_RANKER_STATUS_INFO_SCRIPT $RETRIEVE_AND_RANK_BASE_URL $RETRIEVE_AND_RANK_USERNAME \
    $RETRIEVE_AND_RANK_PASSWORD $RANKER_ID
directory_exists $DATA_DIRECTORY


# Run Retrieve and Rank experiment only
SOLR_EXPERIMENT_FILE=$DATA_DIRECTORY/exp_solr_only.json
echo "-----------------------------------"
echo "[unix] Running Solr experiment with cluster_id=$SOLR_CLUSTER_ID, collection_name=$SOLR_COLLECTION_NAME"
python $TEST_SCRIPT --username=$RETRIEVE_AND_RANK_USERNAME --password=$RETRIEVE_AND_RANK_PASSWORD --url=$RETRIEVE_AND_RANK_BASE_URL \
    --collection-name=$SOLR_COLLECTION_NAME --cluster-id=$SOLR_CLUSTER_ID --relevance-file=$TEST_RELEVANCE_FILE \
    --output-file=$SOLR_EXPERIMENT_FILE --fl=id,title,subtitle,answer,answerScore --debug
echo "[unix] Finished running solr experiment. Experiment results saved to $SOLR_EXPERIMENT_FILE"


# Run Solr experiment only
RR_EXPERIMENT_FILE=$DATA_DIRECTORY/exp_retrieve_and_rank.json
echo "-----------------------------------"
echo "[unix] Running R&R experiment with cluster_id=$SOLR_CLUSTER_ID, collection_name=$SOLR_COLLECTION_NAME, ranker_id=$RANKER_ID"
python $TEST_SCRIPT --username=$RETRIEVE_AND_RANK_USERNAME --password=$RETRIEVE_AND_RANK_PASSWORD --url=$RETRIEVE_AND_RANK_BASE_URL \
    --collection-name=$SOLR_COLLECTION_NAME --cluster-id=$SOLR_CLUSTER_ID --relevance-file=$TEST_RELEVANCE_FILE \
    --output-file=$RR_EXPERIMENT_FILE --fl=id,title,subtitle,answer,answerScore --debug \
    --ranker-id=$RANKER_ID
echo "[unix] Finished running R&R experiment. Experiment results saved to $RR_EXPERIMENT_FILE"


# Exit
echo "-----------------------------------"
echo "[unix] Exiting with status code 0"
exit 0
