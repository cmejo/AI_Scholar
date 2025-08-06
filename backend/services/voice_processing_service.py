"""
Enhanced Voice Processing Service for speech-to-text and text-to-speech functionality
Implements real-time processing, noise reduction, and streaming capabilities
"""

import os
import tempfile
import logging
import uuid
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
import json
from datetime import datetime, timedelta
import threading
import queue
import wave
import audioop
import io
import time
from dataclasses import dataclass

# Audio processing libraries
try:
    import speech_recognition as sr
    import pyttsx3
    import librosa
    import soundfile as sf
    import numpy as np
    import webrtcvad
    import scipy.signal
    from scipy.io import wavfile
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    logging.warning("Audio processing libraries not available. Install speech_recognition, pyttsx3, librosa, soundfile, webrtcvad, scipy")

from ..core.config import Config

@dataclass
class StreamingChunk:
    """Represents a streaming audio chunk"""
    session_id: str
    chunk_id: str
    audio_data: bytes
    timestamp: float
    is_final: bool = False

@dataclass
class ProcessingResult:
    """Represents audio processing result"""
    text: str
    confidence: float
    language: str
    timestamp: float
    processing_time: float
    noise_reduced: bool = False
    quality_enhanced: bool = False

@dataclass
class VoiceProfile:
    """Represents a voice profile for TTS"""
    voice_id: str
    name: str
    language: str
    gender: str
    age: str
    rate: float = 200
    pitch: float = 0
    volume: float = 0.9

logger = logging.getLogger(__name__)

