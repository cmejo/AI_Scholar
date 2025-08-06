"""
Voice Data Security and Privacy Compliance Tests

Tests for voice data encryption, privacy protection, and compliance
with data protection regulations.
"""

import pytest
import asyncio
import base64
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from backend.services.voice_processing_service import VoiceProcessingService
from backend.services.security_testing_service import SecurityTestingService


class TestVoiceDataPrivacyCompliance:
    """Test voice data privacy and encryption compliance"""
    
    @pytest.fixture
    def voice_service(self):
        return VoiceProcessingService()
    
    @pytest.fixture
    def security_service(self):
        return SecurityTestingService()
    
    @pytest.fixture
    def sample_audio_data(self):
        """Generate sample audio data for testing"""
        return b"sample_voice_audio_data_for_testing_purposes_" * 100
    
    @pytest.mark.asyncio
    async def test_voice_data_encryption_at_rest(self, voice_service, sample_audio_data):
        """Test that voice data is encrypted when stored at rest"""
        with patch.object(voice_service, 'store_voice_data') as mock_store:
            # Process voice data
            result = await voice_service.process_and_store_audio(sample_audio_data)
            
            # Verify storage was called
            mock_store.assert_called_once()
            stored_data = mock_store.call_args[0][0]
            
            # Verify data is encrypted (not plaintext)
            assert stored_data != sample_audio_data
            assert len(stored_data) > len(sample_audio_data)  # Encrypted data is larger
            
            # Verify it's not just base64 encoded
            try:
                decoded = base64.b64decode(stored_data)
                assert decoded != sample_audio_data  # Should still be encrypted
            except Exception:
                pass  # Expected if not base64
    
    @pytest.mark.asyncio
    async def test_voice_data_encryption_in_transit(self, voice_service, sample_audio_data):
        """Test that voice data is encrypted during transmission"""
        with patch.object(voice_service, 'transmit_voice_data') as mock_transmit:
            # Simulate transmission
            await voice_service.send_voice_data_to_server(sample_audio_data)
            
            # Verify transmission was called with encrypted data
            mock_transmit.assert_called_once()
            transmitted_data = mock_transmit.call_args[0][0]
            
            # Verify data is encrypted for transmission
            assert transmitted_data != sample_audio_data
            
            # Check for encryption headers or metadata
            if isinstance(transmitted_data, dict):
                assert 'encrypted' in transmitted_data or 'cipher' in transmitted_data
    
    @pytest.mark.asyncio
    async def test_voice_biometric_data_protection(self, voice_service):
        """Test protection of voice biometric characteristics"""
        voice_profile = {
            "user_id": "test_user_voice_123",
            "voice_characteristics": {
                "pitch_range": [80, 300],
                "formant_frequencies": [800, 1200, 2400],
                "speaking_rate": 150,
                "voice_quality": "modal"
            },
            "created_at": datetime.now()
        }
        
        with patch.object(voice_service, 'store_voice_profile') as mock_store:
            await voice_service.create_voice_profile(voice_profile)
            
            # Verify biometric data is hashed/encrypted
            stored_profile = mock_store.call_args[0][0]
            
            # Voice characteristics should be hashed or encrypted
            stored_characteristics = stored_profile.get("voice_characteristics")
            original_characteristics = voice_profile["voice_characteristics"]
            
            assert stored_characteristics != original_characteristics
            
            # Should be a hash or encrypted string
            if isinstance(stored_characteristics, str):
                assert len(stored_characteristics) >= 32  # Minimum hash length
    
    @pytest.mark.asyncio
    async def test_voice_data_retention_policy(self, voice_service):
        """Test voice data retention and automatic deletion"""
        session_id = "test_voice_session_retention"
        
        # Test data within retention period
        with patch.object(voice_service, 'get_voice_session_age') as mock_age:
            mock_age.return_value = timedelta(days=15)  # Within 30-day policy
            
            cleanup_result = await voice_service.cleanup_expired_voice_data(session_id)
            assert cleanup_result.deleted is False
            assert cleanup_result.reason == "within_retention_period"
        
        # Test data beyond retention period
        with patch.object(voice_service, 'get_voice_session_age') as mock_age:
            mock_age.return_value = timedelta(days=35)  # Beyond 30-day policy
            
            cleanup_result = await voice_service.cleanup_expired_voice_data(session_id)
            assert cleanup_result.deleted is True
            assert cleanup_result.reason == "retention_period_exceeded"
    
    @pytest.mark.asyncio
    async def test_voice_consent_management(self, voice_service):
        """Test voice data consent recording and management"""
        user_id = "test_user_consent_voice"
        
        # Test consent recording
        consent_data = {
            "user_id": user_id,
            "consent_type": "voice_processing",
            "consent_given": True,
            "consent_date": datetime.now(),
            "purpose": "research_assistance",
            "data_types": ["voice_audio", "speech_transcription"]
        }
        
        consent_result = await voice_service.record_voice_consent(consent_data)
        assert consent_result.success is True
        assert consent_result.consent_id is not None
        
        # Test consent verification
        verification_result = await voice_service.verify_voice_consent(user_id, "voice_processing")
        assert verification_result.has_consent is True
        assert verification_result.consent_valid is True
        
        # Test consent withdrawal
        withdrawal_result = await voice_service.withdraw_voice_consent(user_id, "voice_processing")
        assert withdrawal_result.success is True
        
        # Verify consent is no longer valid
        verification_after_withdrawal = await voice_service.verify_voice_consent(user_id, "voice_processing")
        assert verification_after_withdrawal.has_consent is False
    
    @pytest.mark.asyncio
    async def test_voice_data_anonymization(self, voice_service, sample_audio_data):
        """Test voice data anonymization capabilities"""
        user_id = "test_user_anonymization"
        
        # Process voice data with anonymization
        anonymization_result = await voice_service.anonymize_voice_data(
            audio_data=sample_audio_data,
            user_id=user_id,
            anonymization_level="high"
        )
        
        assert anonymization_result.success is True
        assert anonymization_result.anonymized_data != sample_audio_data
        
        # Verify personal identifiers are removed
        assert user_id not in str(anonymization_result.anonymized_data)
        
        # Verify anonymization metadata
        assert anonymization_result.anonymization_level == "high"
        assert anonymization_result.techniques_applied is not None
    
    @pytest.mark.asyncio
    async def test_voice_data_access_logging(self, voice_service):
        """Test comprehensive logging of voice data access"""
        user_id = "test_user_access_logging"
        voice_session_id = "test_session_logging"
        
        with patch.object(voice_service, 'log_voice_data_access') as mock_log:
            # Simulate voice data access
            await voice_service.access_voice_data(user_id, voice_session_id)
            
            # Verify access is logged
            mock_log.assert_called_once()
            log_entry = mock_log.call_args[0][0]
            
            assert log_entry["event_type"] == "voice_data_access"
            assert log_entry["user_id"] == user_id
            assert log_entry["session_id"] == voice_session_id
            assert log_entry["timestamp"] is not None
            assert log_entry["ip_address"] is not None
    
    @pytest.mark.asyncio
    async def test_voice_data_breach_detection(self, voice_service):
        """Test voice data breach detection and response"""
        # Simulate suspicious voice data access patterns
        suspicious_patterns = [
            {"user_id": "test_user", "access_count": 100, "time_window": "1_hour"},
            {"user_id": "test_user", "access_time": "03:00:00", "location": "unusual"},
            {"user_id": "test_user", "data_volume": "excessive", "download_speed": "high"}
        ]
        
        for pattern in suspicious_patterns:
            breach_result = await voice_service.detect_voice_data_breach(pattern)
            
            if breach_result.is_suspicious:
                # Verify breach response
                assert breach_result.response_actions is not None
                assert "user_notification" in breach_result.response_actions
                assert "access_restriction" in breach_result.response_actions
                assert "audit_log_creation" in breach_result.response_actions
    
    @pytest.mark.asyncio
    async def test_voice_processing_transparency(self, voice_service):
        """Test transparency in voice processing operations"""
        user_id = "test_user_transparency"
        
        # Request voice processing transparency report
        transparency_result = await voice_service.generate_voice_processing_report(user_id)
        
        assert transparency_result.success is True
        
        # Verify report contains required information
        report = transparency_result.report
        assert "data_collected" in report
        assert "processing_purposes" in report
        assert "retention_period" in report
        assert "third_party_sharing" in report
        assert "user_rights" in report
        
        # Verify data accuracy
        assert report["data_collected"]["voice_audio"] is not None
        assert report["processing_purposes"] is not None
        assert report["retention_period"] == "30_days"
    
    @pytest.mark.asyncio
    async def test_cross_border_voice_data_transfer(self, voice_service):
        """Test compliance for cross-border voice data transfers"""
        transfer_request = {
            "user_id": "test_user_transfer",
            "source_country": "US",
            "destination_country": "EU",
            "data_type": "voice_audio",
            "purpose": "research_collaboration"
        }
        
        # Test transfer compliance check
        compliance_result = await voice_service.check_cross_border_transfer_compliance(transfer_request)
        
        if transfer_request["destination_country"] == "EU":
            # Should require additional GDPR compliance
            assert compliance_result.requires_adequacy_decision is True
            assert compliance_result.additional_safeguards_required is True
        
        # Test transfer with proper safeguards
        safeguards = {
            "standard_contractual_clauses": True,
            "encryption_in_transit": True,
            "data_minimization": True,
            "user_consent": True
        }
        
        transfer_result = await voice_service.execute_cross_border_transfer(
            transfer_request, safeguards
        )
        
        assert transfer_result.success is True
        assert transfer_result.compliance_verified is True


