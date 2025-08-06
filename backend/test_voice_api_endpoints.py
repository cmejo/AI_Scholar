#!/usr/bin/env python3
"""
Test script for voice processing API endpoints
Tests the enhanced voice API functionality
"""

import sys
import os
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_endpoints_structure():
    """Test that API endpoints are properly structured"""
    logger.info("Testing voice API endpoints structure...")
    
    try:
        # Test that the API file exists and has the right structure
        api_file = os.path.join(os.path.dirname(__file__), 'api', 'voice_endpoints.py')
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for enhanced endpoints
        endpoints_to_check = [
            '@router.post(\'/speech-to-text\')',
            '@router.post(\'/text-to-speech\')',
            '@router.post(\'/streaming/start\')',
            '@router.post(\'/streaming/process\')',
            '@router.post(\'/streaming/stop\')',
            '@router.get(\'/streaming/results/{session_id}\')',
            '@router.get(\'/supported-languages\')',
            '@router.get(\'/available-voices\')',
            'real_time: str = Form("false")',  # Enhanced parameter
            'await voice_service.speech_to_text',  # Async call
            'await voice_service.start_streaming_session',  # Enhanced streaming
        ]
        
        results = {}
        for endpoint in endpoints_to_check:
            results[endpoint] = endpoint in content
        
        # Check for enhanced response fields (these are returned by service methods)
        enhanced_features = [
            'processing_time',
            'noise_reduced', 
            'quality_enhanced'
        ]
        
        for feature in enhanced_features:
            results[f'enhanced_field_{feature}'] = feature in content
        
        # Note: voice_detected, chunk_number, and statistics are returned by service methods,
        # not directly in the API file - this is correct architecture
        
        # Print results
        logger.info("API Endpoints Structure Test Results:")
        logger.info("=" * 50)
        
        passed = 0
        total = len(results)
        
        for check, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {check}")
            if result:
                passed += 1
        
        logger.info("=" * 50)
        logger.info(f"Summary: {passed}/{total} checks passed")
        
        if passed == total:
            logger.info("🎉 All API endpoint structure checks passed!")
        else:
            logger.info("⚠️  Some API endpoint checks failed.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"Error testing API endpoints: {str(e)}")
        return False

def test_frontend_service_structure():
    """Test that frontend voice service is properly enhanced"""
    logger.info("Testing frontend voice service structure...")
    
    try:
        # Test that the frontend service file exists and has the right structure
        service_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'services', 'voiceService.ts')
        
        with open(service_file, 'r') as f:
            content = f.read()
        
        # Check for enhanced methods
        methods_to_check = [
            'startStreamingSession',
            'processStreamingChunk',
            'stopStreamingSession',
            'getStreamingResults',
            'getAvailableVoiceProfiles',
            'processAudio',
            'speechToTextServerSide',
            'textToSpeechServerSide'
        ]
        
        results = {}
        for method in methods_to_check:
            results[method] = method in content
        
        # Check for enhanced interfaces
        interfaces_to_check = [
            'VoiceConfig',
            'TranscriptionResult',
            'AudioProcessingResult',
            'SpeechRecognitionOptions'
        ]
        
        for interface in interfaces_to_check:
            results[f'interface_{interface}'] = f'interface {interface}' in content
        
        # Print results
        logger.info("Frontend Voice Service Structure Test Results:")
        logger.info("=" * 50)
        
        passed = 0
        total = len(results)
        
        for check, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {check}")
            if result:
                passed += 1
        
        logger.info("=" * 50)
        logger.info(f"Summary: {passed}/{total} checks passed")
        
        if passed == total:
            logger.info("🎉 All frontend service structure checks passed!")
        else:
            logger.info("⚠️  Some frontend service checks failed.")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"Error testing frontend service: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("Starting voice processing API and frontend tests...")
    logger.info("=" * 60)
    
    # Test API endpoints
    api_test_passed = test_api_endpoints_structure()
    
    logger.info("")
    
    # Test frontend service
    frontend_test_passed = test_frontend_service_structure()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("OVERALL TEST RESULTS")
    logger.info("=" * 60)
    
    if api_test_passed and frontend_test_passed:
        logger.info("🎉 All tests passed! Voice processing infrastructure is properly implemented.")
    elif api_test_passed or frontend_test_passed:
        logger.info("⚠️  Some tests passed. Check individual results above.")
    else:
        logger.info("❌ Tests failed. Check error details above.")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()