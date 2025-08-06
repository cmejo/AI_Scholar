#!/bin/bash

# Feature Flag Management Script for AI Scholar Advanced RAG
# Manages feature flags during deployment for gradual rollouts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
API_ENDPOINT="${API_ENDPOINT:-http://localhost}"
API_TOKEN="${API_TOKEN:-}"
FEATURE_FLAGS_CONFIG="/opt/ai-scholar/config/feature-flags.json"

# Default feature flags for new deployment
DEFAULT_FLAGS='{
  "maintenance_mode": false,
  "new_features_enabled": true,
  "mobile_app_enabled": true,
  "voice_interface_enabled": true,
  "external_integrations_enabled": true,
  "educational_features_enabled": true,
  "enterprise_features_enabled": true,
  "interactive_content_enabled": true,
  "opportunity_matching_enabled": true,
  "advanced_rag_enabled": true,
  "rollout_percentage": 100,
  "beta_features_enabled": false,
  "debug_mode": false
}'

# Get current feature flags
get_feature_flags() {
    print_status "Retrieving current feature flags..."
    
    local response=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
        "$API_ENDPOINT/api/monitoring/features/flags" 2>/dev/null || echo "{}")
    
    if [ "$response" = "{}" ]; then
        print_warning "Unable to retrieve feature flags, using defaults"
        echo "$DEFAULT_FLAGS"
    else
        echo "$response"
    fi
}

