#!/bin/bash

# Script to automate the installation of earkweb and its dependencies

set -e  # Exit on any error

# Define variables
USER="${USER}"
GROUP="${GROUP}"

# supervisor configuration
SUPERVISOR_CONFIG_DIR=/etc/supervisor/conf.d/

# Colours for terminal messages
HEADER="\e[34m"
OKGREEN="\e[92m"
WARN="\e[93m"
FAIL="\e[91m"
ENDC="\e[0m"

function echo_highlight() {
    echo -e "$1$2$ENDC"
}

function echo_highlight_header()
{
    echo -e "$1==========================================================="
    echo -e "$2"
    echo -e "===========================================================$ENDC"
}

function log() {
    echo "[INFO] $1"
}

function error_exit() {
    echo_highlight $FAIL "[ERROR] $1" >&2
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
# Function to check if Solr is available
check_solr() {
    curl --silent --fail "$SOLR_URL" > /dev/null
}


function start_solr_if_not_running() {
    log "Checking if Solr is running..."
    local solr_status
    solr_status=$("$SOLR_DIR/bin/solr" status 2>/dev/null || true)

    # Check if the status explicitly says "No Solr nodes are running"
    if echo "$solr_status" | grep -q "No Solr nodes are running"; then
        log "Solr is not running. Starting Solr..."
        "$SOLR_DIR/bin/solr" start || error_exit "Failed to start Solr."
    elif echo "$solr_status" | grep -q "Found .* Solr nodes"; then
        echo_highlight $OKGREEN "Solr is already running."
    else
        echo_highlight $WARN "Unable to determine Solr status. Attempting to start Solr..."
        "$SOLR_DIR/bin/solr" start || error_exit "Failed to start Solr."
    fi
}

# Prompt user for confirmation
confirm_solr_core_deletion() {
    local core_name=$1
    read -p "Do you want to delete the core '$core_name'? (y/N): " response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0  # Confirmed
            ;;
        *)
            return 1  # Declined
            ;;
    esac
}

function confirm_with_key() {
    local prompt_message=$1
    echo -e -n "${prompt_message}(Press 'y' to confirm, any other key to skip this step):\n"
    read -n1 -s input  # Read a single keypress silently (-s for no echo)
    echo  # Print a new line for cleaner output
    if [[ "$input" == "y" || "$input" == "Y" ]]; then
        return 0  # Confirmed
    else
        return 1  # Canceled
    fi
}

# Function to prompt for a target directory
function prompt_target_directory() {
    local default_dir="/opt"
    read -p "Enter the target directory for installation [${default_dir}]: " target_dir
    echo "${target_dir:-$default_dir}"
}

# Function to set ownership and permissions
function set_permissions() {
    local dir=$1
    local user=$2
    local group=$3

    if [[ ! -d "$dir" ]]; then
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    fi

    echo "Setting ownership of $dir to $user:$group"
    sudo chown -R "$user:$group" "$dir"
}

# Check if the script is run from the correct directory
check_directory() {
    local current_dir
    current_dir=$(pwd)

    # Define the expected files
    local earkweb_module="earkweb"
    local settings_file="settings/settings.cfg.default"

    # Check for the presence of the expected files
    if [[ ! -f "$current_dir/$settings_file" ]]; then
        log "Error: Missing $settings_file in the current directory."
        return 1
    fi

    if [[ ! -d "$current_dir/$earkweb_module" ]]; then
        log "Error: Missing $earkweb_module module in the current directory."
        return 1
    fi

    # If checks pass, set EARKWEB_DIR to the current directory of the script
    EARKWEB_DIR=$current_dir
    echo "EARKWEB_DIR set to: $EARKWEB_DIR"
    return 0
}

