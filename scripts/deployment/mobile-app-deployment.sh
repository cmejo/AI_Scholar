#!/bin/bash

# Mobile App Deployment Script for AI Scholar Advanced RAG
# Handles PWA, Android, and iOS app deployments

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
PWA_BUILD_DIR="./dist"
ANDROID_BUILD_DIR="./android/app/build/outputs/apk/release"
IOS_BUILD_DIR="./ios/App"
CDN_BUCKET_PROD="${PWA_S3_BUCKET_PROD:-ai-scholar-pwa-prod}"
CDN_BUCKET_STAGING="${PWA_S3_BUCKET_STAGING:-ai-scholar-pwa-staging}"
GOOGLE_PLAY_TRACK="${GOOGLE_PLAY_TRACK:-production}"
APP_STORE_ENVIRONMENT="${APP_STORE_ENVIRONMENT:-production}"

# Build PWA
build_pwa() {
    local environment=${1:-production}
    
    print_status "Building PWA for $environment environment..."
    
    # Set environment variables
    export NODE_ENV="production"
    export REACT_APP_ENVIRONMENT="$environment"
    
    if [ "$environment" = "production" ]; then
        export REACT_APP_API_URL="https://aischolar.com/api"
        export REACT_APP_WS_URL="wss://aischolar.com/ws"
    else
        export REACT_APP_API_URL="https://staging.aischolar.com/api"
        export REACT_APP_WS_URL="wss://staging.aischolar.com/ws"
    fi
    
    # Install dependencies
    npm ci
    
    # Build PWA
    npm run build:pwa
    
    if [ -d "$PWA_BUILD_DIR" ]; then
        print_success "PWA build completed successfully"
        return 0
    else
        print_error "PWA build failed"
        return 1
    fi
}

# Deploy PWA to CDN
deploy_pwa() {
    local environment=${1:-production}
    
    print_status "Deploying PWA to $environment environment..."
    
    # Determine S3 bucket and CloudFront distribution
    local s3_bucket
    local cloudfront_id
    
    if [ "$environment" = "production" ]; then
        s3_bucket="$CDN_BUCKET_PROD"
        cloudfront_id="${CLOUDFRONT_DISTRIBUTION_ID_PROD}"
    else
        s3_bucket="$CDN_BUCKET_STAGING"
        cloudfront_id="${CLOUDFRONT_DISTRIBUTION_ID_STAGING}"
    fi
    
    # Sync static assets with long cache headers
    aws s3 sync "$PWA_BUILD_DIR" "s3://$s3_bucket" \
        --delete \
        --cache-control "max-age=31536000,public,immutable" \
        --exclude "*.html" \
        --exclude "sw.js" \
        --exclude "manifest.json" \
        --exclude "*.map"
    
    # Sync HTML, service worker, and manifest with no-cache headers
    aws s3 sync "$PWA_BUILD_DIR" "s3://$s3_bucket" \
        --delete \
        --cache-control "max-age=0,no-cache,no-store,must-revalidate" \
        --include "*.html" \
        --include "sw.js" \
        --include "manifest.json"
    
    # Invalidate CloudFront cache
    if [ -n "$cloudfront_id" ]; then
        print_status "Invalidating CloudFront cache..."
        aws cloudfront create-invalidation \
            --distribution-id "$cloudfront_id" \
            --paths "/*"
    fi
    
    print_success "PWA deployed to $environment environment"
}

# Build Android APK
build_android() {
    local build_type=${1:-release}
    
    print_status "Building Android APK ($build_type)..."
    
    # Check if Android SDK is available
    if ! command -v android &> /dev/null; then
        print_error "Android SDK not found"
        return 1
    fi
    
    # Install Capacitor CLI if not available
    if ! command -v cap &> /dev/null; then
        npm install -g @capacitor/cli
    fi
    
    # Build web app first
    npm run build:mobile
    
    # Sync Capacitor
    npx cap sync android
    
    # Build Android APK
    cd android
    
    if [ "$build_type" = "release" ]; then
        # Build signed release APK
        ./gradlew assembleRelease \
            -Pandroid.injected.signing.store.file="${ANDROID_KEYSTORE_FILE}" \
            -Pandroid.injected.signing.store.password="${KEYSTORE_PASSWORD}" \
            -Pandroid.injected.signing.key.alias="${KEY_ALIAS}" \
            -Pandroid.injected.signing.key.password="${KEY_PASSWORD}"
    else
        # Build debug APK
        ./gradlew assembleDebug
    fi
    
    cd ..
    
    if [ -f "$ANDROID_BUILD_DIR/app-$build_type.apk" ]; then
        print_success "Android APK built successfully"
        return 0
    else
        print_error "Android APK build failed"
        return 1
    fi
}