# Set feature flag
set_feature_flag() {
    local flag_name=$1
    local flag_value=$2
    local rollout_percentage=${3:-100}
    
    print_status "Setting feature flag: $flag_name = $flag_value (rollout: $rollout_percentage%)"
    
    local payload=$(jq -n \
        --arg name "$flag_name" \
        --argjson value "$flag_value" \
        --argjson rollout "$rollout_percentage" \
        '{($name): $value, "rollout_percentage": $rollout}')
    
    local response=$(curl -s -X POST \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$API_ENDPOINT/api/monitoring/features/flags" || echo "error")
    
    if [ "$response" = "error" ]; then
        print_error "Failed to set feature flag: $flag_name"
        return 1
    else
        print_success "Feature flag set successfully: $flag_name"
        return 0
    fi
}

# Enable maintenance mode
enable_maintenance_mode() {
    print_status "Enabling maintenance mode..."
    
    set_feature_flag "maintenance_mode" "true" 100
    set_feature_flag "new_features_enabled" "false" 0
    
    # Wait for propagation
    sleep 10
    
    # Verify maintenance mode is active
    local flags=$(get_feature_flags)
    local maintenance_mode=$(echo "$flags" | jq -r '.maintenance_mode // false')
    
    if [ "$maintenance_mode" = "true" ]; then
        print_success "Maintenance mode enabled"
        return 0
    else
        print_error "Failed to enable maintenance mode"
        return 1
    fi
}

# Disable maintenance mode
disable_maintenance_mode() {
    print_status "Disabling maintenance mode..."
    
    set_feature_flag "maintenance_mode" "false" 100
    
    # Wait for propagation
    sleep 10
    
    print_success "Maintenance mode disabled"
}

# Gradual feature rollout
gradual_rollout() {
    local feature_name=$1
    local rollout_steps=(10 25 50 75 100)
    local step_duration=300  # 5 minutes per step
    
    print_status "Starting gradual rollout for feature: $feature_name"
    
    for percentage in "${rollout_steps[@]}"; do
        print_status "Rolling out $feature_name to $percentage% of users..."
        
        if ! set_feature_flag "$feature_name" "true" "$percentage"; then
            print_error "Failed to set rollout percentage to $percentage%"
            return 1
        fi
        
        # Monitor for issues during this rollout step
        print_status "Monitoring for $step_duration seconds..."
        
        local start_time=$(date +%s)
        local error_count=0
        
        while [ $(($(date +%s) - start_time)) -lt $step_duration ]; do
            # Check for errors
            local health_check=$(curl -s -f "$API_ENDPOINT/health" > /dev/null && echo "ok" || echo "error")
            
            if [ "$health_check" = "error" ]; then
                error_count=$((error_count + 1))
                
                if [ $error_count -ge 3 ]; then
                    print_error "Too many errors detected during rollout. Rolling back..."
                    rollback_feature "$feature_name"
                    return 1
                fi
            else
                error_count=0
            fi
            
            sleep 30
        done
        
        print_success "Rollout to $percentage% completed successfully"
    done
    
    print_success "Gradual rollout completed for $feature_name"
}

# Rollback feature
rollback_feature() {
    local feature_name=$1
    
    print_warning "Rolling back feature: $feature_name"
    
    set_feature_flag "$feature_name" "false" 0
    
    print_success "Feature rolled back: $feature_name"
}

# Pre-deployment feature flag setup
pre_deployment_setup() {
    print_status "Setting up feature flags for deployment..."
    
    # Enable maintenance mode
    enable_maintenance_mode
    
    # Disable new features during deployment
    local new_features=(
        "mobile_app_enabled"
        "voice_interface_enabled"
        "external_integrations_enabled"
        "educational_features_enabled"
        "enterprise_features_enabled"
        "interactive_content_enabled"
        "opportunity_matching_enabled"
    )
    
    for feature in "${new_features[@]}"; do
        set_feature_flag "$feature" "false" 0
    done
    
    print_success "Pre-deployment feature flag setup completed"
}

# Post-deployment feature flag setup
post_deployment_setup() {
    print_status "Setting up feature flags after deployment..."
    
    # Disable maintenance mode
    disable_maintenance_mode
    
    # Enable core features first
    set_feature_flag "advanced_rag_enabled" "true" 100
    
    # Gradually enable new features
    local new_features=(
        "mobile_app_enabled"
        "voice_interface_enabled"
        "external_integrations_enabled"
        "educational_features_enabled"
        "enterprise_features_enabled"
        "interactive_content_enabled"
        "opportunity_matching_enabled"
    )
    
    for feature in "${new_features[@]}"; do
        print_status "Enabling feature: $feature"
        gradual_rollout "$feature"
        
        # Brief pause between features
        sleep 60
    done
    
    print_success "Post-deployment feature flag setup completed"
}

# Emergency rollback
emergency_rollback() {
    print_warning "Performing emergency rollback of all features..."
    
    # Enable maintenance mode
    enable_maintenance_mode
    
    # Disable all new features
    local all_features=(
        "new_features_enabled"
        "mobile_app_enabled"
        "voice_interface_enabled"
        "external_integrations_enabled"
        "educational_features_enabled"
        "enterprise_features_enabled"
        "interactive_content_enabled"
        "opportunity_matching_enabled"
        "beta_features_enabled"
    )
    
    for feature in "${all_features[@]}"; do
        set_feature_flag "$feature" "false" 0
    done
    
    # Keep only core features enabled
    set_feature_flag "advanced_rag_enabled" "true" 100
    
    print_success "Emergency rollback completed"
}

# Monitor feature flag health
monitor_feature_flags() {
    local duration=${1:-300}  # 5 minutes default
    local start_time=$(date +%s)
    
    print_status "Monitoring feature flags for $duration seconds..."
    
    while [ $(($(date +%s) - start_time)) -lt $duration ]; do
        local flags=$(get_feature_flags)
        
        # Check if maintenance mode is unexpectedly enabled
        local maintenance_mode=$(echo "$flags" | jq -r '.maintenance_mode // false')
        if [ "$maintenance_mode" = "true" ]; then
            print_warning "Maintenance mode is enabled"
        fi
        
        # Check rollout percentages
        local rollout_percentage=$(echo "$flags" | jq -r '.rollout_percentage // 100')
        print_status "Current rollout percentage: $rollout_percentage%"
        
        # Check for any disabled critical features
        local critical_features=("advanced_rag_enabled")
        for feature in "${critical_features[@]}"; do
            local feature_status=$(echo "$flags" | jq -r ".$feature // false")
            if [ "$feature_status" = "false" ]; then
                print_warning "Critical feature disabled: $feature"
            fi
        done
        
        sleep 30
    done
    
    print_success "Feature flag monitoring completed"
}

# Save feature flags configuration
save_configuration() {
    local config_file=${1:-$FEATURE_FLAGS_CONFIG}
    
    print_status "Saving feature flags configuration to $config_file..."
    
    local flags=$(get_feature_flags)
    
    # Create config directory if it doesn't exist
    mkdir -p "$(dirname "$config_file")"
    
    # Save with timestamp
    echo "$flags" | jq --arg timestamp "$(date -Iseconds)" '. + {saved_at: $timestamp}' > "$config_file"
    
    print_success "Configuration saved to $config_file"
}

# Load feature flags configuration
load_configuration() {
    local config_file=${1:-$FEATURE_FLAGS_CONFIG}
    
    if [ ! -f "$config_file" ]; then
        print_warning "Configuration file not found: $config_file"
        return 1
    fi
    
    print_status "Loading feature flags configuration from $config_file..."
    
    local config=$(cat "$config_file")
    local flags=$(echo "$config" | jq 'del(.saved_at)')
    
    # Apply each flag
    echo "$flags" | jq -r 'to_entries[] | "\(.key) \(.value)"' | while read key value; do
        if [ "$key" != "rollout_percentage" ]; then
            set_feature_flag "$key" "$value"
        fi
    done
    
    # Set rollout percentage last
    local rollout=$(echo "$flags" | jq -r '.rollout_percentage // 100')
    set_feature_flag "rollout_percentage" "$rollout"
    
    print_success "Configuration loaded from $config_file"
}

# Main function
main() {
    local command=${1:-status}
    local feature_name=${2:-}
    local value=${3:-}
    
    echo ""
    echo "🚩 AI Scholar Advanced RAG - Feature Flag Management"
    echo "===================================================="
    echo "Command: $command"
    echo "Started: $(date)"
    echo ""
    
    # Check if API token is set
    if [ -z "$API_TOKEN" ]; then
        print_warning "API_TOKEN not set, some operations may fail"
    fi
    
    case "$command" in
        "status")
            # Show current feature flags
            local flags=$(get_feature_flags)
            print_status "Current feature flags:"
            echo "$flags" | jq -r 'to_entries[] | "  \(.key): \(.value)"'
            ;;
        "set")
            # Set a specific feature flag
            if [ -z "$feature_name" ] || [ -z "$value" ]; then
                print_error "Usage: $0 set <feature_name> <value> [rollout_percentage]"
                exit 1
            fi
            set_feature_flag "$feature_name" "$value" "${4:-100}"
            ;;
        "enable")
            # Enable a feature
            if [ -z "$feature_name" ]; then
                print_error "Usage: $0 enable <feature_name> [rollout_percentage]"
                exit 1
            fi
            set_feature_flag "$feature_name" "true" "${3:-100}"
            ;;
        "disable")
            # Disable a feature
            if [ -z "$feature_name" ]; then
                print_error "Usage: $0 disable <feature_name>"
                exit 1
            fi
            set_feature_flag "$feature_name" "false" 0
            ;;
        "rollout")
            # Gradual rollout of a feature
            if [ -z "$feature_name" ]; then
                print_error "Usage: $0 rollout <feature_name>"
                exit 1
            fi
            gradual_rollout "$feature_name"
            ;;
        "rollback")
            # Rollback a feature
            if [ -z "$feature_name" ]; then
                print_error "Usage: $0 rollback <feature_name>"
                exit 1
            fi
            rollback_feature "$feature_name"
            ;;
        "maintenance-on")
            # Enable maintenance mode
            enable_maintenance_mode
            ;;
        "maintenance-off")
            # Disable maintenance mode
            disable_maintenance_mode
            ;;
        "pre-deploy")
            # Pre-deployment setup
            pre_deployment_setup
            ;;
        "post-deploy")
            # Post-deployment setup
            post_deployment_setup
            ;;
        "emergency-rollback")
            # Emergency rollback
            emergency_rollback
            ;;
        "monitor")
            # Monitor feature flags
            monitor_feature_flags "${2:-300}"
            ;;
        "save")
            # Save configuration
            save_configuration "$feature_name"
            ;;
        "load")
            # Load configuration
            load_configuration "$feature_name"
            ;;
        *)
            echo "Usage: $0 {status|set|enable|disable|rollout|rollback|maintenance-on|maintenance-off|pre-deploy|post-deploy|emergency-rollback|monitor|save|load}"
            echo ""
            echo "Commands:"
            echo "  status              - Show current feature flags"
            echo "  set <name> <value>  - Set a specific feature flag"
            echo "  enable <name>       - Enable a feature"
            echo "  disable <name>      - Disable a feature"
            echo "  rollout <name>      - Gradual rollout of a feature"
            echo "  rollback <name>     - Rollback a feature"
            echo "  maintenance-on      - Enable maintenance mode"
            echo "  maintenance-off     - Disable maintenance mode"
            echo "  pre-deploy          - Pre-deployment setup"
            echo "  post-deploy         - Post-deployment setup"
            echo "  emergency-rollback  - Emergency rollback all features"
            echo "  monitor [duration]  - Monitor feature flags"
            echo "  save [file]         - Save configuration to file"
            echo "  load [file]         - Load configuration from file"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Install jq if not available
if ! command -v jq &> /dev/null; then
    print_status "Installing jq for JSON processing..."
    apt-get update && apt-get install -y jq
fi

# Run main function
main "$@"