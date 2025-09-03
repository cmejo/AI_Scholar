#!/bin/bash
# Installation script for comprehensive analysis tools
# Ubuntu compatibility focused

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Ubuntu
check_ubuntu() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            log_info "Detected Ubuntu $VERSION_ID"
            return 0
        fi
    fi
    log_warning "Not running on Ubuntu. Some tools may not work as expected."
    return 1
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update
    
    # Install required system packages
    sudo apt-get install -y \
        curl \
        wget \
        git \
        build-essential \
        python3-dev \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        shellcheck \
        yamllint \
        jq \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "System dependencies installed"
}

# Install Docker (if not present)
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker already installed: $(docker --version)"
        return 0
    fi
    
    log_info "Installing Docker..."
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up the repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    log_success "Docker installed. Please log out and back in for group changes to take effect."
}

# Install Hadolint
install_hadolint() {
    if command -v hadolint &> /dev/null; then
        log_info "Hadolint already installed: $(hadolint --version)"
        return 0
    fi
    
    log_info "Installing Hadolint..."
    
    # Download and install hadolint
    HADOLINT_VERSION="v2.12.0"
    wget -O /tmp/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-x86_64"
    chmod +x /tmp/hadolint
    sudo mv /tmp/hadolint /usr/local/bin/hadolint
    
    log_success "Hadolint installed: $(hadolint --version)"
}

# Install Node.js tools
install_node_tools() {
    log_info "Installing Node.js analysis tools..."
    
    # Update npm to latest version
    sudo npm install -g npm@latest
    
    # Install global analysis tools
    sudo npm install -g \
        eslint \
        prettier \
        typescript \
        @typescript-eslint/parser \
        @typescript-eslint/eslint-plugin \
        eslint-plugin-react \
        eslint-plugin-react-hooks \
        eslint-plugin-import \
        eslint-plugin-jsx-a11y \
        npm-check-updates \
        depcheck \
        bundlesize \
        webpack-bundle-analyzer
    
    log_success "Node.js tools installed"
}

# Install Python analysis tools
install_python_tools() {
    log_info "Installing Python analysis tools..."
    
    # Create virtual environment for analysis tools
    if [[ ! -d "analysis-venv" ]]; then
        python3 -m venv analysis-venv
    fi
    
    # Activate virtual environment
    source analysis-venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install analysis tools
    pip install -r scripts/analysis-requirements.txt
    
    # Create symlinks for global access
    sudo ln -sf "$(pwd)/analysis-venv/bin/flake8" /usr/local/bin/flake8-analysis
    sudo ln -sf "$(pwd)/analysis-venv/bin/black" /usr/local/bin/black-analysis
    sudo ln -sf "$(pwd)/analysis-venv/bin/mypy" /usr/local/bin/mypy-analysis
    sudo ln -sf "$(pwd)/analysis-venv/bin/bandit" /usr/local/bin/bandit-analysis
    sudo ln -sf "$(pwd)/analysis-venv/bin/pylint" /usr/local/bin/pylint-analysis
    sudo ln -sf "$(pwd)/analysis-venv/bin/safety" /usr/local/bin/safety-analysis
    sudo ln -sf "$(pwd)/analysis-venv/bin/pip-audit" /usr/local/bin/pip-audit-analysis
    
    deactivate
    
    log_success "Python analysis tools installed"
}

# Install additional security tools
install_security_tools() {
    log_info "Installing additional security tools..."
    
    # Install Trivy for container security scanning
    if ! command -v trivy &> /dev/null; then
        wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
        echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
        sudo apt-get update
        sudo apt-get install -y trivy
    fi
    
    # Install Grype for vulnerability scanning
    if ! command -v grype &> /dev/null; then
        curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
    fi
    
    log_success "Security tools installed"
}

# Verify installations
verify_installations() {
    log_info "Verifying tool installations..."
    
    local tools=(
        "docker --version"
        "hadolint --version"
        "shellcheck --version"
        "yamllint --version"
        "node --version"
        "npm --version"
        "eslint --version"
        "prettier --version"
        "typescript --version"
        "trivy --version"
        "grype version"
    )
    
    local python_tools=(
        "flake8-analysis --version"
        "black-analysis --version"
        "mypy-analysis --version"
        "bandit-analysis --version"
        "pylint-analysis --version"
        "safety-analysis --version"
        "pip-audit-analysis --version"
    )
    
    local failed=0
    
    for tool in "${tools[@]}"; do
        if eval "$tool" &> /dev/null; then
            log_success "$tool"
        else
            log_error "Failed: $tool"
            ((failed++))
        fi
    done
    
    for tool in "${python_tools[@]}"; do
        if eval "$tool" &> /dev/null; then
            log_success "$tool"
        else
            log_error "Failed: $tool"
            ((failed++))
        fi
    done
    
    if [[ $failed -eq 0 ]]; then
        log_success "All tools installed successfully!"
    else
        log_error "$failed tools failed to install"
        exit 1
    fi
}

# Create analysis configuration
create_analysis_config() {
    log_info "Creating analysis configuration..."
    
    # Make analysis script executable
    chmod +x scripts/codebase-analysis.py
    
    # Create analysis wrapper script
    cat > scripts/run-analysis.sh << 'EOF'
#!/bin/bash
# Wrapper script for codebase analysis

set -euo pipefail

# Default values
OUTPUT_FILE="analysis-results.json"
PROJECT_ROOT="$(pwd)"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -r|--root)
            PROJECT_ROOT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -o, --output FILE    Output file for results (default: analysis-results.json)"
            echo "  -r, --root DIR       Project root directory (default: current directory)"
            echo "  -v, --verbose        Enable verbose output"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Activate analysis environment
if [[ -d "analysis-venv" ]]; then
    source analysis-venv/bin/activate
fi

# Run analysis
ARGS=("--output" "$OUTPUT_FILE" "--project-root" "$PROJECT_ROOT")
if [[ "$VERBOSE" == "true" ]]; then
    ARGS+=("--verbose")
fi

python3 scripts/codebase-analysis.py "${ARGS[@]}"

# Deactivate environment
if [[ -d "analysis-venv" ]]; then
    deactivate
fi

echo "Analysis complete. Results saved to $OUTPUT_FILE"
EOF
    
    chmod +x scripts/run-analysis.sh
    
    log_success "Analysis configuration created"
}

# Main installation function
main() {
    log_info "Starting comprehensive analysis tools installation for Ubuntu..."
    
    check_root
    check_ubuntu
    
    install_system_deps
    install_docker
    install_hadolint
    install_node_tools
    install_python_tools
    install_security_tools
    verify_installations
    create_analysis_config
    
    log_success "Installation complete!"
    log_info "You can now run analysis with: ./scripts/run-analysis.sh"
    log_warning "Please log out and back in for Docker group changes to take effect."
}

# Run main function
main "$@"