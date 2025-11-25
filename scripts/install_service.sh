#!/bin/bash

# Systemd Service Installer for Life Weeks Telegram Bot
# This script sets up the bot as a systemd service for automatic startup and restart.

set -e

# --- Configuration ---
SERVICE_NAME="lifeweeks-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Resolve project root directory (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MAIN_FILE="$PROJECT_DIR/main.py"
ENV_FILE="$PROJECT_DIR/.env"

# --- Functions ---

log_info() {
    echo -e "\e[32m[INFO]\e[0m $1"
}

log_warn() {
    echo -e "\e[33m[WARN]\e[0m $1"
}

log_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
}

check_root() {
    # Some commands require sudo, but we can rely on the user having sudo access or running as root for specific commands.
    # We will use 'sudo' inside the script where necessary.
    if ! command -v sudo &> /dev/null; then
        log_warn "'sudo' not found. Ensure you are running as root or have appropriate permissions."
    fi
}

detect_venv() {
    if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
        echo "$PROJECT_DIR/venv/bin/python"
    elif [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
        echo "$PROJECT_DIR/.venv/bin/python"
    else
        echo ""
    fi
}

uninstall_service() {
    log_info "Uninstalling $SERVICE_NAME service..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl stop "$SERVICE_NAME"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        sudo systemctl disable "$SERVICE_NAME"
    fi

    if [ -f "$SERVICE_FILE" ]; then
        sudo rm "$SERVICE_FILE"
        log_info "Removed service file: $SERVICE_FILE"
    fi

    sudo systemctl daemon-reload
    log_info "Service uninstalled successfully."
}

install_service() {
    log_info "Starting installation..."

    # 1. Check required files
    if [ ! -f "$MAIN_FILE" ]; then
        log_error "main.py not found at $MAIN_FILE"
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        log_warn ".env file not found at $ENV_FILE. Make sure to create it before starting the service."
    else
        log_info "Found .env configuration."
    fi

    # 2. Detect Virtual Environment
    PYTHON_EXEC=$(detect_venv)
    if [ -z "$PYTHON_EXEC" ]; then
        log_error "Virtual environment not found (checked 'venv' and '.venv'). Please create one first."
        exit 1
    fi
    log_info "Using Python interpreter: $PYTHON_EXEC"

    # 3. Determine User/Group
    CURRENT_USER=$(whoami)
    # Group is usually same as user in standard setups, or can be detected
    CURRENT_GROUP=$(id -gn)

    # 4. Create Service File
    log_info "Generating systemd unit file..."
    
    # Create a temporary file
    TMP_SERVICE_FILE="/tmp/${SERVICE_NAME}.service"

    cat > "$TMP_SERVICE_FILE" <<EOF
[Unit]
Description=Life Weeks Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_GROUP
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$PYTHON_EXEC $MAIN_FILE
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # 5. Install Service File
    log_info "Installing service file to $SERVICE_FILE..."
    
    # Stop existing service if running (for update)
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Stopping existing service..."
        sudo systemctl stop "$SERVICE_NAME"
    fi

    sudo mv "$TMP_SERVICE_FILE" "$SERVICE_FILE"
    sudo chown root:root "$SERVICE_FILE"
    sudo chmod 644 "$SERVICE_FILE"

    # 6. Reload and Enable
    log_info "Reloading systemd daemon..."
    sudo systemctl daemon-reload

    log_info "Enabling service..."
    sudo systemctl enable "$SERVICE_NAME"

    log_info "Starting service..."
    sudo systemctl start "$SERVICE_NAME"

    # 7. Verification
    log_info "Checking service status..."
    # Wait a brief moment for startup
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Service is RUNNING."
        sudo systemctl status "$SERVICE_NAME" --no-pager | head -n 10
    else
        log_error "Service failed to start. Check logs with: journalctl -u $SERVICE_NAME -f"
        sudo systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

# --- Main Execution ---

if [ "$1" == "--uninstall" ]; then
    uninstall_service
else
    install_service
fi