# Update system and install dependencies
echo_highlight_header $HEADER 'System dependencies'
if confirm_with_key "The system requires the following system packages:\npython3 python3-dev python3-pip python3-virtualenv \
build-essential default-libmysqlclient-dev libmysqlclient-dev libicu-dev gettext default-jre \
curl gnupg apt-transport-https mysql-server redis-server\nDo you want to install the system packages (sudo required)?\n"; then
    echo "Proceeding with installing system dependencies with apt-get..."
    sudo apt-get update -y && sudo apt-get upgrade -y
    sudo apt-get install -y python3 python3-dev python3-pip python3-virtualenv \
      build-essential default-libmysqlclient-dev libmysqlclient-dev libicu-dev gettext default-jre \
      curl gnupg apt-transport-https mysql-server redis-server
    echo_highlight $OKGREEN "Installing dependencies completed"
else
    echo_highlight $WARN "installing system dependencies skipped."
fi

# Installing earkweb
echo_highlight_header $HEADER 'Installing earkweb'
if confirm_with_key "Do you want to proceed with installing earkweb?\n"; then
    echo "Proceeding with installing earkweb..."
    
    # Ensure the user is in the correct directory
    if ! check_directory; then
        echo_highlight $FAIL "Please ensure you are running this script from within the cloned 'earkweb' repository."
        exit 1
    fi

    # Path to the settings file
    EARKWEB_SETTINGS_FILE="settings/settings.cfg"
    EARKWEB_SETTINGS_PATH="$EARKWEB_DIR/$EARKWEB_SETTINGS_FILE"

    # Set ownership fallback to current user and group
    DESIRED_USER="${USER}"  # Default to the current logged-in user
    DESIRED_GROUP="$(id -gn)"  # Get the current user's primary group
    echo "Using ownership: ${DESIRED_USER}:${DESIRED_GROUP}"

    # Prompt for Variables
    LOG_DIR=$(prompt_with_default "Enter earkweb log directory (press Enter to use the default)" "/var/log/earkweb")
    CELERY_LOG_DIR=$(prompt_with_default "Enter celery log directory (press Enter to use the default)" "/var/log/celery")
    STORAGE_DIR=$(prompt_with_default "Enter earkweb storage directory (press Enter to use the default)" "/var/data/repo/storage")
    WORK_DIR=$(prompt_with_default "Enter earkweb work directory (press Enter to use the default)" "/var/data/repo/work")
    RECEPTION_DIR=$(prompt_with_default "Enter earkweb reception directory (press Enter to use the default)" "/var/data/repo/reception")
    ACCESS_DIR=$(prompt_with_default "Enter earkweb access directory (press Enter to use the default)" "/var/data/repo/access")

    # Setup Python virtual environment
    virtualenv -p python3 venv
    source venv/bin/activate

    # Install Python packages
    pip install --upgrade pip
    pip install -r requirements.txt

    # Create required directories and set permissions
    sudo mkdir -p $LOG_DIR
    set_permissions "$LOG_DIR" "$DESIRED_USER" "$DESIRED_GROUP"
    sudo mkdir -p $CELERY_LOG_DIR
    set_permissions "$CELERY_LOG_DIR" "$DESIRED_USER" "$DESIRED_GROUP"
    sudo mkdir -p $STORAGE_DIR/pairtree_root
    set_permissions "$STORAGE_DIR" "$DESIRED_USER" "$DESIRED_GROUP"
    sudo touch $STORAGE_DIR/pairtree_version0_1
    sudo mkdir -p $WORK_DIR
    set_permissions "$WORK_DIR" "$DESIRED_USER" "$DESIRED_GROUP"
    sudo mkdir -p $RECEPTION_DIR
    set_permissions "$RECEPTION_DIR" "$DESIRED_USER" "$DESIRED_GROUP"
    sudo mkdir -p $ACCESS_DIR
    set_permissions "$ACCESS_DIR" "$DESIRED_USER" "$DESIRED_GROUP"

    # Copy default settings and configure settings file
    cp ${EARKWEB_SETTINGS_FILE}.default ${EARKWEB_SETTINGS_FILE}

    # Generate localized messages
    ./locale/makemessages.sh
    
    STATIC_ROOT_TARGET=$(prompt_with_default "Enter static root web server target directory (press Enter to use the default)" "/var/www/data")
    STATIC_ROOT=$STATIC_ROOT_TARGET/earkwebstatic/
    sudo mkdir -p $STATIC_ROOT
    set_permissions "$STATIC_ROOT" "$DESIRED_USER" "$DESIRED_GROUP"

    # Collect static files
    python manage.py collectstatic --noinput
    
    MEDIA_ROOT_TARGET=$(prompt_with_default "Enter media root web server target directory (press Enter to use the default)" "/var/www/html")
    MEDIA_ROOT=$STATIC_ROOT_TARGET/media/
    sudo mkdir -p $MEDIA_ROOT
    set_permissions "$MEDIA_ROOT" "$DESIRED_USER" "$DESIRED_GROUP"
 
    # Adapt earkweb configuration
    echo_highlight_header $HEADER 'Adapt earkweb configuration'
    if confirm_with_key "Do you want to proceed with adapting the earkweb configuration ($EARKWEB_SETTINGS_PATH)?\n"; then
        echo "Proceeding with adapting the earkweb configuration ($EARKWEB_SETTINGS_PATH)..."
        # Check if the settings file exists
        if [[ ! -f "$EARKWEB_SETTINGS_PATH" ]]; then
            echo_highlight $FAIL "Error: Settings file not found at $EARKWEB_SETTINGS_PATH"
            exit 1
        fi

        # Update the settings file using sed
        sed -i "s|^\(config_path_storage\s*=\s*\).*|\1$STORAGE_DIR|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(config_path_work\s*=\s*\).*|\1$WORK_DIR|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(config_path_reception\s*=\s*\).*|\1$RECEPTION_DIR|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(config_path_access\s*=\s*\).*|\1$ACCESS_DIR|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(logfile_ui\s*=\s*\).*|\1$LOG_DIR/ui.log|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(logfile_request\s*=\s*\).*|\1$LOG_DIR/request.log|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(logfile_celery\s*=\s*\).*|\1$CELERY_LOG_DIR/request.log|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(logfile_celery_proc\s*=\s*\).*|\1$CELERY_LOG_DIR/logfile_celery_proc.log|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(static_root\s*=\s*\).*|\1$STATIC_ROOT|" "$EARKWEB_SETTINGS_PATH"
        sed -i "s|^\(media_root\s*=\s*\).*|\1$MEDIA_ROOT|" "$EARKWEB_SETTINGS_PATH"

        echo "Settings file $EARKWEB_SETTINGS_PATH updated:"
        echo " - config_path_storage: $STORAGE_DIR"
        echo " - config_path_work: $WORK_DIR"
        echo " - config_path_reception: $RECEPTION_DIR"
        echo " - config_path_access: $ACCESS_DIR"
        echo " - logfile_ui: $LOG_DIR/ui.log"
        echo " - logfile_celery: $LOG_DIR/request.log"
        echo " - logfile_celery_proc: $LOG_DIR/logfile_celery_proc.log"
        echo " - static_root: $STATIC_ROOT"
        echo " - media_root: $MEDIA_ROOT"
        echo_highlight $OKGREEN "Adapting earkweb configuration completed"

    else
        echo_highlight $WARN "Adapting earkweb settings skipped."
    fi

    echo_highlight_header $HEADER 'Installing and configuring supervisor'
    if confirm_with_key "Do you want to install and configure supervisor (sudo required)?\n"; then
        echo "Proceeding with installing supervisor..."
        sudo apt update
        sudo apt install supervisor
        sudo systemctl enable supervisor
        sudo systemctl start supervisor
        # Ensure the user is in the correct directory
        if ! check_directory; then
            echo_highlight $FAIL "Please ensure you are running this script from within the cloned 'earkweb' repository."
            exit 1
        fi
        if [[ ! -d "$current_dir/$earkweb_module" ]]; then
            echo_highlight $FAIL "Error: Supervisor configuration not found at: $SUPERVISOR_CONFIG_DIR"
            return 1
        fi
        # Set ownership fallback to current user and group
        DESIRED_USER="${USER}"  # Default to the current logged-in user
        DESIRED_GROUP="$(id -gn)"  # Get the current user's primary group
        echo "Using ownership: ${DESIRED_USER}:${DESIRED_GROUP}"
        
        MODULES_TO_UPDATE=(
            "earkweb"
            "celery"
            "beat"
            "flower"
        )
        log "Updating supvervisor configuration files"
        for module in "${MODULES_TO_UPDATE[@]}"; do
            # copy config file
            sudo cp $EARKWEB_DIR/config/supervisor/$module.conf $SUPERVISOR_CONFIG_DIR
            # update file
            FILE_TO_UPDATE="${SUPERVISOR_CONFIG_DIR}$module.conf"
            sudo sed -i "s|^\(directory\s*=\s*\).*|\1$EARKWEB_DIR|" "$FILE_TO_UPDATE"
            sudo sed -i "s|^\(command\s*=\s*\)/opt/earkweb|\1$EARKWEB_DIR|" "$FILE_TO_UPDATE"
            sudo sed -i "s|^\(user\s*=\s*\).*|\1$DESIRED_USER|" "$FILE_TO_UPDATE"
            sudo sed -i "s|^\(group\s*=\s*\).*|\1$DESIRED_GROUP|" "$FILE_TO_UPDATE"
            sudo sed -i "s|^\(stdout_logfile\s*=\s*\).*|\1$LOG_DIR/$module.log|" "$FILE_TO_UPDATE"
            sudo sed -i "s|^\(stderr_logfile\s*=\s*\).*|\1$LOG_DIR/$module.err|" "$FILE_TO_UPDATE"
        done

        log "Re-read supervisor configuration"
        sudo supervisorctl reread
        sudo supervisorctl update
    else
        echo_highlight $WARN "Supervisor installation skipped."
    fi

    # creating directory for uwsgi pidfile
    sudo mkdir -p /var/run/uwsgi/earkweb/
    sudo chown ${DESIRED_USER}:${DESIRED_GROUP} /var/run/uwsgi/earkweb

    echo_highlight $OKGREEN "Installing earkweb completed"
