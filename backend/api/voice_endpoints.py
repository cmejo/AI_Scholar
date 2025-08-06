"""
Voice processing API endpoints for speech-to-text and text-to-speech
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import tempfile
import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from ..services.voice_processing_service import VoiceProcessingService
from ..services.voice_nlp_service import VoiceNLPService
from ..core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize voice processing service
voice_service = VoiceProcessingService()
voice_nlp_service = VoiceNLPService()

# Pydantic models
class TextToSpeechRequest(BaseModel):
    text: str
    config: Optional[Dict[str, Any]] = None

class VoiceConfigUpdate(BaseModel):
    rate: Optional[float] = None
    volume: Optional[float] = None
    voice: Optional[str] = None

class StreamingStartRequest(BaseModel):
    language: Optional[str] = "en-US"

class StreamingStopRequest(BaseModel):
    session_id: str

class CommandProcessRequest(BaseModel):
    text: str
    session_id: Optional[str] = "default"
    language: Optional[str] = "en"

class MultilingualTTSRequest(BaseModel):
    text: str
    language: str
    config: Optional[Dict[str, Any]] = None

class TranslationRequest(BaseModel):
    text: str
    from_language: str = "auto"
    to_language: str = "en"

@router.post('/speech-to-text')
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = Form("en-US"),
    real_time: str = Form("false")
):
    """
    Enhanced speech-to-text conversion with real-time processing support
    """
    try:
        # Validate audio file
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file selected")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Process speech to text with enhanced features
            real_time_mode = real_time.lower() == "true"
            result = await voice_service.speech_to_text(temp_filename, language, real_time_mode)
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            return {
                'text': result.text,
                'confidence': result.confidence,
                'language': result.language,
                'timestamp': result.timestamp,
                'processing_time': result.processing_time,
                'noise_reduced': result.noise_reduced,
                'quality_enhanced': result.quality_enhanced
            }
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            raise e
            
    except Exception as e:
        logger.error(f"Enhanced speech-to-text error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {str(e)}")

@router.post('/text-to-speech')
async def text_to_speech(request: TextToSpeechRequest):
    """
    Convert text to speech audio
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Generate speech audio
        audio_data = voice_service.text_to_speech(request.text, request.config or {})
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        # Return audio file
        return FileResponse(
            temp_filename,
            media_type='audio/wav',
            filename='speech.wav'
        )
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@router.post('/process-audio')
async def process_audio(audio: UploadFile = File(...)):
    """
    Process audio for noise reduction and quality enhancement
    """
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file selected")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Process audio
            processed_audio = voice_service.process_audio(temp_filename)
            
            # Clean up original temporary file
            os.unlink(temp_filename)
            
            # Create temporary file for processed audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as processed_file:
                processed_file.write(processed_audio['audio_data'])
                processed_filename = processed_file.name
            
            # Return processed audio file
            return FileResponse(
                processed_filename,
                media_type='audio/wav',
                filename='processed_audio.wav'
            )
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            raise e
            
    except Exception as e:
        logger.error(f"Audio processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@router.get('/supported-languages')
async def get_supported_languages():
    """
    Get list of supported languages for voice processing
    """
    try:
        languages = voice_service.get_supported_languages()
        return {'languages': languages}
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get supported languages")

@router.get('/available-voices')
async def get_available_voices(language: str = "en-US"):
    """
    Get list of available voices for text-to-speech
    """
    try:
        voices = voice_service.get_available_voices(language)
        return {'voices': voices}
        
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get available voices")

@router.get('/voice-config')
async def get_voice_config():
    """
    Get voice configuration
    """
    try:
        config = voice_service.get_voice_config()
        return config
        
    except Exception as e:
        logger.error(f"Error getting voice config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voice configuration")

@router.post('/voice-config')
async def update_voice_config(config_update: VoiceConfigUpdate):
    """
    Update voice configuration
    """
    try:
        config_dict = config_update.dict(exclude_unset=True)
        if not config_dict:
            raise HTTPException(status_code=400, detail="No configuration data provided")
        
        updated_config = voice_service.update_voice_config(config_dict)
        return updated_config
        
    except Exception as e:
        logger.error(f"Error updating voice config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update voice configuration")

@router.post('/streaming/start')
async def start_streaming(request: StreamingStartRequest):
    """
    Start enhanced streaming audio processing session
    """
    try:
        session_id = await voice_service.start_streaming_session(request.language, real_time=True)
        
        return {
            'session_id': session_id,
            'status': 'started',
            'language': request.language,
            'real_time': True
        }
        
    except Exception as e:
        logger.error(f"Error starting streaming session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start streaming session")

@router.post('/streaming/process')
async def process_streaming_audio(
    session_id: str = Form(...),
    audio_chunk: UploadFile = File(...)
):
    """
    Process streaming audio chunk with enhanced real-time capabilities
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="No session ID provided")
        
        if not audio_chunk.filename:
            raise HTTPException(status_code=400, detail="No audio chunk provided")
        
        # Save chunk temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio_chunk.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Process streaming chunk with enhanced features
            result = await voice_service.process_streaming_chunk(session_id, temp_filename)
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            return result
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            raise e
            
    except Exception as e:
        logger.error(f"Error processing streaming audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process streaming audio")

@router.post('/streaming/stop')
async def stop_streaming(request: StreamingStopRequest):
    """
    Stop streaming audio processing session
    """
    try:
        result = await voice_service.stop_streaming_session(request.session_id)
        return result
        
    except Exception as e:
        logger.error(f"Error stopping streaming session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to stop streaming session")

@router.get('/streaming/results/{session_id}')
async def get_streaming_results(session_id: str):
    """
    Get current streaming results for a session
    """
    try:
        results = await voice_service.get_streaming_results(session_id)
        return results
        
    except Exception as e:
        logger.error(f"Error getting streaming results: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get streaming results")

@router.post('/process-command')
async def process_voice_command(request: CommandProcessRequest):
    """
    Process voice command for intent and entity extraction
    """
    try:
        command = await voice_nlp_service.process_command(
            text=request.text,
            session_id=request.session_id,
            language=request.language
        )
        
        # Convert dataclass to dict for JSON response
        return {
            'id': command.id,
            'text': command.text,
            'intent': {
                'name': command.intent.name,
                'confidence': command.intent.confidence,
                'parameters': command.intent.parameters
            },
            'entities': [
                {
                    'type': entity.type,
                    'value': entity.value,
                    'confidence': entity.confidence,
                    'start': entity.start,
                    'end': entity.end
                }
                for entity in command.entities
            ],
            'confidence': command.confidence,
            'timestamp': command.timestamp,
            'language': command.language
        }
        
    except Exception as e:
        logger.error(f"Command processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Command processing failed: {str(e)}")

@router.get('/conversation-context/{session_id}')
async def get_conversation_context(session_id: str):
    """
    Get conversation context for a session
    """
    try:
        context = voice_nlp_service.get_conversation_context(session_id)
        
        if not context:
            return {
                'session_id': session_id,
                'history': [],
                'current_topic': None,
                'user_preferences': {},
                'last_command': None
            }
        
        return {
            'session_id': context.session_id,
            'history': [
                {
                    'id': cmd.id,
                    'text': cmd.text,
                    'intent': cmd.intent.name,
                    'confidence': cmd.confidence,
                    'timestamp': cmd.timestamp
                }
                for cmd in context.history[-10:]  # Last 10 commands
            ],
            'current_topic': context.current_topic,
            'user_preferences': context.user_preferences,
            'last_command': {
                'id': context.last_command.id,
                'text': context.last_command.text,
                'intent': context.last_command.intent.name,
                'confidence': context.last_command.confidence
            } if context.last_command else None
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get conversation context")

@router.delete('/conversation-context/{session_id}')
async def clear_conversation_context(session_id: str):
    """
    Clear conversation context for a session
    """
    try:
        voice_nlp_service.clear_conversation_context(session_id)
        return {'success': True, 'message': f'Conversation context cleared for session {session_id}'}
        
    except Exception as e:
        logger.error(f"Error clearing conversation context: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear conversation context")

@router.get('/command-suggestions')
async def get_command_suggestions(partial_text: str, limit: int = 5):
    """
    Get command suggestions based on partial text
    """
    try:
        suggestions = voice_nlp_service.get_command_suggestions(partial_text, limit)
        return {'suggestions': suggestions}
        
    except Exception as e:
        logger.error(f"Error getting command suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get command suggestions")

@router.get('/session-analytics/{session_id}')
async def get_session_analytics(session_id: str):
    """
    Get analytics for a conversation session
    """
    try:
        analytics = voice_nlp_service.analyze_command_patterns(session_id)
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting session analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get session analytics")

@router.post('/detect-language')
async def detect_language(audio: UploadFile = File(...)):
    """
    Detect language from audio input
    """
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Detect language using voice processing service
            # This is a simplified implementation - in production you'd use
            # more sophisticated language detection models
            result = voice_service.speech_to_text(temp_filename, 'auto')
            
            # Simple language detection based on text patterns
            detected_language = 'en-US'  # Default fallback
            confidence = 0.8
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            return {
                'detected_language': detected_language,
                'confidence': confidence,
                'alternatives': [
                    {'language': 'es-ES', 'confidence': 0.6},
                    {'language': 'fr-FR', 'confidence': 0.4}
                ]
            }
            
        except Exception as e:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            raise e
            
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")

@router.post('/multilingual-speech-to-text')
async def multilingual_speech_to_text(
    audio: UploadFile = File(...),
    language: str = Form("en-US")
):
    """
    Multilingual speech-to-text conversion
    """
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_filename = temp_file.name
        
        try:
            # Process speech to text with specified language
            result = voice_service.speech_to_text(temp_filename, language)
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            return {
                'text': result['text'],
                'confidence': result['confidence'],
                'language': result['language'],
                'timestamp': result['timestamp'],
                'detected_language': language,
                'original_language': language
            }
            
        except Exception as e:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            raise e
            
    except Exception as e:
        logger.error(f"Multilingual speech-to-text error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Multilingual speech recognition failed: {str(e)}")

@router.post('/multilingual-text-to-speech')
async def multilingual_text_to_speech(request: MultilingualTTSRequest):
    """
    Multilingual text-to-speech conversion
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Configure TTS for specific language
        config = request.config or {}
        config['language'] = request.language
        
        # Generate speech audio
        audio_data = voice_service.text_to_speech(request.text, config)
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        # Return audio file
        return FileResponse(
            temp_filename,
            media_type='audio/wav',
            filename=f'speech_{request.language}.wav'
        )
        
    except Exception as e:
        logger.error(f"Multilingual text-to-speech error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Multilingual speech synthesis failed: {str(e)}")

@router.post('/translate')
async def translate_text(request: TranslationRequest):
    """
    Translate text between languages
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # This is a simplified implementation
        # In production, you would integrate with translation services like:
        # - Google Translate API
        # - Microsoft Translator
        # - AWS Translate
        # - Local translation models
        
        # For now, return a mock translation
        translated_text = f"[Translated from {request.from_language} to {request.to_language}] {request.text}"
        
        return {
            'text': translated_text,
            'target_language': request.to_language,
            'confidence': 0.85,
            'source_language': request.from_language
        }
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@router.get('/supported-languages-detailed')
async def get_supported_languages_detailed():
    """
    Get detailed information about supported languages
    """
    try:
        # This would typically come from a configuration file or database
        supported_languages = [
            {
                'code': 'en-US',
                'name': 'English (US)',
                'native_name': 'English',
                'region': 'United States',
                'rtl': False,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.95
            },
            {
                'code': 'es-ES',
                'name': 'Spanish (Spain)',
                'native_name': 'Español',
                'region': 'Spain',
                'rtl': False,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.9
            },
            {
                'code': 'fr-FR',
                'name': 'French (France)',
                'native_name': 'Français',
                'region': 'France',
                'rtl': False,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.9
            },
            {
                'code': 'de-DE',
                'name': 'German (Germany)',
                'native_name': 'Deutsch',
                'region': 'Germany',
                'rtl': False,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.9
            },
            {
                'code': 'ja-JP',
                'name': 'Japanese (Japan)',
                'native_name': '日本語',
                'region': 'Japan',
                'rtl': False,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.8
            },
            {
                'code': 'zh-CN',
                'name': 'Chinese (Simplified)',
                'native_name': '中文',
                'region': 'China',
                'rtl': False,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.8
            },
            {
                'code': 'ar-SA',
                'name': 'Arabic (Saudi Arabia)',
                'native_name': 'العربية',
                'region': 'Saudi Arabia',
                'rtl': True,
                'voice_support': True,
                'recognition_support': True,
                'confidence': 0.75
            }
        ]
        
        return {'languages': supported_languages}
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get supported languages")

@router.get('/language-patterns/{language}')
async def get_language_patterns(language: str):
    """
    Get voice command patterns for a specific language
    """
    try:
        # This would typically come from a language pattern database
        patterns = {
            'en-US': {
                'search': ['search for', 'find', 'look for', 'show me'],
                'navigate': ['go to', 'open', 'navigate to', 'take me to'],
                'document': ['upload document', 'open file', 'delete document', 'summarize'],
                'help': ['help', 'what can you do', 'assistance'],
                'stop': ['stop', 'cancel', 'quit', 'pause']
            },
            'es-ES': {
                'search': ['buscar', 'encontrar', 'busca', 'muéstrame'],
                'navigate': ['ir a', 'abrir', 'navegar a', 'llévame a'],
                'document': ['subir documento', 'abrir archivo', 'eliminar documento', 'resumir'],
                'help': ['ayuda', 'qué puedes hacer', 'asistencia'],
                'stop': ['parar', 'cancelar', 'salir', 'pausar']
            },
            'fr-FR': {
                'search': ['chercher', 'trouver', 'rechercher', 'montrez-moi'],
                'navigate': ['aller à', 'ouvrir', 'naviguer vers', 'emmenez-moi à'],
                'document': ['télécharger document', 'ouvrir fichier', 'supprimer document', 'résumer'],
                'help': ['aide', 'que pouvez-vous faire', 'assistance'],
                'stop': ['arrêter', 'annuler', 'quitter', 'pause']
            }
        }
        
        language_patterns = patterns.get(language, patterns['en-US'])
        
        return {
            'language': language,
            'patterns': language_patterns
        }
        
    except Exception as e:
        logger.error(f"Error getting language patterns: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get language patterns")

# Initialize voice command router
try:
    from ..services.voice_command_router import VoiceCommandRouter
    voice_router = VoiceCommandRouter()
except ImportError:
    logger.warning("Voice command router not available")
    voice_router = None

@router.post('/execute-command')
async def execute_voice_command(request: CommandProcessRequest):
    """
    Execute voice command with full NLP processing and routing
    """
    if not voice_router:
        raise HTTPException(status_code=503, detail="Voice command router not available")
    
    try:
        result = await voice_router.process_voice_command(
            text=request.text,
            session_id=request.session_id or "default",
            user_id=None  # Could be extracted from authentication
        )
        
        return {
            'success': result.success,
            'message': result.message,
            'data': result.data,
            'error': result.error,
            'execution_time': result.execution_time,
            'follow_up_actions': result.follow_up_actions,
            'context_updates': result.context_updates
        }
        
    except Exception as e:
        logger.error(f"Voice command execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Command execution failed: {str(e)}")

@router.get('/execution-status/{execution_id}')
async def get_execution_status(execution_id: str):
    """
    Get status of a command execution
    """
    if not voice_router:
        raise HTTPException(status_code=503, detail="Voice command router not available")
    
    try:
        execution = voice_router.get_execution_status(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            'execution_id': execution.execution_id,
            'status': execution.status.value,
            'priority': execution.priority.value,
            'created_at': execution.created_at.isoformat(),
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'result': execution.result,
            'error': execution.error,
            'retry_count': execution.retry_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get execution status")

@router.post('/cancel-execution/{execution_id}')
async def cancel_execution(execution_id: str):
    """
    Cancel a command execution
    """
    if not voice_router:
        raise HTTPException(status_code=503, detail="Voice command router not available")
    
    try:
        success = await voice_router.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found or cannot be cancelled")
        
        return {'success': True, 'message': f'Execution {execution_id} cancelled'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel execution")

@router.get('/conversation-state/{session_id}')
async def get_conversation_state(session_id: str):
    """
    Get detailed conversation state for a session
    """
    if not voice_router:
        raise HTTPException(status_code=503, detail="Voice command router not available")
    
    try:
        state = voice_router.get_conversation_state(session_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Conversation state not found")
        
        return {
            'session_id': state.session_id,
            'user_id': state.user_id,
            'current_intent': state.current_intent,
            'pending_clarifications': state.pending_clarifications,
            'context_variables': state.context_variables,
            'conversation_flow': state.conversation_flow,
            'last_activity': state.last_activity.isoformat(),
            'is_active': state.is_active,
            'turn_count': state.turn_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get conversation state")

@router.get('/active-executions')
async def get_active_executions():
    """
    Get all active command executions
    """
    if not voice_router:
        raise HTTPException(status_code=503, detail="Voice command router not available")
    
    try:
        executions = voice_router.get_active_executions()
        
        return {
            'executions': [
                {
                    'execution_id': exec.execution_id,
                    'command_text': exec.command.text,
                    'intent': exec.command.intent.name,
                    'status': exec.status.value,
                    'priority': exec.priority.value,
                    'created_at': exec.created_at.isoformat(),
                    'started_at': exec.started_at.isoformat() if exec.started_at else None
                }
                for exec in executions.values()
            ],
            'total_count': len(executions)
        }
        
    except Exception as e:
        logger.error(f"Error getting active executions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get active executions")

@router.get('/router-analytics')
async def get_router_analytics():
    """
    Get analytics for the voice command router
    """
    if not voice_router:
        raise HTTPException(status_code=503, detail="Voice command router not available")
    
    try:
        # Get analytics for all active sessions
        analytics = {}
        
        # This would typically aggregate data from all sessions
        # For now, return router health information
        health_info = voice_router.health_check()
        
        return {
            'router_health': health_info,
            'session_analytics': analytics,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting router analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get router analytics")

@router.get('/health')
async def health_check():
    """
    Health check for voice processing service
    """
    try:
        voice_status = voice_service.health_check()
        nlp_status = voice_nlp_service.health_check()
        router_status = voice_router.health_check() if voice_router else {'status': 'unavailable'}
        
        return {
            'voice_processing': voice_status,
            'nlp_processing': nlp_status,
            'command_router': router_status,
            'multilingual_support': True,
            'supported_languages_count': 20,  # Update based on actual count
            'overall_status': 'healthy' if (
                voice_status.get('status') == 'healthy' and 
                nlp_status.get('status') in ['healthy', 'limited'] and
                router_status.get('status') == 'healthy'
            ) else 'unhealthy'
        }
        
    except Exception as e:
        logger.error(f"Voice service health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            'status': 'unhealthy',
            'error': str(e)
        })