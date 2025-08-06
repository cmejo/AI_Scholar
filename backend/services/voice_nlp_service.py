"""
Voice Natural Language Processing Service
Advanced NLP for voice command interpretation and entity extraction
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
from dataclasses import dataclass, asdict

# NLP libraries
try:
    import spacy
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.chunk import ne_chunk
    from nltk.tag import pos_tag
    NLP_LIBS_AVAILABLE = True
except ImportError:
    NLP_LIBS_AVAILABLE = False
    logging.warning("NLP libraries not available. Install spacy, nltk for advanced processing")

logger = logging.getLogger(__name__)

@dataclass
class Intent:
    name: str
    confidence: float
    parameters: Dict[str, Any]

@dataclass
class Entity:
    type: str
    value: str
    confidence: float
    start: int
    end: int

@dataclass
class VoiceCommand:
    id: str
    text: str
    intent: Intent
    entities: List[Entity]
    confidence: float
    timestamp: int
    language: str = "en"

@dataclass
class ConversationContext:
    session_id: str
    history: List[VoiceCommand]
    current_topic: Optional[str] = None
    user_preferences: Dict[str, Any] = None
    last_command: Optional[VoiceCommand] = None

class VoiceNLPService:
    """Advanced NLP service for voice command processing"""
    
    def __init__(self):
        self.nlp_model = None
        self.lemmatizer = None
        self.stop_words = set()
        self.intent_patterns = {}
        self.entity_patterns = {}
        self.conversation_contexts = {}
        
        if NLP_LIBS_AVAILABLE:
            self._initialize_nlp_models()
            self._initialize_patterns()
    
    def _initialize_nlp_models(self):
        """Initialize NLP models and resources"""
        try:
            # Initialize spaCy model
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp_model = None
            
            # Initialize NLTK resources
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
                
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
                
            except Exception as e:
                logger.warning(f"Failed to initialize NLTK resources: {e}")
                
        except Exception as e:
            logger.error(f"Failed to initialize NLP models: {e}")
    
    def _initialize_patterns(self):
        """Initialize intent and entity patterns"""
        
        # Intent patterns with confidence weights
        self.intent_patterns = {
            'search': {
                'patterns': [
                    (r'\b(search|find|look\s+for|show\s+me)\s+(.+)', 0.9),
                    (r'\b(what|tell\s+me\s+about|explain)\s+(.+)', 0.8),
                    (r'\b(where\s+is|locate)\s+(.+)', 0.85),
                    (r'\b(can\s+you\s+find|help\s+me\s+find)\s+(.+)', 0.8)
                ],
                'keywords': ['search', 'find', 'look', 'show', 'what', 'where', 'locate', 'explain']
            },
            'navigate': {
                'patterns': [
                    (r'\b(go\s+to|open|navigate\s+to)\s+(.+)', 0.9),
                    (r'\b(take\s+me\s+to|show\s+me\s+the)\s+(.+)', 0.85),
                    (r'\b(switch\s+to|change\s+to)\s+(.+)', 0.8)
                ],
                'keywords': ['go', 'open', 'navigate', 'take', 'show', 'switch', 'change', 'page', 'section']
            },
            'document': {
                'patterns': [
                    (r'\b(upload|add|import)\s+(document|file|paper)\s*(.+)?', 0.9),
                    (r'\b(delete|remove)\s+(document|file)\s+(.+)', 0.9),
                    (r'\b(open|view|read)\s+(document|file)\s+(.+)', 0.85),
                    (r'\b(summarize|summary\s+of)\s+(.+)', 0.8)
                ],
                'keywords': ['document', 'file', 'paper', 'upload', 'add', 'import', 'delete', 'remove', 'open', 'view', 'read', 'summarize']
            },
            'chat': {
                'patterns': [
                    (r'\b(ask|question|query)\s+(.+)', 0.85),
                    (r'\b(explain|describe|tell\s+me)\s+(.+)', 0.8),
                    (r'\b(compare|contrast)\s+(.+)\s+(with|and)\s+(.+)', 0.9),
                    (r'\b(how\s+does|why\s+does|what\s+happens)\s+(.+)', 0.85)
                ],
                'keywords': ['ask', 'question', 'query', 'explain', 'describe', 'tell', 'compare', 'contrast', 'how', 'why', 'what']
            },
            'system': {
                'patterns': [
                    (r'\b(help|assistance|what\s+can\s+you\s+do)', 0.95),
                    (r'\b(settings|preferences|configuration)', 0.9),
                    (r'\b(stop|pause|cancel|quit)', 0.95),
                    (r'\b(repeat|say\s+again|what\s+did\s+you\s+say)', 0.9)
                ],
                'keywords': ['help', 'assistance', 'settings', 'preferences', 'stop', 'pause', 'cancel', 'quit', 'repeat']
            },
            'voice_control': {
                'patterns': [
                    (r'\b(speak|read|say)\s+(.+)', 0.9),
                    (r'\b(louder|quieter|faster|slower)', 0.95),
                    (r'\b(change\s+voice|switch\s+voice)\s*(.+)?', 0.9),
                    (r'\b(mute|unmute|silence)', 0.95)
                ],
                'keywords': ['speak', 'read', 'say', 'louder', 'quieter', 'faster', 'slower', 'voice', 'mute', 'unmute', 'silence']
            }
        }
        
        # Entity patterns
        self.entity_patterns = {
            'document_name': [
                (r'(?:document|file|paper)\s+(?:called|named|titled)\s+"([^"]+)"', 0.95),
                (r'(?:document|file|paper)\s+"([^"]+)"', 0.9),
                (r'"([^"]+)"(?:\s+(?:document|file|paper))?', 0.85),
                (r'(?:document|file|paper)\s+([a-zA-Z0-9_\-\s]+?)(?:\s+(?:in|from|with)|$)', 0.7)
            ],
            'topic': [
                (r'(?:about|regarding|concerning)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with)|$)', 0.8),
                (r'(?:search|find|look\s+for)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with)|$)', 0.75),
                (r'(?:what\s+is|tell\s+me\s+about)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with)|$)', 0.8)
            ],
            'page_section': [
                (r'(?:go\s+to|open|show)\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\s+(?:page|section|tab))', 0.9),
                (r'(?:page|section|tab)\s+([a-zA-Z\s]+)', 0.85),
                (r'(?:navigate\s+to|take\s+me\s+to)\s+([a-zA-Z\s]+)', 0.8)
            ],
            'action': [
                (r'\b(upload|download|delete|remove|open|close|save|edit|create|update)\b', 0.9),
                (r'\b(search|find|look|show|display|view|read)\b', 0.85),
                (r'\b(compare|analyze|summarize|explain|describe)\b', 0.8)
            ],
            'number': [
                (r'\b(\d+(?:\.\d+)?)\b', 0.95)
            ],
            'date_time': [
                (r'\b(today|tomorrow|yesterday|now|later)\b', 0.9),
                (r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b', 0.95),
                (r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?)\b', 0.9)
            ]
        }
    
    async def process_command(self, text: str, session_id: str = "default", language: str = "en") -> VoiceCommand:
        """
        Process voice command text and extract intent and entities
        
        Args:
            text: Voice command text
            session_id: Conversation session ID
            language: Language code
            
        Returns:
            Processed voice command
        """
        command_id = f"cmd_{int(datetime.now().timestamp() * 1000)}_{hash(text) % 10000}"
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Extract intent
        intent = await self._extract_intent(cleaned_text)
        
        # Extract entities
        entities = await self._extract_entities(cleaned_text)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(intent, entities, cleaned_text)
        
        # Create command object
        command = VoiceCommand(
            id=command_id,
            text=text,
            intent=intent,
            entities=entities,
            confidence=confidence,
            timestamp=int(datetime.now().timestamp() * 1000),
            language=language
        )
        
        # Update conversation context
        self._update_conversation_context(session_id, command)
        
        return command
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better NLP processing"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle contractions
        contractions = {
            "can't": "cannot",
            "won't": "will not",
            "n't": " not",
            "'re": " are",
            "'ve": " have",
            "'ll": " will",
            "'d": " would",
            "'m": " am"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    async def _extract_intent(self, text: str) -> Intent:
        """Extract intent from text using pattern matching and NLP"""
        best_intent = "unknown"
        best_confidence = 0.0
        parameters = {}
        
        # Enhanced pattern-based intent detection (works without NLP libraries)
        text_lower = text.lower()
        
        # Direct keyword matching for better fallback performance
        intent_keywords = {
            'search': ['search', 'find', 'look', 'show', 'what', 'tell', 'about', 'papers', 'documents'],
            'navigate': ['go', 'open', 'navigate', 'take', 'page', 'section', 'tab', 'settings'],
            'document': ['document', 'file', 'paper', 'upload', 'add', 'import', 'delete', 'remove', 'view', 'read', 'summarize'],
            'chat': ['ask', 'question', 'query', 'explain', 'describe', 'compare', 'contrast', 'mean', 'how', 'why'],
            'system': ['help', 'assistance', 'can you do', 'settings', 'preferences', 'stop', 'pause', 'cancel', 'quit', 'repeat'],
            'voice_control': ['speak', 'read', 'say', 'louder', 'quieter', 'faster', 'slower', 'voice', 'mute', 'unmute']
        }
        
        # Score each intent based on keyword matches
        for intent_name, keywords in intent_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Calculate confidence based on keyword density and specificity
                confidence = min(0.9, score / len(text_lower.split()) * 3)
                
                # Boost confidence for exact phrase matches
                if intent_name == 'search' and any(phrase in text_lower for phrase in ['search for', 'find', 'what is', 'tell me about']):
                    confidence += 0.2
                elif intent_name == 'navigate' and any(phrase in text_lower for phrase in ['go to', 'open', 'navigate to', 'take me to']):
                    confidence += 0.2
                elif intent_name == 'document' and any(phrase in text_lower for phrase in ['upload', 'delete', 'open document', 'summarize']):
                    confidence += 0.2
                elif intent_name == 'chat' and any(phrase in text_lower for phrase in ['explain', 'tell me', 'what does', 'how does']):
                    confidence += 0.2
                elif intent_name == 'system' and any(phrase in text_lower for phrase in ['help', 'what can you do', 'stop']):
                    confidence += 0.3
                elif intent_name == 'voice_control' and any(phrase in text_lower for phrase in ['speak', 'louder', 'mute']):
                    confidence += 0.2
                
                confidence = min(1.0, confidence)
                
                if confidence > best_confidence:
                    best_intent = intent_name
                    best_confidence = confidence
                    parameters['matched_keywords'] = matched_keywords
                    parameters['keyword_score'] = score
        
        # Pattern-based intent detection (original logic)
        if NLP_LIBS_AVAILABLE and hasattr(self, 'intent_patterns'):
            for intent_name, intent_data in self.intent_patterns.items():
                patterns = intent_data['patterns']
                keywords = intent_data['keywords']
                
                # Check patterns
                for pattern, base_confidence in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        confidence = base_confidence
                        
                        # Boost confidence based on keyword density
                        words = text.split()
                        keyword_matches = sum(1 for word in words if word in keywords)
                        keyword_boost = min(0.1, keyword_matches / len(words))
                        confidence += keyword_boost
                        
                        if confidence > best_confidence:
                            best_intent = intent_name
                            best_confidence = confidence
                            parameters['pattern_match'] = match.groups()
                            break
        
        # Use spaCy for advanced intent classification if available
        if self.nlp_model and best_confidence < 0.7:
            spacy_intent, spacy_confidence = self._classify_intent_with_spacy(text)
            if spacy_confidence > best_confidence:
                best_intent = spacy_intent
                best_confidence = spacy_confidence
                parameters['spacy_classification'] = True
        
        return Intent(
            name=best_intent,
            confidence=min(1.0, best_confidence),
            parameters=parameters
        )
    
    def _classify_intent_with_spacy(self, text: str) -> Tuple[str, float]:
        """Use spaCy for intent classification"""
        if not self.nlp_model:
            return "unknown", 0.0
        
        try:
            doc = self.nlp_model(text)
            
            # Analyze POS tags and dependencies for intent clues
            verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
            nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN"]
            
            # Intent classification based on linguistic patterns
            if any(verb in ["search", "find", "look", "show"] for verb in verbs):
                return "search", 0.7
            elif any(verb in ["go", "open", "navigate", "take"] for verb in verbs):
                return "navigate", 0.7
            elif any(noun in ["document", "file", "paper"] for noun in nouns):
                return "document", 0.6
            elif any(verb in ["ask", "explain", "tell", "describe"] for verb in verbs):
                return "chat", 0.6
            elif any(verb in ["help", "stop", "quit", "cancel"] for verb in verbs):
                return "system", 0.7
            elif any(verb in ["speak", "read", "say"] for verb in verbs):
                return "voice_control", 0.7
            
            return "unknown", 0.0
            
        except Exception as e:
            logger.warning(f"spaCy intent classification failed: {e}")
            return "unknown", 0.0
    
    async def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        # Enhanced pattern-based entity extraction (works without NLP libraries)
        entity_patterns_simple = {
            'document_name': [
                (r'"([^"]+)"', 0.95),  # Quoted text
                (r'document\s+(?:called\s+|named\s+)?([a-zA-Z0-9_\-\s]+?)(?:\s|$)', 0.7),
                (r'file\s+(?:called\s+|named\s+)?([a-zA-Z0-9_\-\s]+?)(?:\s|$)', 0.7)
            ],
            'topic': [
                (r'(?:about|regarding|concerning)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with|papers|documents)|$)', 0.8),
                (r'(?:search|find|look\s+for)\s+(?:papers\s+about\s+|documents\s+about\s+)?([a-zA-Z\s]+?)(?:\s+(?:in|from|with|papers|documents)|$)', 0.75),
                (r'(?:what\s+is|tell\s+me\s+about)\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|with)|$)', 0.8)
            ],
            'page_section': [
                (r'(?:go\s+to|open|show|navigate\s+to)\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\s+(?:page|section|tab)|$)', 0.9),
                (r'(?:page|section|tab)\s+([a-zA-Z\s]+)', 0.85)
            ],
            'action': [
                (r'\b(upload|download|delete|remove|open|close|save|edit|create|update|summarize|explain|search|find)\b', 0.9)
            ],
            'number': [
                (r'\b(\d+(?:\.\d+)?)\b', 0.95)
            ],
            'date_time': [
                (r'\b(today|tomorrow|yesterday|now|later)\b', 0.9),
                (r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b', 0.95),
                (r'\b(\d{1,2}:\d{2}(?:\s*[ap]m)?)\b', 0.9)
            ]
        }
        
        # Extract entities using simple patterns
        for entity_type, patterns in entity_patterns_simple.items():
            for pattern, confidence in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_value = match.group(1) if match.groups() else match.group(0)
                    entity_value = entity_value.strip()
                    
                    if entity_value:  # Only add non-empty entities
                        entity = Entity(
                            type=entity_type,
                            value=entity_value,
                            confidence=confidence,
                            start=match.start(),
                            end=match.end()
                        )
                        entities.append(entity)
        
        # Original pattern-based entity extraction (if available)
        if hasattr(self, 'entity_patterns'):
            for entity_type, patterns in self.entity_patterns.items():
                for pattern, confidence in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity = Entity(
                            type=entity_type,
                            value=match.group(1) if match.groups() else match.group(0),
                            confidence=confidence,
                            start=match.start(),
                            end=match.end()
                        )
                        entities.append(entity)
        
        # Use spaCy for named entity recognition
        if self.nlp_model:
            spacy_entities = self._extract_entities_with_spacy(text)
            entities.extend(spacy_entities)
        
        # Use NLTK for additional entity extraction
        if NLP_LIBS_AVAILABLE:
            nltk_entities = self._extract_entities_with_nltk(text)
            entities.extend(nltk_entities)
        
        # Resolve overlapping entities
        entities = self._resolve_entity_overlaps(entities)
        
        return entities
    
    def _extract_entities_with_spacy(self, text: str) -> List[Entity]:
        """Extract entities using spaCy NER"""
        entities = []
        
        try:
            doc = self.nlp_model(text)
            
            for ent in doc.ents:
                entity_type = self._map_spacy_entity_type(ent.label_)
                if entity_type:
                    entity = Entity(
                        type=entity_type,
                        value=ent.text,
                        confidence=0.8,  # spaCy doesn't provide confidence scores
                        start=ent.start_char,
                        end=ent.end_char
                    )
                    entities.append(entity)
                    
        except Exception as e:
            logger.warning(f"spaCy entity extraction failed: {e}")
        
        return entities
    
    def _extract_entities_with_nltk(self, text: str) -> List[Entity]:
        """Extract entities using NLTK"""
        entities = []
        
        try:
            # Tokenize and tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Named entity chunking
            chunks = ne_chunk(pos_tags)
            
            current_pos = 0
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    # This is a named entity
                    entity_text = ' '.join([token for token, pos in chunk])
                    entity_type = self._map_nltk_entity_type(chunk.label())
                    
                    if entity_type:
                        # Find position in original text
                        start_pos = text.lower().find(entity_text.lower(), current_pos)
                        if start_pos != -1:
                            entity = Entity(
                                type=entity_type,
                                value=entity_text,
                                confidence=0.7,
                                start=start_pos,
                                end=start_pos + len(entity_text)
                            )
                            entities.append(entity)
                            current_pos = start_pos + len(entity_text)
                else:
                    # Regular token
                    token, pos = chunk
                    current_pos = text.lower().find(token.lower(), current_pos) + len(token)
                    
        except Exception as e:
            logger.warning(f"NLTK entity extraction failed: {e}")
        
        return entities
    
    def _map_spacy_entity_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our entity types"""
        mapping = {
            'PERSON': 'person',
            'ORG': 'organization',
            'GPE': 'location',
            'DATE': 'date_time',
            'TIME': 'date_time',
            'MONEY': 'number',
            'QUANTITY': 'number',
            'CARDINAL': 'number',
            'ORDINAL': 'number'
        }
        return mapping.get(spacy_label)
    
    def _map_nltk_entity_type(self, nltk_label: str) -> Optional[str]:
        """Map NLTK entity labels to our entity types"""
        mapping = {
            'PERSON': 'person',
            'ORGANIZATION': 'organization',
            'GPE': 'location',
            'LOCATION': 'location',
            'DATE': 'date_time',
            'TIME': 'date_time',
            'MONEY': 'number',
            'PERCENT': 'number'
        }
        return mapping.get(nltk_label)
    
    def _resolve_entity_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Resolve overlapping entities by keeping highest confidence ones"""
        if not entities:
            return entities
        
        # Sort by confidence (descending)
        sorted_entities = sorted(entities, key=lambda e: e.confidence, reverse=True)
        resolved_entities = []
        
        for entity in sorted_entities:
            # Check for overlaps with already resolved entities
            has_overlap = False
            for resolved in resolved_entities:
                if (entity.start < resolved.end and entity.end > resolved.start):
                    has_overlap = True
                    break
            
            if not has_overlap:
                resolved_entities.append(entity)
        
        # Sort by position
        return sorted(resolved_entities, key=lambda e: e.start)
    
    def _calculate_confidence(self, intent: Intent, entities: List[Entity], text: str) -> float:
        """Calculate overall confidence score"""
        intent_weight = 0.6
        entity_weight = 0.3
        text_quality_weight = 0.1
        
        # Intent confidence
        intent_confidence = intent.confidence
        
        # Entity confidence (average of all entities)
        entity_confidence = 0.5  # Default neutral confidence
        if entities:
            entity_confidence = sum(e.confidence for e in entities) / len(entities)
        
        # Text quality score (based on length, completeness, etc.)
        text_quality = min(1.0, len(text.split()) / 10)  # Normalize by expected command length
        
        overall_confidence = (
            intent_confidence * intent_weight +
            entity_confidence * entity_weight +
            text_quality * text_quality_weight
        )
        
        return min(1.0, overall_confidence)
    
    def _update_conversation_context(self, session_id: str, command: VoiceCommand):
        """Update conversation context with new command"""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext(
                session_id=session_id,
                history=[],
                user_preferences={}
            )
        
        context = self.conversation_contexts[session_id]
        context.history.append(command)
        context.last_command = command
        
        # Keep only last 20 commands
        if len(context.history) > 20:
            context.history = context.history[-20:]
        
        # Update current topic if relevant
        topic_entities = [e for e in command.entities if e.type == 'topic']
        if topic_entities:
            context.current_topic = topic_entities[0].value
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for session"""
        return self.conversation_contexts.get(session_id)
    
    def clear_conversation_context(self, session_id: str):
        """Clear conversation context for session"""
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
    
    def get_command_suggestions(self, partial_text: str, limit: int = 5) -> List[str]:
        """Get command suggestions based on partial text"""
        suggestions = []
        
        # Simple pattern-based suggestions
        text_lower = partial_text.lower()
        
        if text_lower.startswith(('search', 'find', 'look')):
            suggestions.extend([
                'search for machine learning',
                'find documents about AI',
                'look for research papers'
            ])
        elif text_lower.startswith(('go', 'open', 'navigate')):
            suggestions.extend([
                'go to documents page',
                'open settings',
                'navigate to chat'
            ])
        elif text_lower.startswith(('upload', 'add', 'import')):
            suggestions.extend([
                'upload a document',
                'add new file',
                'import research paper'
            ])
        else:
            # General suggestions
            suggestions.extend([
                'search for documents',
                'go to settings',
                'upload a file',
                'help me',
                'what can you do'
            ])
        
        return suggestions[:limit]
    
    def analyze_command_patterns(self, session_id: str) -> Dict[str, Any]:
        """Analyze command patterns for a session"""
        context = self.conversation_contexts.get(session_id)
        if not context or not context.history:
            return {}
        
        commands = context.history
        
        # Intent distribution
        intent_counts = {}
        for cmd in commands:
            intent_name = cmd.intent.name
            intent_counts[intent_name] = intent_counts.get(intent_name, 0) + 1
        
        # Average confidence
        avg_confidence = sum(cmd.confidence for cmd in commands) / len(commands)
        
        # Most common entities
        entity_counts = {}
        for cmd in commands:
            for entity in cmd.entities:
                entity_type = entity.type
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        return {
            'total_commands': len(commands),
            'intent_distribution': intent_counts,
            'average_confidence': avg_confidence,
            'entity_distribution': entity_counts,
            'current_topic': context.current_topic,
            'session_duration': commands[-1].timestamp - commands[0].timestamp if len(commands) > 1 else 0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for NLP service"""
        return {
            'status': 'healthy' if NLP_LIBS_AVAILABLE else 'limited',
            'nlp_libraries_available': NLP_LIBS_AVAILABLE,
            'spacy_model_loaded': self.nlp_model is not None,
            'nltk_resources_available': self.lemmatizer is not None,
            'active_sessions': len(self.conversation_contexts),
            'supported_intents': list(self.intent_patterns.keys()),
            'supported_entities': list(self.entity_patterns.keys())
        }