else
    echo_highlight $WARN "Installation of earkweb skipped."
fi

# Setting up and initialising the mysql database
echo_highlight_header $HEADER 'Setting up and initialising the mysql database'
if confirm_with_key "Do you want to proceed with setting up and initialising the mysql database (sudo required)?\n"; then
    echo "Proceeding with setting up and initialising the mysql database..."
    # Set up MySQL database
    sudo systemctl start mysql
    sudo mysql <<EOF
CREATE USER 'repo'@'%' IDENTIFIED BY 'repo';
CREATE DATABASE repodb;
ALTER DATABASE repodb CHARACTER SET utf8 COLLATE utf8_general_ci;
GRANT ALL ON repodb.* TO 'repo'@'%';
EOF

    # Initialize database tables
    cd $EARKWEB_DIR
    python manage.py makemigrations earkweb
    python manage.py migrate

    # Create superuser
    python manage.py createsuperuser

    # Generate admin token
    python manage.py shell <<EOF
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
u = User.objects.get(pk=1)
token = Token.objects.create(user=u)
token.save()
print(f"Generated token for admin user: {token.key}")
EOF
    echo_highlight $OKGREEN "Setting up and initialising the mysql database completed"
else
    echo_highlight $WARN "Setting up and initialising the mysql database skipped."