# Deploy Android app to Google Play
deploy_android() {
    local track=${1:-$GOOGLE_PLAY_TRACK}
    
    print_status "Deploying Android app to Google Play ($track track)..."
    
    # Check if APK exists
    if [ ! -f "$ANDROID_BUILD_DIR/app-release.apk" ]; then
        print_error "Release APK not found. Build first."
        return 1
    fi
    
    # Upload to Google Play using fastlane or Google Play Console API
    if command -v fastlane &> /dev/null; then
        # Use fastlane if available
        cd android
        fastlane deploy track:"$track"
        cd ..
    else
        # Use Google Play Console API directly
        python3 << EOF
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Load service account credentials
credentials = Credentials.from_service_account_info(
    json.loads(os.environ['GOOGLE_PLAY_SERVICE_ACCOUNT'])
)

# Build Google Play service
service = build('androidpublisher', 'v3', credentials=credentials)

# Upload APK
package_name = 'com.aischolar.advancedrag'
apk_file = '$ANDROID_BUILD_DIR/app-release.apk'

# Create edit
edit_request = service.edits().insert(body={}, packageName=package_name)
edit_result = edit_request.execute()
edit_id = edit_result['id']

# Upload APK
with open(apk_file, 'rb') as apk_file:
    apk_response = service.edits().apks().upload(
        editId=edit_id,
        packageName=package_name,
        media_body=apk_file
    ).execute()

# Assign to track
track_response = service.edits().tracks().update(
    editId=edit_id,
    track='$track',
    packageName=package_name,
    body={'releases': [{'versionCodes': [apk_response['versionCode']], 'status': 'completed'}]}
).execute()

# Commit changes
commit_request = service.edits().commit(
    editId=edit_id,
    packageName=package_name
).execute()

print(f"Android app deployed to {track} track successfully")
EOF
    fi
    
    print_success "Android app deployed to Google Play"
}

# Build iOS app
build_ios() {
    local configuration=${1:-Release}
    
    print_status "Building iOS app ($configuration)..."
    
    # Check if Xcode is available
    if ! command -v xcodebuild &> /dev/null; then
        print_error "Xcode not found"
        return 1
    fi
    
    # Build web app first
    npm run build:mobile
    
    # Sync Capacitor
    npx cap sync ios
    
    # Build iOS app
    cd "$IOS_BUILD_DIR"
    
    # Archive the app
    xcodebuild -workspace App.xcworkspace \
        -scheme App \
        -configuration "$configuration" \
        -destination generic/platform=iOS \
        -archivePath App.xcarchive \
        archive
    
    # Export IPA
    if [ "$configuration" = "Release" ]; then
        xcodebuild -exportArchive \
            -archivePath App.xcarchive \
            -exportPath . \
            -exportOptionsPlist ExportOptions.plist
    fi
    
    cd - > /dev/null
    
    if [ -f "$IOS_BUILD_DIR/App.xcarchive" ]; then
        print_success "iOS app built successfully"
        return 0
    else
        print_error "iOS app build failed"
        return 1
    fi
}

