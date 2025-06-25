#!/usr/bin/env python3
"""
Hierarchical RAG System
Implements intelligent document chunking and multi-level retrieval
"""

import spacy
from typing import List, Dict, Tuple
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

class HierarchicalRAG:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
    def intelligent_chunking(self, document: str, chunk_strategy: str = "semantic") -> List[Dict]:
        """
        Intelligent document chunking based on semantic boundaries
        """
        if chunk_strategy == "semantic":
            return self._semantic_chunking(document)
        elif chunk_strategy == "hierarchical":
            return self._hierarchical_chunking(document)
        elif chunk_strategy == "topic_based":
            return self._topic_based_chunking(document)
        else:
            return self._sliding_window_chunking(document)
    
    def _semantic_chunking(self, document: str) -> List[Dict]:
        """Chunk based on semantic boundaries (sentences, paragraphs)"""
        doc = self.nlp(document)
        
        chunks = []
        current_chunk = []
        current_size = 0
        max_chunk_size = 500  # tokens
        
        for sent in doc.sents:
            sent_tokens = len(sent)
            
            # If adding this sentence would exceed max size, finalize current chunk
            if current_size + sent_tokens > max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'type': 'semantic',
                    'token_count': current_size,
                    'sentences': len(current_chunk),
                    'entities': self._extract_entities(chunk_text),
                    'keywords': self._extract_keywords(chunk_text)
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sent.text.strip())
            current_size += sent_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'type': 'semantic',
                'token_count': current_size,
                'sentences': len(current_chunk),
                'entities': self._extract_entities(chunk_text),
                'keywords': self._extract_keywords(chunk_text)
            })
        
        return chunks
    
    def _hierarchical_chunking(self, document: str) -> List[Dict]:
        """Create hierarchical chunks (document -> sections -> paragraphs -> sentences)"""
        # Split by sections (assuming markdown-style headers)
        sections = self._split_by_headers(document)
        
        hierarchical_chunks = []
        
        for section_idx, section in enumerate(sections):
            # Section-level chunk
            section_chunk = {
                'text': section['content'],
                'type': 'section',
                'level': 1,
                'section_id': section_idx,
                'title': section.get('title', f'Section {section_idx}'),
                'entities': self._extract_entities(section['content']),
                'keywords': self._extract_keywords(section['content'])
            }
            hierarchical_chunks.append(section_chunk)
            
            # Paragraph-level chunks
            paragraphs = section['content'].split('\n\n')
            for para_idx, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) > 50:  # Skip very short paragraphs
                    para_chunk = {
                        'text': paragraph,
                        'type': 'paragraph',
                        'level': 2,
                        'section_id': section_idx,
                        'paragraph_id': para_idx,
                        'parent_title': section.get('title', f'Section {section_idx}'),
                        'entities': self._extract_entities(paragraph),
                        'keywords': self._extract_keywords(paragraph)
                    }
                    hierarchical_chunks.append(para_chunk)
        
        return hierarchical_chunks
    
    def _topic_based_chunking(self, document: str) -> List[Dict]:
        """Chunk based on topic modeling"""
        # Split into sentences
        doc = self.nlp(document)
        sentences = [sent.text for sent in doc.sents]
        
        if len(sentences) < 10:
            return self._semantic_chunking(document)
        
        # Vectorize sentences
        sentence_vectors = self.vectorizer.fit_transform(sentences)
        
        # Cluster sentences by topic
        n_clusters = min(max(2, len(sentences) // 10), 10)  # Dynamic cluster count
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(sentence_vectors)
        
        # Group sentences by cluster
        topic_chunks = []
        for cluster_id in range(n_clusters):
            cluster_sentences = [sentences[i] for i, c in enumerate(clusters) if c == cluster_id]
            
            if cluster_sentences:
                chunk_text = " ".join(cluster_sentences)
                topic_chunks.append({
                    'text': chunk_text,
                    'type': 'topic_based',
                    'topic_id': cluster_id,
                    'sentence_count': len(cluster_sentences),
                    'entities': self._extract_entities(chunk_text),
                    'keywords': self._extract_keywords(chunk_text),
                    'topic_keywords': self._get_cluster_keywords(cluster_id, kmeans, self.vectorizer)
                })
        
        return topic_chunks
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities from text"""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_)
            })
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using TF-IDF"""
        try:
            tfidf = TfidfVectorizer(max_features=10, stop_words='english')
            tfidf_matrix = tfidf.fit_transform([text])
            feature_names = tfidf.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [kw[0] for kw in keyword_scores[:5]]
        except:
            return []
    
    def _split_by_headers(self, document: str) -> List[Dict]:
        """Split document by markdown-style headers"""
        lines = document.split('\n')
        sections = []
        current_section = {'title': '', 'content': ''}
        
        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': line.strip('#').strip(),
                    'content': ''
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def create_knowledge_graph(self, chunks: List[Dict]) -> nx.Graph:
        """Create a knowledge graph from document chunks"""
        G = nx.Graph()
        
        # Add nodes for each chunk
        for i, chunk in enumerate(chunks):
            G.add_node(i, 
                      text=chunk['text'][:100] + '...',
                      type=chunk['type'],
                      entities=chunk.get('entities', []),
                      keywords=chunk.get('keywords', []))
        
        # Add edges based on entity overlap
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                similarity = self._calculate_chunk_similarity(chunks[i], chunks[j])
                if similarity > 0.3:  # Threshold for connection
                    G.add_edge(i, j, weight=similarity)
        
        return G
    
    def _calculate_chunk_similarity(self, chunk1: Dict, chunk2: Dict) -> float:
        """Calculate similarity between two chunks"""
        # Entity overlap
        entities1 = set([e['text'].lower() for e in chunk1.get('entities', [])])
        entities2 = set([e['text'].lower() for e in chunk2.get('entities', [])])
        entity_overlap = len(entities1.intersection(entities2)) / max(len(entities1.union(entities2)), 1)
        
        # Keyword overlap
        keywords1 = set(chunk1.get('keywords', []))
        keywords2 = set(chunk2.get('keywords', []))
        keyword_overlap = len(keywords1.intersection(keywords2)) / max(len(keywords1.union(keywords2)), 1)
        
        return (entity_overlap + keyword_overlap) / 2

class MultiLevelRetrieval:
    """Multi-level retrieval system for hierarchical RAG"""
    
    def __init__(self, hierarchical_rag: HierarchicalRAG):
        self.rag = hierarchical_rag
        self.knowledge_graph = None
        
    def retrieve_with_context(self, query: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
        """Retrieve chunks with hierarchical context"""
        # Level 1: Direct similarity search
        direct_matches = self._similarity_search(query, chunks, top_k)
        
        # Level 2: Expand with related chunks using knowledge graph
        if self.knowledge_graph:
            expanded_matches = self._expand_with_graph(direct_matches, chunks)
        else:
            expanded_matches = direct_matches
        
        # Level 3: Add hierarchical context (parent/child chunks)
        contextualized_matches = self._add_hierarchical_context(expanded_matches, chunks)
        
        return contextualized_matches[:top_k]
    
    def _similarity_search(self, query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
        """Basic similarity search"""
        # This would use your existing embedding-based search
        # For now, simple keyword matching
        query_words = set(query.lower().split())
        
        scored_chunks = []
        for chunk in chunks:
            chunk_words = set(chunk['text'].lower().split())
            score = len(query_words.intersection(chunk_words)) / len(query_words.union(chunk_words))
            scored_chunks.append((chunk, score))
        
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored_chunks[:top_k]]
    
    def _expand_with_graph(self, initial_chunks: List[Dict], all_chunks: List[Dict]) -> List[Dict]:
        """Expand results using knowledge graph connections"""
        if not self.knowledge_graph:
            return initial_chunks
        
        expanded = list(initial_chunks)
        
        # Find connected chunks in the knowledge graph
        for chunk in initial_chunks:
            chunk_idx = all_chunks.index(chunk)
            if chunk_idx in self.knowledge_graph:
                neighbors = list(self.knowledge_graph.neighbors(chunk_idx))
                for neighbor_idx in neighbors[:2]:  # Add top 2 neighbors
                    neighbor_chunk = all_chunks[neighbor_idx]
                    if neighbor_chunk not in expanded:
                        expanded.append(neighbor_chunk)
        
        return expanded

# Usage example
def implement_hierarchical_rag():
    """Example implementation of hierarchical RAG"""
    hierarchical_rag = HierarchicalRAG()
    retrieval_system = MultiLevelRetrieval(hierarchical_rag)
    
    # Process document with intelligent chunking
    document = """
    # Introduction to Machine Learning
    Machine learning is a subset of artificial intelligence...
    
    ## Supervised Learning
    Supervised learning uses labeled data...
    
    ## Unsupervised Learning
    Unsupervised learning finds patterns in unlabeled data...
    """
    
    # Create hierarchical chunks
    chunks = hierarchical_rag.intelligent_chunking(document, "hierarchical")
    
    # Create knowledge graph
    knowledge_graph = hierarchical_rag.create_knowledge_graph(chunks)
    retrieval_system.knowledge_graph = knowledge_graph
    
    # Retrieve with context
    query = "What is supervised learning?"
    results = retrieval_system.retrieve_with_context(query, chunks)
    
    return {
        'chunks': chunks,
        'knowledge_graph': knowledge_graph,
        'retrieval_results': results
    }