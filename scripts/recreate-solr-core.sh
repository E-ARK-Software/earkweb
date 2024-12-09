#!/bin/bash

# This script automates the re-creation of the solr core.
# It performs the following tasks:
# 1. Prompts the user to provide installation directories and URLs, with default values available.
# 2. Checks for required dependencies (`curl` and `python3`) and ensures they are installed.
# 3. Ensures Solr is running:
#    - Starts Solr only if it is not already running.
# 4. Deletes and recreates the Solr core (`storagecore1`) to ensure a clean state.
# 5. Configures the newly created core:
#    - Enables remote streaming using Solr's REST API.
#    - Copies a pre-configured `solrconfig.xml` from the EarkWeb directory to the Solr core's configuration directory.
# 6. Runs an earkweb initialization script (`init_solr.py`) to finalize core setup.
# 7. Restarts Solr to apply the new configurations.

set -e

# Functions
function log() {
    echo "[INFO] $1"
}

function error_exit() {
    echo "[ERROR] $1" >&2
    exit 1
}

function check_dependency() {
    command -v $1 >/dev/null 2>&1 || error_exit "Required dependency '$1' not found."
}

function prompt_with_default() {
    local prompt_message=$1
    local default_value=$2
    read -p "${prompt_message} [${default_value}]: " input_value
    echo "${input_value:-$default_value}"
}

function start_solr_if_not_running() {
    log "Checking if Solr is running..."
    local solr_status
    solr_status=$("$SOLR_DIR/bin/solr" status 2>/dev/null || true)
    if echo "$solr_status" | grep -q "running"; then
        log "Solr is already running."
    else
        log "Solr is not running. Starting Solr..."
        "$SOLR_DIR/bin/solr" start || error_exit "Failed to start Solr."
    fi
}

# Prompt for Variables
SOLR_DIR=$(prompt_with_default "Enter Solr installation directory (press Enter to use the default)" "/opt/solr/solr-8.4.1")
EARKWEB_DIR=$(prompt_with_default "Enter earkweb installation directory (press Enter to use the default)" "/opt/earkweb")
SOLR_CONF_DIR="${SOLR_DIR}/server/solr/storagecore1/conf"
VENV_DIR=$(prompt_with_default "Enter virtual environment directory" "${EARKWEB_DIR}/venv")
SOLR_URL=$(prompt_with_default "Enter Solr base URL (press Enter to use the default)" "http://localhost:8983/solr")

# Ensure required dependencies are installed
check_dependency "curl"
check_dependency "python3"

# Check directories
[ -d "$SOLR_DIR" ] || error_exit "Solr directory not found: $SOLR_DIR"
[ -d "$EARKWEB_DIR" ] || error_exit "EarkWeb directory not found: $EARKWEB_DIR"

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    log "Activating virtual environment..."
    source "${VENV_DIR}/bin/activate"
else
    error_exit "Virtual environment not found in $VENV_DIR. Please create it first \
(using 'python3 -m venv $VENV_DIR') and install the Python dependencies \
(using 'pip3 install -r $EARKWEB_DIR/requirements.txt')."
fi

# Start Solr if not already running
start_solr_if_not_running

# Delete storagecore1
log "Deleting storagecore1 core (if exists)..."
"$SOLR_DIR/bin/solr" delete -c storagecore1 || log "Core storagecore1 does not exist, skipping delete."

# Create new storagecore1
log "Creating storagecore1 core..."
"$SOLR_DIR/bin/solr" create -c storagecore1

# Enable remote streaming
log "Enabling remote streaming for storagecore1..."
curl -s "${SOLR_URL}/storagecore1/config" \
     -H 'Content-type:application/json' \
     -d '{
         "set-property": {
             "requestDispatcher.requestParsers.enableRemoteStreaming": true,
             "requestDispatcher.requestParsers.enableStreamBody": true
         }
     }' || error_exit "Failed to configure remote streaming."

# Copy Solr configuration
log "Copying solrconfig.xml from EarkWeb to Solr storagecore1..."
cp "${EARKWEB_DIR}/config/solrconfig.xml" "${SOLR_CONF_DIR}/solrconfig.xml" || error_exit "Failed to copy solrconfig.xml."


# Run initialization script
log "Running Solr initialization script..."
cd "${EARKWEB_DIR}/scripts/"
python3 init_solr.py || error_exit "Failed to run init_solr.py."

# Restart Solr
log "Restarting Solr..."
"$SOLR_DIR/bin/solr" stop
"$SOLR_DIR/bin/solr" start

log "Script completed successfully."