fi

# Installing RabbitMQ and Redis
echo_highlight_header $HEADER 'Installing RabbitMQ and Redis'
if confirm_with_key "Do you want to proceed  with installing RabbitMQ and Redis (sudo required)?\n"; then
    echo "Proceeding with installing RabbitMQ and Redis..."
    # Install RabbitMQ
    # Add repository keys
    curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | sudo gpg --dearmor -o /usr/share/keyrings/com.rabbitmq.team.gpg
    curl -1sLf "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf77f1eda57ebb1cc" | sudo gpg --dearmor -o /usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg
    curl -1sLf "https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey" | sudo gpg --dearmor -o /usr/share/keyrings/io.packagecloud.rabbitmq.gpg

    # Add repositories
    sudo tee /etc/apt/sources.list.d/rabbitmq.list <<EOF

deb [signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu jammy main
deb [signed-by=/usr/share/keyrings/io.packagecloud.rabbitmq.gpg] https://packagecloud.io/rabbitmq/rabbitmq-server/ubuntu/ jammy main
EOF

    # Update and install RabbitMQ
    sudo apt-get update -y
    sudo apt-get install -y erlang-base erlang-asn1 erlang-crypto erlang-eldap \
      erlang-ftp erlang-inets erlang-mnesia erlang-os-mon erlang-parsetools \
      erlang-public-key erlang-runtime-tools erlang-snmp erlang-ssl \
      erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl rabbitmq-server

    # Start RabbitMQ service
    sudo systemctl start rabbitmq-server
    sudo systemctl enable rabbitmq-server

    # Start Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    echo_highlight $OKGREEN "Installation of RabbitMQ and Redis completed"
else
    echo_highlight $WARN "Installation of RabbitMQ and Redis skipped."
fi

# Installing Solr
echo_highlight_header $HEADER 'Installing Solr'
if confirm_with_key "Do you want to proceed with installing solr (sudo required)?\n"; then
    echo "Proceeding with installing solr..."

    # Prompt for Variables
    SOLR_VERSION="8.4.1"
    SOLR_DIST_FILE=solr-$SOLR_VERSION.tgz
    #SOLR_DIST_URL=http://archive.apache.org/dist/lucene/solr/${SOLR_VERSION}/solr-${SOLR_VERSION}.tgz
    SOLR_DIST_URL=https://earkweb.sydarkivera.se/$SOLR_DIST_FILE
    CORE_NAME="storagecore1"
    SOLR_TARGET_DIR=$(prompt_with_default "Enter Solr installation directory (press Enter to use the default)" "/opt/solr")
    SOLR_DIR="${SOLR_TARGET_DIR}/solr-$SOLR_VERSION"
    SOLR_CONF_DIR="${SOLR_DIR}/server/solr/${CORE_NAME}/conf"
    SOLR_URL=$(prompt_with_default "Enter Solr base URL (press Enter to use the default)" "http://localhost:8983/solr")

    # Ensure the user is in the correct directory
    if ! check_directory; then
    	echo_highlight $FAIL "Please ensure you are running this script from within the cloned 'earkweb' repository."
    	exit 1
    fi
    VENV_DIR="${EARKWEB_DIR}/venv"

    # Ensure required dependencies are installed
    check_dependency "curl"
    check_dependency "python3"

    # Set ownership fallback to current user and group
    DESIRED_USER="${USER}"  # Default to the current logged-in user
    DESIRED_GROUP="$(id -gn)"  # Get the current user's primary group
    echo "Using ownership: ${DESIRED_USER}:${DESIRED_GROUP}"

    # create directory, set permissions and change to solr directory
    echo "creating directory $SOLR_TARGET_DIR ..."    
    sudo mkdir -p $SOLR_TARGET_DIR
    set_permissions "$SOLR_TARGET_DIR" "$DESIRED_USER" "$DESIRED_GROUP"
    cd $SOLR_TARGET_DIR

    echo "downloading solr and unpacking it ..."    
    # download solr and unpack it
 
    # Check if the file already exists
    if [ -f "$SOLR_DIST_FILE" ]; then
        echo "File '$SOLR_DIST_FILE' already exists in the current directory. Skipping download."
    else
        echo "File '$SOLR_DIST_FILE' not found. Downloading..."
        wget "$SOLR_DIST_URK" || { echo_highlight $FAIL "Failed to download $FILE_NAME"; exit 1; }
        echo_hightlight $OKGREEN "Download complete."
    fi
    tar -xzvf solr-${SOLR_VERSION}.tgz
    
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

    # check java installation
    if command -v java &> /dev/null; then
        echo_highlight $OKGREEN "Java is installed."
        java -version
    else
        echo_highlight $FAIL "Java is NOT installed."
	exit
    fi
    # Start Solr if not already running
    start_solr_if_not_running

    # Track start time
    START_TIME=$(date +%s)

    # Time to wait before retrying (in seconds)
    WAIT_TIME=5
    
    # # Timeout in seconds (adjust as needed, e.g., 120 seconds)
    TIMEOUT=60

    # Wait for Solr to become available
    echo "Waiting for Solr to become available..."
    while ! check_solr; do
        CURRENT_TIME=$(date +%s)
        ELAPSED_TIME=$((CURRENT_TIME - START_TIME))
	# Break if timeout is reached
        if [ "$ELAPSED_TIME" -ge "$TIMEOUT" ]; then
	    echo_highlight $FAIL "Timeout reached! Solr did not become available after ${TIMEOUT} seconds."
	    exit 1
	fi
	echo "Solr is not yet available. Retrying in $WAIT_TIME seconds... (Elapsed: ${ELAPSED_TIME}s)"
	sleep "$WAIT_TIME"
    done
    echo_highlight $OKGREEN "Solr is now available!"


    # Delete storagecore1, ask for confirmation
    if confirm_solr_core_deletion "$CORE_NAME"; then
        log "Deleting $CORE_NAME core (if exists)..."
        "$SOLR_DIR/bin/solr" delete -c "$CORE_NAME" || log "Core $CORE_NAME does not exist, skipping delete."
    else
        log "Skipping deletion of $CORE_NAME."
    fi

    # Create new storagecore1
    log "Creating ${CORE_NAME} core..."
    "$SOLR_DIR/bin/solr" create -c ${CORE_NAME}

    # Enable remote streaming
    log "Enabling remote streaming for ${CORE_NAME}..."
    curl -s "${SOLR_URL}/${CORE_NAME}/config" \
        -H 'Content-type:application/json' \
        -d '{
            "set-property": {
                "requestDispatcher.requestParsers.enableRemoteStreaming": true,
                "requestDispatcher.requestParsers.enableStreamBody": true
            }
        }' || error_exit "Failed to configure remote streaming."

    # Copy Solr configuration
    log "Copying solrconfig.xml from EarkWeb to Solr ${CORE_NAME} config..."
    cp "${EARKWEB_DIR}/config/solrconfig.xml" "${SOLR_CONF_DIR}/solrconfig.xml" || error_exit "Failed to copy solrconfig.xml."

    # Run initialization script
    log "Running Solr initialization script..."
    cd "${EARKWEB_DIR}/scripts/"
    python3 init_solr.py || error_exit "Failed to run init_solr.py."

    # Restart Solr
    log "Restarting Solr..."
    "$SOLR_DIR/bin/solr" stop
    "$SOLR_DIR/bin/solr" start

    sudo cp $EARKWEB_DIR/config/supervisor/solr.conf $SUPERVISOR_CONFIG_DIR
    # Update supervisor configuration if file is present
    if [[ -f "${SUPERVISOR_CONFIG_DIR}solr.conf" ]]; then
        FILE_TO_UPDATE=$SUPERVISOR_CONFIG_DIR/solr.conf
        sudo sed -i "s|^\(directory\s*=\s*\).*|\1$SOLR_DIR|" "$FILE_TO_UPDATE"
        sudo sed -i "s|^\(command\s*=\s*\)/opt/earkweb|\1$EARKWEB_DIR|" "$FILE_TO_UPDATE"
        sudo sed -i "s|^\(user\s*=\s*\).*|\1$DESIRED_USER|" "$FILE_TO_UPDATE"
        sudo sed -i "s|^\(group\s*=\s*\).*|\1$DESIRED_GROUP|" "$FILE_TO_UPDATE"
        sudo sed -i "s|^\(stdout_logfile\s*=\s*\).*|\1$LOG_DIR/solr.log|" "$FILE_TO_UPDATE"
        sudo sed -i "s|^\(stderr_logfile\s*=\s*\).*|\1$LOG_DIR/solr.err|" "$FILE_TO_UPDATE"
        
        log "Re-read supervisor configuration"
        sudo supervisorctl reread
        sudo supervisorctl update
    else
        echo_highlight $WARN "Error: Missing ${SUPERVISOR_CONFIG_DIR}solr.conf file, supervisor is not configured."
    fi

    echo_highlight $OKGREEN "Installation of Solr completed"