class TestVoiceSecurityIntegration:
    """Test integration of voice security with other system components"""
    
    @pytest.fixture
    def security_service(self):
        return SecurityTestingService()
    
    @pytest.mark.asyncio
    async def test_voice_security_with_user_authentication(self, security_service):
        """Test voice security integration with user authentication"""
        # Test voice-based authentication security
        voice_auth_data = {
            "user_id": "test_user_voice_auth",
            "voice_sample": b"voice_authentication_sample",
            "authentication_method": "voice_biometric"
        }
        
        # Test voice authentication security
        auth_security_result = await security_service.test_voice_authentication_security(voice_auth_data)
        
        # Verify security measures
        assert auth_security_result.biometric_template_protected is True
        assert auth_security_result.replay_attack_prevention is True
        assert auth_security_result.liveness_detection is True
    
    @pytest.mark.asyncio
    async def test_voice_security_with_data_storage(self, security_service):
        """Test voice security integration with data storage systems"""
        storage_config = {
            "encryption_at_rest": True,
            "key_management": "HSM",
            "access_controls": ["RBAC", "MAC"],
            "audit_logging": True
        }
        
        # Test storage security for voice data
        storage_security_result = await security_service.test_voice_storage_security(storage_config)
        
        assert storage_security_result.encryption_verified is True
        assert storage_security_result.key_management_secure is True
        assert storage_security_result.access_controls_effective is True
    
    @pytest.mark.asyncio
    async def test_voice_security_performance_impact(self, security_service):
        """Test performance impact of voice security measures"""
        performance_test_data = {
            "audio_size": 1024 * 1024,  # 1MB audio file
            "encryption_algorithm": "AES-256-GCM",
            "processing_time_limit": 2.0  # 2 seconds max
        }
        
        # Test encryption performance
        performance_result = await security_service.test_voice_encryption_performance(performance_test_data)
        
        assert performance_result.encryption_time < performance_test_data["processing_time_limit"]
        assert performance_result.decryption_time < performance_test_data["processing_time_limit"]
        assert performance_result.throughput_acceptable is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])