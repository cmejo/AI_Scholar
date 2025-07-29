"""
Text processing utilities for chunking and analysis
"""
import re
import spacy
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class TextProcessor:
    def __init__(self):
        # Load spaCy model for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if spaCy model not installed
            self.nlp = None
        
        self.stop_words = set(stopwords.words('english'))
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 64) -> List[Dict[str, Any]]:
        """Chunk text with semantic awareness"""
        # Split into sentences
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = ""
        current_size = 0
        sentence_start_idx = 0
        
        for i, sentence in enumerate(sentences):
            sentence_words = len(word_tokenize(sentence))
            
            # If adding this sentence would exceed chunk size
            if current_size + sentence_words > chunk_size and current_chunk:
                # Create chunk
                chunk_data = {
                    'content': current_chunk.strip(),
                    'start_sentence': sentence_start_idx,
                    'end_sentence': i - 1,
                    'word_count': current_size,
                    'metadata': self._extract_metadata(current_chunk)
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_sentences = sentences[max(0, i - overlap//20):i]  # Rough overlap
                current_chunk = " ".join(overlap_sentences) + " " + sentence
                current_size = sum(len(word_tokenize(s)) for s in overlap_sentences) + sentence_words
                sentence_start_idx = max(0, i - len(overlap_sentences))
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_words
                if not current_chunk.strip():
                    sentence_start_idx = i
        
        # Add final chunk
        if current_chunk.strip():
            chunk_data = {
                'content': current_chunk.strip(),
                'start_sentence': sentence_start_idx,
                'end_sentence': len(sentences) - 1,
                'word_count': current_size,
                'metadata': self._extract_metadata(current_chunk)
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text chunk"""
        metadata = {
            'entities': [],
            'keywords': [],
            'topics': [],
            'sentiment': 'neutral'
        }
        
        # Extract entities using spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            metadata['entities'] = [
                {'text': ent.text, 'label': ent.label_, 'start': ent.start_char, 'end': ent.end_char}
                for ent in doc.ents
            ]
        
        # Extract keywords (simple frequency-based)
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalpha() and word not in self.stop_words and len(word) > 3]
        
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top keywords
        metadata['keywords'] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Detect topics (simple keyword-based)
        topic_keywords = {
            'research': ['research', 'study', 'analysis', 'experiment', 'methodology'],
            'technology': ['technology', 'software', 'algorithm', 'system', 'computer'],
            'science': ['science', 'scientific', 'theory', 'hypothesis', 'data'],
            'business': ['business', 'market', 'company', 'strategy', 'management']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                metadata['topics'].append(topic)
        
        return metadata
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        
        # Extract noun phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) > 1]
        
        # Extract named entities
        entities = [ent.text for ent in doc.ents]
        
        return list(set(noun_phrases + entities))
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not self.nlp:
            # Fallback to simple word overlap
            words1 = set(word_tokenize(text1.lower()))
            words2 = set(word_tokenize(text2.lower()))
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        
        return doc1.similarity(doc2)