class VoiceProcessingService:
    """Enhanced service for handling voice processing operations with real-time capabilities"""
    
    def __init__(self):
        self.config = Config()
        self.recognizer = None
        self.tts_engine = None
        self.streaming_sessions = {}
        self.voice_profiles = {}
        self.vad = None  # Voice Activity Detection
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # Enhanced language support with regional variants
        self.supported_languages = [
            'en-US', 'en-GB', 'en-AU', 'en-CA', 'en-IN',
            'es-ES', 'es-MX', 'es-AR', 'es-CO', 'es-CL',
            'fr-FR', 'fr-CA', 'fr-BE', 'fr-CH',
            'de-DE', 'de-AT', 'de-CH',
            'it-IT', 'pt-BR', 'pt-PT',
            'ru-RU', 'ja-JP', 'ko-KR', 'zh-CN', 'zh-TW',
            'ar-SA', 'ar-EG', 'ar-AE',
            'hi-IN', 'th-TH', 'vi-VN', 'tr-TR',
            'nl-NL', 'sv-SE', 'da-DK', 'no-NO', 'fi-FI'
        ]
        
        # Audio processing parameters
        self.sample_rate = 16000
        self.chunk_duration = 0.5  # 500ms chunks for real-time processing
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        if AUDIO_LIBS_AVAILABLE:
            self._initialize_services()
            self._initialize_voice_profiles()
            self._initialize_vad()
    
    def _initialize_services(self):
        """Initialize enhanced speech recognition and TTS services"""
        try:
            # Initialize speech recognition with optimized settings
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.5  # Reduced for real-time processing
            self.recognizer.phrase_threshold = 0.3
            self.recognizer.non_speaking_duration = 0.5
            
            # Initialize TTS engine with enhanced configuration
            self.tts_engine = pyttsx3.init()
            self._configure_tts_engine()
            
            logger.info("Enhanced voice processing services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice services: {str(e)}")
            self.recognizer = None
            self.tts_engine = None
    
    def _initialize_voice_profiles(self):
        """Initialize voice profiles for different languages and speakers"""
        try:
            if not self.tts_engine:
                return
            
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                # Extract language from voice ID or name
                language = self._extract_language_from_voice(voice)
                gender = getattr(voice, 'gender', 'unknown')
                
                profile = VoiceProfile(
                    voice_id=voice.id,
                    name=voice.name,
                    language=language,
                    gender=gender,
                    age='adult'  # Default age
                )
                
                self.voice_profiles[voice.id] = profile
            
            logger.info(f"Initialized {len(self.voice_profiles)} voice profiles")
            
        except Exception as e:
            logger.error(f"Failed to initialize voice profiles: {str(e)}")
    
    def _initialize_vad(self):
        """Initialize Voice Activity Detection"""
        try:
            if AUDIO_LIBS_AVAILABLE:
                self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2 (0-3)
                logger.info("Voice Activity Detection initialized")
        except Exception as e:
            logger.warning(f"VAD initialization failed: {str(e)}")
            self.vad = None
    
    def _extract_language_from_voice(self, voice) -> str:
        """Extract language code from voice object"""
        try:
            # Try to get language from voice languages attribute
            if hasattr(voice, 'languages') and voice.languages:
                return voice.languages[0]
            
            # Fallback: extract from voice name or ID
            voice_str = (voice.name or voice.id).lower()
            
            # Language mapping based on common patterns
            language_patterns = {
                'english': 'en-US', 'american': 'en-US', 'british': 'en-GB',
                'spanish': 'es-ES', 'french': 'fr-FR', 'german': 'de-DE',
                'italian': 'it-IT', 'portuguese': 'pt-BR', 'russian': 'ru-RU',
                'japanese': 'ja-JP', 'chinese': 'zh-CN', 'korean': 'ko-KR',
                'arabic': 'ar-SA', 'hindi': 'hi-IN'
            }
            
            for pattern, lang_code in language_patterns.items():
                if pattern in voice_str:
                    return lang_code
            
            return 'en-US'  # Default fallback
            
        except Exception:
            return 'en-US'
    
    def _configure_tts_engine(self):
        """Configure TTS engine settings"""
        if not self.tts_engine:
            return
        
        try:
            # Set default properties
            self.tts_engine.setProperty('rate', 200)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.9)  # Volume level
            
            # Get available voices
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Set default voice (first available)
                self.tts_engine.setProperty('voice', voices[0].id)
                
        except Exception as e:
            logger.error(f"Failed to configure TTS engine: {str(e)}")
    
    async def speech_to_text(self, audio_file_path: str, language: str = 'en-US', 
                            real_time: bool = False) -> ProcessingResult:
        """
        Enhanced speech-to-text conversion with real-time processing
        
        Args:
            audio_file_path: Path to audio file
            language: Language code for recognition
            real_time: Enable real-time processing optimizations
            
        Returns:
            ProcessingResult with transcription and metadata
        """
        if not AUDIO_LIBS_AVAILABLE or not self.recognizer:
            raise Exception("Speech recognition not available")
        
        start_time = time.time()
        
        try:
            # Preprocess audio for better recognition
            processed_audio_path = await self._preprocess_audio_for_recognition(
                audio_file_path, real_time
            )
            
            # Load preprocessed audio
            audio_data = self._load_audio_file(processed_audio_path)
            
            # Perform multi-engine speech recognition
            result = await self._multi_engine_recognition(audio_data, language, real_time)
            
            processing_time = time.time() - start_time
            
            # Clean up temporary files
            if processed_audio_path != audio_file_path:
                os.unlink(processed_audio_path)
            
            return ProcessingResult(
                text=result['text'].strip(),
                confidence=result['confidence'],
                language=language,
                timestamp=time.time(),
                processing_time=processing_time,
                noise_reduced=result.get('noise_reduced', False),
                quality_enhanced=result.get('quality_enhanced', False)
            )
            
        except Exception as e:
            logger.error(f"Enhanced speech-to-text error: {str(e)}")
            raise Exception(f"Speech recognition failed: {str(e)}")
    
    async def _preprocess_audio_for_recognition(self, audio_file_path: str, 
                                              real_time: bool = False) -> str:
        """Preprocess audio for optimal speech recognition"""
        try:
            # Load audio
            audio, sr_orig = librosa.load(audio_file_path, sr=None)
            
            # Resample to optimal rate for recognition
            if sr_orig != self.sample_rate:
                audio = librosa.resample(audio, orig_sr=sr_orig, target_sr=self.sample_rate)
            
            # Apply preprocessing pipeline
            if not real_time:
                # Full preprocessing for batch processing
                audio = self._apply_noise_reduction(audio, self.sample_rate)
                audio = self._apply_voice_enhancement(audio, self.sample_rate)
                audio = self._normalize_audio(audio)
            else:
                # Lightweight preprocessing for real-time
                audio = self._apply_realtime_filters(audio, self.sample_rate)
            
            # Save preprocessed audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            sf.write(temp_filename, audio, self.sample_rate)
            return temp_filename
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {str(e)}")
            return audio_file_path  # Return original if preprocessing fails
    
    async def _multi_engine_recognition(self, audio_data: sr.AudioData, 
                                       language: str, real_time: bool = False) -> Dict[str, Any]:
        """Perform recognition using multiple engines for better accuracy"""
        results = []
        
        # Primary: Google Speech Recognition (online)
        try:
            text = self.recognizer.recognize_google(audio_data, language=language)
            results.append({
                'text': text,
                'confidence': 0.9,
                'engine': 'google',
                'online': True
            })
        except (sr.UnknownValueError, sr.RequestError) as e:
            logger.debug(f"Google recognition failed: {str(e)}")
        
        # Secondary: Sphinx (offline) - for fallback
        if not results or not real_time:
            try:
                text = self.recognizer.recognize_sphinx(audio_data)
                results.append({
                    'text': text,
                    'confidence': 0.7,
                    'engine': 'sphinx',
                    'online': False
                })
            except Exception as e:
                logger.debug(f"Sphinx recognition failed: {str(e)}")
        
        # Tertiary: Wit.ai (if available)
        if not results:
            try:
                # This would require Wit.ai API key
                # text = self.recognizer.recognize_wit(audio_data, key="WIT_AI_KEY")
                # results.append({'text': text, 'confidence': 0.8, 'engine': 'wit'})
                pass
            except Exception:
                pass
        
        if not results:
            raise Exception("No recognition engine could process the audio")
        
        # Return best result (highest confidence)
        best_result = max(results, key=lambda x: x['confidence'])
        
        return {
            'text': best_result['text'],
            'confidence': best_result['confidence'],
            'engine': best_result['engine'],
            'noise_reduced': True,
            'quality_enhanced': True
        }
    
    async def text_to_speech(self, text: str, config: Dict[str, Any] = None, 
                            voice_profile: Optional[VoiceProfile] = None) -> bytes:
        """
        Enhanced text-to-speech conversion with multiple voice options
        
        Args:
            text: Text to convert to speech
            config: Voice configuration options
            voice_profile: Specific voice profile to use
            
        Returns:
            Audio data as bytes
        """
        if not AUDIO_LIBS_AVAILABLE or not self.tts_engine:
            raise Exception("Text-to-speech not available")
        
        try:
            # Apply voice profile or configuration
            if voice_profile:
                self._apply_voice_profile(voice_profile)
            elif config:
                self._apply_tts_config(config)
            
            # Preprocess text for better synthesis
            processed_text = self._preprocess_text_for_tts(text, config)
            
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                # Generate speech with enhanced quality
                await self._generate_enhanced_speech(processed_text, temp_filename, config)
                
                # Post-process audio for quality enhancement
                enhanced_audio_path = await self._enhance_tts_audio(temp_filename)
                
                # Read generated audio file
                with open(enhanced_audio_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # Clean up temporary files
                os.unlink(temp_filename)
                if enhanced_audio_path != temp_filename:
                    os.unlink(enhanced_audio_path)
                
                return audio_data
                
            except Exception as e:
                # Clean up temporary files on error
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                raise e
                
        except Exception as e:
            logger.error(f"Enhanced text-to-speech error: {str(e)}")
            raise Exception(f"Speech synthesis failed: {str(e)}")
    
    def _preprocess_text_for_tts(self, text: str, config: Dict[str, Any] = None) -> str:
        """Preprocess text for optimal speech synthesis"""
        try:
            # Basic text cleaning
            processed_text = text.strip()
            
            # Handle abbreviations and acronyms
            abbreviations = {
                'Dr.': 'Doctor',
                'Mr.': 'Mister',
                'Mrs.': 'Missus',
                'Ms.': 'Miss',
                'Prof.': 'Professor',
                'etc.': 'etcetera',
                'vs.': 'versus',
                'e.g.': 'for example',
                'i.e.': 'that is'
            }
            
            for abbrev, expansion in abbreviations.items():
                processed_text = processed_text.replace(abbrev, expansion)
            
            # Handle numbers and dates (basic implementation)
            # In production, use more sophisticated text normalization
            
            # Add pauses for better speech flow
            processed_text = processed_text.replace('.', '. ')
            processed_text = processed_text.replace(',', ', ')
            processed_text = processed_text.replace(';', '; ')
            
            # Remove excessive whitespace
            processed_text = ' '.join(processed_text.split())
            
            return processed_text
            
        except Exception as e:
            logger.warning(f"Text preprocessing failed: {str(e)}")
            return text
    
    async def _generate_enhanced_speech(self, text: str, output_path: str, 
                                       config: Dict[str, Any] = None):
        """Generate speech with enhanced quality settings"""
        try:
            # Run TTS generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._sync_generate_speech,
                text,
                output_path
            )
        except Exception as e:
            logger.error(f"Speech generation failed: {str(e)}")
            raise
    
    def _sync_generate_speech(self, text: str, output_path: str):
        """Synchronous speech generation"""
        self.tts_engine.save_to_file(text, output_path)
        self.tts_engine.runAndWait()
    
    async def _enhance_tts_audio(self, audio_path: str) -> str:
        """Post-process TTS audio for quality enhancement"""
        try:
            # Load generated audio
            audio, sample_rate = librosa.load(audio_path, sr=None)
            
            # Apply audio enhancements
            enhanced_audio = self._apply_tts_enhancements(audio, sample_rate)
            
            # Save enhanced audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                enhanced_path = temp_file.name
            
            sf.write(enhanced_path, enhanced_audio, sample_rate)
            return enhanced_path
            
        except Exception as e:
            logger.warning(f"TTS audio enhancement failed: {str(e)}")
            return audio_path  # Return original if enhancement fails
    
    def _apply_tts_enhancements(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply enhancements to TTS-generated audio"""
        try:
            # Normalize audio levels
            audio = librosa.util.normalize(audio)
            
            # Apply gentle compression for consistent volume
            threshold = 0.8
            ratio = 3.0
            audio = np.where(
                np.abs(audio) > threshold,
                np.sign(audio) * (threshold + (np.abs(audio) - threshold) / ratio),
                audio
            )
            
            # Apply subtle reverb for more natural sound
            # This is a simplified implementation
            delay_samples = int(0.05 * sample_rate)  # 50ms delay
            reverb = np.zeros_like(audio)
            reverb[delay_samples:] = audio[:-delay_samples] * 0.3
            audio = audio + reverb
            
            # Final normalization
            audio = librosa.util.normalize(audio)
            
            return audio
            
        except Exception as e:
            logger.warning(f"TTS enhancement failed: {str(e)}")
            return audio
    
    def _apply_voice_profile(self, profile: VoiceProfile):
        """Apply a specific voice profile to TTS engine"""
        try:
            if not self.tts_engine:
                return
            
            self.tts_engine.setProperty('voice', profile.voice_id)
            self.tts_engine.setProperty('rate', profile.rate)
            self.tts_engine.setProperty('volume', profile.volume)
            
            logger.debug(f"Applied voice profile: {profile.name}")
            
        except Exception as e:
            logger.warning(f"Failed to apply voice profile: {str(e)}")
    
    def get_voice_profiles_by_language(self, language: str) -> List[VoiceProfile]:
        """Get available voice profiles for a specific language"""
        matching_profiles = []
        
        for profile in self.voice_profiles.values():
            if profile.language.startswith(language[:2]):  # Match language prefix
                matching_profiles.append(profile)
        
        return matching_profiles
    
    def get_recommended_voice_profile(self, language: str, gender: str = None) -> Optional[VoiceProfile]:
        """Get recommended voice profile for language and gender"""
        profiles = self.get_voice_profiles_by_language(language)
        
        if not profiles:
            return None
        
        if gender:
            gender_profiles = [p for p in profiles if p.gender.lower() == gender.lower()]
            if gender_profiles:
                profiles = gender_profiles
        
        # Return first available profile (could be enhanced with quality scoring)
        return profiles[0]
    
    def process_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Process audio for noise reduction and quality enhancement
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Dictionary with processed audio data
        """
        if not AUDIO_LIBS_AVAILABLE:
            # Return original audio if processing libraries not available
            with open(audio_file_path, 'rb') as f:
                return {
                    'audio_data': f.read(),
                    'noise_reduced': False,
                    'quality_enhanced': False
                }
        
        try:
            # Load audio file
            audio, sample_rate = librosa.load(audio_file_path, sr=None)
            
            # Apply noise reduction
            audio_denoised = self._reduce_noise(audio, sample_rate)
            
            # Apply quality enhancement
            audio_enhanced = self._enhance_quality(audio_denoised, sample_rate)
            
            # Convert back to audio file format
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            try:
                # Save processed audio
                sf.write(temp_filename, audio_enhanced, sample_rate)
                
                # Read processed audio data
                with open(temp_filename, 'rb') as audio_file:
                    processed_audio_data = audio_file.read()
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
                return {
                    'audio_data': processed_audio_data,
                    'noise_reduced': True,
                    'quality_enhanced': True
                }
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                raise e
                
        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            # Return original audio on processing failure
            with open(audio_file_path, 'rb') as f:
                return {
                    'audio_data': f.read(),
                    'noise_reduced': False,
                    'quality_enhanced': False
                }
    
    async def start_streaming_session(self, language: str = 'en-US', 
                                     real_time: bool = True) -> str:
        """
        Start an enhanced streaming audio processing session
        
        Args:
            language: Language code for recognition
            real_time: Enable real-time processing optimizations
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        self.streaming_sessions[session_id] = {
            'language': language,
            'created_at': datetime.now(),
            'audio_buffer': io.BytesIO(),
            'partial_results': [],
            'final_result': None,
            'real_time': real_time,
            'chunk_count': 0,
            'total_audio_duration': 0.0,
            'voice_activity_detected': False,
            'silence_duration': 0.0,
            'processing_queue': asyncio.Queue(),
            'is_active': True
        }
        
        # Start background processing task for this session
        asyncio.create_task(self._process_streaming_session(session_id))
        
        logger.info(f"Started enhanced streaming session: {session_id}")
        return session_id
    
    async def process_streaming_chunk(self, session_id: str, audio_chunk_path: str) -> Dict[str, Any]:
        """
        Process a streaming audio chunk with enhanced real-time capabilities
        
        Args:
            session_id: Streaming session ID
            audio_chunk_path: Path to audio chunk file
            
        Returns:
            Processing result with enhanced metadata
        """
        if session_id not in self.streaming_sessions:
            raise Exception("Invalid session ID")
        
        session = self.streaming_sessions[session_id]
        
        try:
            # Load and validate audio chunk
            with open(audio_chunk_path, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
            
            # Create streaming chunk object
            chunk = StreamingChunk(
                session_id=session_id,
                chunk_id=str(uuid.uuid4()),
                audio_data=chunk_data,
                timestamp=time.time()
            )
            
            # Add chunk to processing queue
            await session['processing_queue'].put(chunk)
            
            # Update session statistics
            session['chunk_count'] += 1
            
            # Detect voice activity in chunk
            has_voice = self._detect_voice_activity(chunk_data)
            
            if has_voice:
                session['voice_activity_detected'] = True
                session['silence_duration'] = 0.0
            else:
                session['silence_duration'] += self.chunk_duration
            
            # Return immediate response for real-time feedback
            return {
                'session_id': session_id,
                'chunk_id': chunk.chunk_id,
                'voice_detected': has_voice,
                'chunk_number': session['chunk_count'],
                'processing_status': 'queued',
                'timestamp': chunk.timestamp
            }
            
        except Exception as e:
            logger.error(f"Enhanced streaming chunk processing error: {str(e)}")
            raise Exception(f"Failed to process streaming chunk: {str(e)}")
    
    async def _process_streaming_session(self, session_id: str):
        """Background task to process streaming audio chunks"""
        session = self.streaming_sessions.get(session_id)
        if not session:
            return
        
        accumulated_audio = []
        last_recognition_time = time.time()
        recognition_interval = 1.0  # Process every 1 second
        
        try:
            while session['is_active']:
                try:
                    # Wait for new chunk with timeout
                    chunk = await asyncio.wait_for(
                        session['processing_queue'].get(), 
                        timeout=0.5
                    )
                    
                    # Add chunk to accumulated audio
                    accumulated_audio.append(chunk.audio_data)
                    
                    # Check if it's time to run recognition
                    current_time = time.time()
                    if (current_time - last_recognition_time >= recognition_interval or
                        session['silence_duration'] > 1.0):  # Process on silence
                        
                        if accumulated_audio:
                            # Process accumulated audio
                            result = await self._process_accumulated_audio(
                                session_id, accumulated_audio
                            )
                            
                            if result and result.text.strip():
                                # Store partial result
                                session['partial_results'].append(result)
                                
                                # Notify about new partial result
                                # This could trigger a callback or event
                                logger.debug(f"Partial result for {session_id}: {result.text}")
                            
                            # Reset accumulation
                            accumulated_audio = []
                            last_recognition_time = current_time
                    
                except asyncio.TimeoutError:
                    # No new chunks, continue processing
                    continue
                except Exception as e:
                    logger.error(f"Error in streaming session processing: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Streaming session {session_id} processing failed: {str(e)}")
        finally:
            # Clean up session
            if session_id in self.streaming_sessions:
                self.streaming_sessions[session_id]['is_active'] = False
    
    async def _process_accumulated_audio(self, session_id: str, 
                                        audio_chunks: List[bytes]) -> Optional[ProcessingResult]:
        """Process accumulated audio chunks for recognition"""
        try:
            if not audio_chunks:
                return None
            
            # Combine audio chunks
            combined_audio = b''.join(audio_chunks)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(combined_audio)
                temp_filename = temp_file.name
            
            try:
                session = self.streaming_sessions[session_id]
                
                # Process with real-time optimizations
                result = await self.speech_to_text(
                    temp_filename, 
                    session['language'], 
                    real_time=session['real_time']
                )
                
                # Clean up temporary file
                os.unlink(temp_filename)
                
                return result
                
            except Exception as e:
                # Clean up temporary file on error
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                logger.debug(f"Recognition failed for accumulated audio: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing accumulated audio: {str(e)}")
            return None
    
    async def get_streaming_results(self, session_id: str) -> Dict[str, Any]:
        """Get current streaming results for a session"""
        if session_id not in self.streaming_sessions:
            raise Exception("Invalid session ID")
        
        session = self.streaming_sessions[session_id]
        
        # Get latest partial results
        recent_results = session['partial_results'][-5:]  # Last 5 results
        
        return {
            'session_id': session_id,
            'partial_results': [
                {
                    'text': result.text,
                    'confidence': result.confidence,
                    'timestamp': result.timestamp
                }
                for result in recent_results
            ],
            'voice_activity_detected': session['voice_activity_detected'],
            'chunk_count': session['chunk_count'],
            'session_duration': (datetime.now() - session['created_at']).total_seconds(),
            'is_active': session['is_active']
        }
    
    async def stop_streaming_session(self, session_id: str) -> Dict[str, Any]:
        """
        Stop an enhanced streaming audio processing session
        
        Args:
            session_id: Session ID to stop
            
        Returns:
            Final processing result with comprehensive statistics
        """
        if session_id not in self.streaming_sessions:
            raise Exception("Invalid session ID")
        
        session = self.streaming_sessions[session_id]
        
        try:
            # Mark session as inactive to stop background processing
            session['is_active'] = False
            
            # Wait a moment for background processing to complete
            await asyncio.sleep(0.1)
            
            # Process any remaining chunks in queue
            remaining_chunks = []
            try:
                while not session['processing_queue'].empty():
                    chunk = session['processing_queue'].get_nowait()
                    remaining_chunks.append(chunk.audio_data)
            except asyncio.QueueEmpty:
                pass
            
            # Process remaining audio if any
            if remaining_chunks:
                final_chunk_result = await self._process_accumulated_audio(
                    session_id, remaining_chunks
                )
                if final_chunk_result and final_chunk_result.text.strip():
                    session['partial_results'].append(final_chunk_result)
            
            # Determine final result
            final_result = self._determine_final_result(session)
            session['final_result'] = final_result
            
            # Calculate session statistics
            session_duration = (datetime.now() - session['created_at']).total_seconds()
            
            # Prepare comprehensive result
            result = {
                'session_id': session_id,
                'final_text': final_result.text if final_result else '',
                'confidence': final_result.confidence if final_result else 0.0,
                'language': session['language'],
                'is_final': True,
                'statistics': {
                    'duration': session_duration,
                    'chunks_processed': session['chunk_count'],
                    'partial_results_count': len(session['partial_results']),
                    'voice_activity_detected': session['voice_activity_detected'],
                    'average_processing_time': (
                        sum(r.processing_time for r in session['partial_results']) / 
                        len(session['partial_results'])
                    ) if session['partial_results'] else 0.0,
                    'total_silence_duration': session['silence_duration']
                },
                'partial_results': [
                    {
                        'text': result.text,
                        'confidence': result.confidence,
                        'timestamp': result.timestamp,
                        'processing_time': result.processing_time
                    }
                    for result in session['partial_results']
                ]
            }
            
            # Clean up session
            del self.streaming_sessions[session_id]
            
            logger.info(f"Stopped enhanced streaming session: {session_id}")
            return result
            
        except Exception as e:
            # Clean up session on error
            if session_id in self.streaming_sessions:
                self.streaming_sessions[session_id]['is_active'] = False
                del self.streaming_sessions[session_id]
            
            logger.error(f"Error stopping enhanced streaming session: {str(e)}")
            raise Exception(f"Failed to stop streaming session: {str(e)}")
    
    def _determine_final_result(self, session: Dict[str, Any]) -> Optional[ProcessingResult]:
        """Determine the best final result from partial results"""
        partial_results = session['partial_results']
        
        if not partial_results:
            return None
        
        # If only one result, return it
        if len(partial_results) == 1:
            return partial_results[0]
        
        # Combine results intelligently
        # For now, use the result with highest confidence
        # In production, you might want to combine multiple results
        best_result = max(partial_results, key=lambda x: x.confidence)
        
        # Optionally, combine text from multiple results
        # This is a simplified approach - more sophisticated text merging could be used
        if len(partial_results) > 1:
            # Combine unique text segments
            all_text = ' '.join(result.text for result in partial_results if result.text.strip())
            if all_text.strip():
                best_result.text = all_text
        
        return best_result
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.supported_languages
    
    def get_available_voices(self, language: str = 'en-US') -> List[Dict[str, Any]]:
        """
        Get available voices for text-to-speech
        
        Args:
            language: Language code to filter voices
            
        Returns:
            List of available voices
        """
        if not self.tts_engine:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            available_voices = []
            
            for voice in voices:
                # Filter by language if specified
                if language and language.lower() not in voice.id.lower():
                    continue
                
                available_voices.append({
                    'id': voice.id,
                    'name': voice.name,
                    'language': getattr(voice, 'languages', [language]),
                    'gender': getattr(voice, 'gender', 'unknown')
                })
            
            return available_voices
            
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []
    
    def get_voice_config(self) -> Dict[str, Any]:
        """Get current voice configuration"""
        if not self.tts_engine:
            return {}
        
        try:
            return {
                'rate': self.tts_engine.getProperty('rate'),
                'volume': self.tts_engine.getProperty('volume'),
                'voice': self.tts_engine.getProperty('voice')
            }
        except Exception as e:
            logger.error(f"Error getting voice config: {str(e)}")
            return {}
    
    def update_voice_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update voice configuration
        
        Args:
            config: Configuration updates
            
        Returns:
            Updated configuration
        """
        if not self.tts_engine:
            return {}
        
        try:
            if 'rate' in config:
                self.tts_engine.setProperty('rate', config['rate'])
            
            if 'volume' in config:
                self.tts_engine.setProperty('volume', config['volume'])
            
            if 'voice' in config:
                self.tts_engine.setProperty('voice', config['voice'])
            
            return self.get_voice_config()
            
        except Exception as e:
            logger.error(f"Error updating voice config: {str(e)}")
            return self.get_voice_config()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on voice processing services"""
        status = {
            'status': 'healthy',
            'services': {
                'speech_recognition': bool(self.recognizer),
                'text_to_speech': bool(self.tts_engine),
                'audio_processing': AUDIO_LIBS_AVAILABLE
            },
            'active_sessions': len(self.streaming_sessions),
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if any critical services are down
        if not any(status['services'].values()):
            status['status'] = 'unhealthy'
        
        return status
    
    def _load_audio_file(self, audio_file_path: str) -> sr.AudioData:
        """Load audio file for speech recognition"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record audio data
                audio_data = self.recognizer.record(source)
            
            return audio_data
            
        except Exception as e:
            # Try alternative loading method for different formats
            try:
                # Convert to WAV format if needed
                audio, sample_rate = librosa.load(audio_file_path, sr=16000)
                
                # Convert to AudioData format
                audio_int16 = (audio * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                
                return sr.AudioData(audio_bytes, sample_rate, 2)
                
            except Exception as e2:
                raise Exception(f"Failed to load audio file: {str(e2)}")
    
    def _apply_tts_config(self, config: Dict[str, Any]):
        """Apply TTS configuration"""
        try:
            if 'rate' in config:
                self.tts_engine.setProperty('rate', config['rate'])
            
            if 'volume' in config:
                self.tts_engine.setProperty('volume', config['volume'])
            
            if 'voice' in config:
                self.tts_engine.setProperty('voice', config['voice'])
                
        except Exception as e:
            logger.warning(f"Failed to apply TTS config: {str(e)}")
    
    def _apply_noise_reduction(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Advanced noise reduction using spectral subtraction and Wiener filtering"""
        try:
            # Compute short-time Fourier transform
            stft = librosa.stft(audio, hop_length=256, n_fft=1024)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Estimate noise from first 0.5 seconds (assuming initial silence)
            noise_frames = min(int(0.5 * sample_rate / 256), magnitude.shape[1] // 4)
            noise_magnitude = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            
            # Apply enhanced spectral subtraction
            alpha = 2.5  # Over-subtraction factor
            beta = 0.02  # Spectral floor
            
            # Calculate SNR estimate
            snr_estimate = magnitude / (noise_magnitude + 1e-10)
            
            # Apply Wiener-like filtering
            wiener_gain = snr_estimate / (snr_estimate + 1)
            
            # Combine spectral subtraction with Wiener filtering
            clean_magnitude = magnitude * wiener_gain
            clean_magnitude = np.maximum(clean_magnitude, beta * magnitude)
            
            # Apply smoothing to reduce musical noise
            clean_magnitude = scipy.signal.medfilt(clean_magnitude, kernel_size=(1, 3))
            
            # Reconstruct audio
            clean_stft = clean_magnitude * np.exp(1j * phase)
            clean_audio = librosa.istft(clean_stft, hop_length=256)
            
            return clean_audio
            
        except Exception as e:
            logger.warning(f"Advanced noise reduction failed: {str(e)}")
            return self._simple_noise_reduction(audio, sample_rate)
    
    def _simple_noise_reduction(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Fallback simple noise reduction"""
        try:
            # High-pass filter to remove low-frequency noise
            nyquist = sample_rate / 2
            low_cutoff = 80 / nyquist
            b, a = scipy.signal.butter(4, low_cutoff, btype='high')
            filtered_audio = scipy.signal.filtfilt(b, a, audio)
            
            return filtered_audio
            
        except Exception as e:
            logger.warning(f"Simple noise reduction failed: {str(e)}")
            return audio
    
    def _apply_voice_enhancement(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Advanced voice enhancement for speech clarity"""
        try:
            # Apply pre-emphasis filter to boost high frequencies
            pre_emphasis = 0.97
            emphasized = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])
            
            # Apply formant enhancement (boost speech frequencies)
            # Design bandpass filter for speech frequencies (300-3400 Hz)
            nyquist = sample_rate / 2
            low_freq = 300 / nyquist
            high_freq = 3400 / nyquist
            
            b, a = scipy.signal.butter(4, [low_freq, high_freq], btype='band')
            speech_band = scipy.signal.filtfilt(b, a, emphasized)
            
            # Combine original with enhanced speech band
            enhanced = emphasized + 0.3 * speech_band
            
            # Apply dynamic range compression
            enhanced = self._apply_compression(enhanced)
            
            # Final normalization
            enhanced = librosa.util.normalize(enhanced)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Voice enhancement failed: {str(e)}")
            return audio
    
    def _apply_compression(self, audio: np.ndarray, threshold: float = 0.7, 
                          ratio: float = 4.0, attack: float = 0.003, 
                          release: float = 0.1) -> np.ndarray:
        """Apply dynamic range compression"""
        try:
            # Simple compression implementation
            compressed = np.copy(audio)
            
            # Apply compression where signal exceeds threshold
            over_threshold = np.abs(audio) > threshold
            compressed[over_threshold] = np.sign(audio[over_threshold]) * (
                threshold + (np.abs(audio[over_threshold]) - threshold) / ratio
            )
            
            return compressed
            
        except Exception as e:
            logger.warning(f"Compression failed: {str(e)}")
            return audio
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio with peak limiting"""
        try:
            # Peak normalization
            peak = np.max(np.abs(audio))
            if peak > 0:
                audio = audio / peak * 0.95  # Leave some headroom
            
            # RMS normalization for consistent loudness
            rms = np.sqrt(np.mean(audio**2))
            target_rms = 0.2
            if rms > 0:
                audio = audio * (target_rms / rms)
            
            # Final peak limiting
            audio = np.clip(audio, -0.95, 0.95)
            
            return audio
            
        except Exception as e:
            logger.warning(f"Audio normalization failed: {str(e)}")
            return audio
    
    def _apply_realtime_filters(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply lightweight filters for real-time processing"""
        try:
            # Simple high-pass filter for noise reduction
            nyquist = sample_rate / 2
            cutoff = 80 / nyquist
            b, a = scipy.signal.butter(2, cutoff, btype='high')
            filtered = scipy.signal.filtfilt(b, a, audio)
            
            # Basic normalization
            filtered = librosa.util.normalize(filtered)
            
            return filtered
            
        except Exception as e:
            logger.warning(f"Real-time filtering failed: {str(e)}")
            return audio
    
    def _detect_voice_activity(self, audio_chunk: bytes, sample_rate: int = 16000) -> bool:
        """Detect voice activity in audio chunk"""
        try:
            if not self.vad:
                return True  # Assume voice activity if VAD not available
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)
            
            # Ensure chunk is correct length for VAD (10, 20, or 30ms)
            chunk_duration_ms = 20  # 20ms chunks
            chunk_samples = int(sample_rate * chunk_duration_ms / 1000)
            
            if len(audio_array) < chunk_samples:
                # Pad with zeros if too short
                audio_array = np.pad(audio_array, (0, chunk_samples - len(audio_array)))
            elif len(audio_array) > chunk_samples:
                # Truncate if too long
                audio_array = audio_array[:chunk_samples]
            
            # Convert to bytes for VAD
            audio_bytes = audio_array.astype(np.int16).tobytes()
            
            # Detect voice activity
            return self.vad.is_speech(audio_bytes, sample_rate)
            
        except Exception as e:
            logger.debug(f"VAD failed: {str(e)}")
            return True  # Default to assuming voice activity