# Deploy iOS app to App Store
deploy_ios() {
    local environment=${1:-$APP_STORE_ENVIRONMENT}
    
    print_status "Deploying iOS app to App Store ($environment)..."
    
    # Check if IPA exists
    if [ ! -f "$IOS_BUILD_DIR"/*.ipa ]; then
        print_error "IPA file not found. Build first."
        return 1
    fi
    
    # Upload to App Store using altool
    xcrun altool --upload-app \
        --type ios \
        --file "$IOS_BUILD_DIR"/*.ipa \
        --username "${APPLE_ID_USERNAME}" \
        --password "${APPLE_ID_PASSWORD}"
    
    print_success "iOS app uploaded to App Store"
}

# Update PWA version in backend
update_pwa_version() {
    local environment=${1:-production}
    local version=${2:-$(git rev-parse --short HEAD)}
    
    print_status "Updating PWA version in backend..."
    
    # Update PWA version via API
    curl -X POST "${API_ENDPOINT}/api/admin/pwa/update-version" \
        -H "Authorization: Bearer ${API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"version\": \"$version\", \"environment\": \"$environment\"}" \
        --fail --silent
    
    print_success "PWA version updated to $version"
}

# Send deployment notifications
send_deployment_notification() {
    local platform=$1
    local environment=$2
    local status=$3
    local version=${4:-$(git rev-parse --short HEAD)}
    
    # Slack notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local color=$([[ "$status" == "success" ]] && echo "good" || echo "danger")
        local emoji=$([[ "$platform" == "pwa" ]] && echo "🌐" || [[ "$platform" == "android" ]] && echo "🤖" || echo "🍎")
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$emoji AI Scholar Mobile Deployment\",
                    \"text\": \"$platform deployment $status\",
                    \"fields\": [
                        {\"title\": \"Platform\", \"value\": \"$platform\", \"short\": true},
                        {\"title\": \"Environment\", \"value\": \"$environment\", \"short\": true},
                        {\"title\": \"Version\", \"value\": \"$version\", \"short\": true},
                        {\"title\": \"Status\", \"value\": \"$status\", \"short\": true}
                    ]
                }]
            }" \
            "${SLACK_WEBHOOK_URL}" > /dev/null 2>&1 || true
    fi
}

# Main deployment function
main() {
    local platform=${1:-all}
    local environment=${2:-production}
    local build_type=${3:-release}
    
    echo ""
    echo "📱 AI Scholar Advanced RAG - Mobile App Deployment"
    echo "=================================================="
    echo "Platform: $platform"
    echo "Environment: $environment"
    echo "Build Type: $build_type"
    echo "Started: $(date)"
    echo ""
    
    case "$platform" in
        "pwa")
            if build_pwa "$environment" && deploy_pwa "$environment"; then
                update_pwa_version "$environment"
                send_deployment_notification "pwa" "$environment" "success"
                print_success "🎉 PWA deployment completed successfully!"
            else
                send_deployment_notification "pwa" "$environment" "failed"
                print_error "PWA deployment failed"
                exit 1
            fi
            ;;
        "android")
            if build_android "$build_type" && deploy_android; then
                send_deployment_notification "android" "$environment" "success"
                print_success "🎉 Android deployment completed successfully!"
            else
                send_deployment_notification "android" "$environment" "failed"
                print_error "Android deployment failed"
                exit 1
            fi
            ;;
        "ios")
            if build_ios "Release" && deploy_ios; then
                send_deployment_notification "ios" "$environment" "success"
                print_success "🎉 iOS deployment completed successfully!"
            else
                send_deployment_notification "ios" "$environment" "failed"
                print_error "iOS deployment failed"
                exit 1
            fi
            ;;
        "all")
            # Deploy all platforms
            local failed_platforms=()
            
            # Deploy PWA
            if build_pwa "$environment" && deploy_pwa "$environment"; then
                update_pwa_version "$environment"
                send_deployment_notification "pwa" "$environment" "success"
                print_success "PWA deployment completed"
            else
                failed_platforms+=("pwa")
                send_deployment_notification "pwa" "$environment" "failed"
            fi
            
            # Deploy Android (only for production)
            if [ "$environment" = "production" ]; then
                if build_android "$build_type" && deploy_android; then
                    send_deployment_notification "android" "$environment" "success"
                    print_success "Android deployment completed"
                else
                    failed_platforms+=("android")
                    send_deployment_notification "android" "$environment" "failed"
                fi
                
                # Deploy iOS (only for production)
                if build_ios "Release" && deploy_ios; then
                    send_deployment_notification "ios" "$environment" "success"
                    print_success "iOS deployment completed"
                else
                    failed_platforms+=("ios")
                    send_deployment_notification "ios" "$environment" "failed"
                fi
            fi
            
            # Summary
            if [ ${#failed_platforms[@]} -eq 0 ]; then
                print_success "🎉 All mobile deployments completed successfully!"
            else
                print_error "Some deployments failed: ${failed_platforms[*]}"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 {pwa|android|ios|all} [environment] [build_type]"
            echo ""
            echo "Platforms:"
            echo "  pwa     - Deploy Progressive Web App"
            echo "  android - Deploy Android app to Google Play"
            echo "  ios     - Deploy iOS app to App Store"
            echo "  all     - Deploy all platforms"
            echo ""
            echo "Environments:"
            echo "  production - Production environment (default)"
            echo "  staging    - Staging environment"
            echo ""
            echo "Build Types:"
            echo "  release - Release build (default)"
            echo "  debug   - Debug build"
            exit 1
            ;;
    esac
    
    echo ""
    echo "Finished: $(date)"
    echo ""
}

# Error handling
trap 'print_error "Mobile deployment failed at line $LINENO"' ERR

# Run main function
main "$@"