else
    echo_highlight $WARN "Solr installation skipped."
fi

# Installing Nginx
echo_highlight_header $HEADER 'Installing and configuring Nginx'
if confirm_with_key "Do you want to proceed  with installing and configuring Nginx (sudo required)?\n"; then
    echo "Proceeding with installing and configuring Nginx..."
    sudo apt update
    sudo apt install nginx

    # Set ownership fallback to current user and group
    DESIRED_USER="${USER}"  # Default to the current logged-in user
    DESIRED_GROUP="$(id -gn)"  # Get the current user's primary group
    echo "Using ownership: ${DESIRED_USER}:${DESIRED_GROUP}"

    # Ensure the user is in the correct directory
    if ! check_directory; then
        echo_highlight $FAIL "Please ensure you are running this script from within the cloned 'earkweb' repository."
        exit 1
    fi

    # Define the variables
    CONFIG_NAME="earkweb"  # Replace with your configuration file name
    SOURCE_PATH="$EARKWEB_DIR/config/$CONFIG_NAME"  # Replace with the actual path to your config file
    NGINX_AVAILABLE="/etc/nginx/sites-available"
    NGINX_ENABLED="/etc/nginx/sites-enabled"
    DEFAULT_CONFIG="$NGINX_ENABLED/default"

    # Check if the source configuration file exists
    if [[ ! -f "$SOURCE_PATH" ]]; then
        echo "Error: Source Nginx configuration file $SOURCE_PATH does not exist."
        exit 1
    fi

    # Copy the configuration file to sites-available
    sudo cp "$SOURCE_PATH" "$NGINX_AVAILABLE/"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to copy $CONFIG_NAME to $NGINX_AVAILABLE."
        exit 1
    fi
    echo "Configuration file copied to $NGINX_AVAILABLE."

    # Disable the default configuration if it exists
    if [[ -L "$DEFAULT_CONFIG" ]]; then
        sudo rm -f "$DEFAULT_CONFIG"
        if [[ $? -ne 0 ]]; then
            echo "Error: Failed to remove default configuration."
            exit 1
        fi
        echo "Default configuration disabled."
    fi

    # Create a symbolic link in sites-enabled
    sudo ln -sf "$NGINX_AVAILABLE/$CONFIG_NAME" "$NGINX_ENABLED/$CONFIG_NAME"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to create symbolic link in $NGINX_ENABLED."
        exit 1
    fi
    echo "Symbolic link created in $NGINX_ENABLED."

    # Test the Nginx configuration
    sudo nginx -t
    if [[ $? -ne 0 ]]; then
        echo "Error: Nginx configuration test failed. Rolling back."
        sudo rm -f "$NGINX_ENABLED/$CONFIG_NAME"
        exit 1
    fi
    echo "Nginx configuration test passed."

    # Restart Nginx
    sudo systemctl restart nginx
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to restart Nginx."
        exit 1
    fi
echo "Nginx restarted successfully."
    echo_highlight $OKGREEN "Installation and configuration of Nginx completed"
else
    echo_highlight $WARN "Installation of Nginx skipped."
fi

# Installation complete
echo_highlight_header $HEADER 'Installation complete'
echo "Configure the API key at http://127.0.0.1:8000/earkweb/adminrest_framework_api_key/apikey/"
echo "Ensure it matches backend_api_key in the earkweb settings file settings/settings.cfg."
echo_highlight $OKGREEN "Installation complete."
