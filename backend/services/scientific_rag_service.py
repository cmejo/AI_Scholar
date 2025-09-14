"""
Scientific RAG Service for AI Scholar
Combines document retrieval with Ollama LLM generation for scientific queries
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

from .ollama_service import ollama_service
from .scientific_pdf_processor import scientific_pdf_processor
from .vector_store_service import vector_store_service

logger = logging.getLogger(__name__)

class ScientificRAGService:
    """RAG service specialized for scientific literature queries"""
    
    def __init__(self):
        self.ollama = ollama_service
        self.pdf_processor = scientific_pdf_processor
        self.vector_store = vector_store_service
        
        # Scientific query patterns
        self.query_types = {
            'methodology': ['how', 'method', 'approach', 'technique', 'procedure'],
            'findings': ['what', 'result', 'finding', 'outcome', 'conclusion'],
            'comparison': ['compare', 'versus', 'difference', 'better', 'advantage'],
            'definition': ['what is', 'define', 'definition', 'meaning'],
            'review': ['review', 'survey', 'overview', 'summary', 'state of art']
        }
    
    async def process_scientific_query(
        self, 
        query: str, 
        filters: Optional[Dict] = None,
        model: str = "llama2",
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """Process a scientific research query using RAG pipeline"""
        
        start_time = datetime.now()
        
        try:
            # Step 1: Analyze and expand the query
            query_analysis = self._analyze_scientific_query(query)
            expanded_query = await self._expand_scientific_query(query, query_analysis)
            
            # Step 2: Retrieve relevant document chunks
            search_results = await self.vector_store.semantic_search(
                expanded_query,
                n_results=max_sources * 3,  # Get more results for better filtering
                filters=filters
            )
            
            # Step 3: Filter and rank results by relevance
            filtered_results = self._filter_by_scientific_relevance(
                search_results, 
                query, 
                query_analysis
            )
            
            # Step 4: Select best context chunks
            context_chunks = self._select_optimal_context(
                filtered_results[:max_sources], 
                query_analysis
            )
            
            # Step 5: Generate response using Ollama
            llm_response = await self.ollama.generate_scientific_response(
                query,
                context_chunks,
                model=model
            )
            
            # Step 6: Post-process and enhance response
            enhanced_response = self._enhance_scientific_response(
                llm_response,
                filtered_results,
                query_analysis
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'query': query,
                'query_type': query_analysis['type'],
                'response': enhanced_response['response'],
                'sources': enhanced_response['sources'],
                'context_chunks_used': len(context_chunks),
                'total_results_found': len(search_results),
                'confidence_score': enhanced_response['confidence_score'],
                'processing_time': processing_time,
                'model_used': model,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing scientific query: {e}")
            return {
                'query': query,
                'response': f"I apologize, but I encountered an error processing your scientific query: {str(e)}",
                'error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _analyze_scientific_query(self, query: str) -> Dict[str, Any]:
        """Analyze the type and intent of a scientific query"""
        query_lower = query.lower()
        
        # Determine query type
        query_type = 'general'
        for qtype, keywords in self.query_types.items():
            if any(keyword in query_lower for keyword in keywords):
                query_type = qtype
                break
        
        # Extract scientific entities
        entities = {
            'genes': re.findall(r'\b[A-Z]{2,}[0-9]*\b', query),  # Gene names (e.g., TP53, BRCA1)
            'proteins': re.findall(r'\b[A-Z][a-z]+(?:-[A-Z][a-z]+)*\b', query),  # Protein names
            'chemicals': re.findall(r'\b[A-Z][a-z]*(?:-[a-z]+)*\b', query),  # Chemical compounds
            'organisms': re.findall(r'\b[A-Z][a-z]+\s+[a-z]+\b', query)  # Species names
        }
        
        # Identify research domains
        domains = []
        domain_keywords = {
            'molecular_biology': ['gene', 'protein', 'dna', 'rna', 'cell', 'molecular'],
            'medicine': ['patient', 'treatment', 'therapy', 'clinical', 'medical', 'disease'],
            'neuroscience': ['brain', 'neuron', 'cognitive', 'neural', 'memory'],
            'chemistry': ['chemical', 'compound', 'reaction', 'synthesis', 'molecule'],
            'physics': ['quantum', 'particle', 'energy', 'force', 'wave'],
            'computer_science': ['algorithm', 'model', 'computation', 'data', 'machine learning']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                domains.append(domain)
        
        return {
            'type': query_type,
            'entities': entities,
            'domains': domains,
            'complexity': 'high' if len(query.split()) > 10 else 'medium' if len(query.split()) > 5 else 'simple'
        }
    
    async def _expand_scientific_query(self, query: str, analysis: Dict) -> str:
        """Expand query with scientific synonyms and related terms"""
        
        # Scientific term synonyms
        scientific_synonyms = {
            'gene': ['genetic', 'genomic', 'allele', 'locus', 'sequence'],
            'protein': ['polypeptide', 'enzyme', 'peptide', 'amino acid'],
            'cell': ['cellular', 'cytoplasm', 'membrane', 'organelle'],
            'study': ['research', 'investigation', 'analysis', 'experiment'],
            'method': ['methodology', 'approach', 'technique', 'procedure'],
            'result': ['finding', 'outcome', 'conclusion', 'observation'],
            'treatment': ['therapy', 'intervention', 'medication', 'drug'],
            'disease': ['disorder', 'condition', 'syndrome', 'pathology']
        }
        
        expanded_terms = set()
        query_words = query.lower().split()
        
        for word in query_words:
            if word in scientific_synonyms:
                expanded_terms.update(scientific_synonyms[word])
        
        # Add domain-specific terms
        for domain in analysis['domains']:
            if domain == 'molecular_biology':
                expanded_terms.update(['expression', 'regulation', 'pathway', 'interaction'])
            elif domain == 'medicine':
                expanded_terms.update(['clinical', 'patient', 'diagnosis', 'prognosis'])
            elif domain == 'neuroscience':
                expanded_terms.update(['synaptic', 'cortical', 'behavioral', 'cognitive'])
        
        # Combine original query with expanded terms
        if expanded_terms:
            expansion = ' '.join(list(expanded_terms)[:10])  # Limit expansion
            return f"{query} {expansion}"
        
        return query
    
    def _filter_by_scientific_relevance(
        self, 
        search_results: List[Dict], 
        query: str, 
        analysis: Dict
    ) -> List[Dict]:
        """Filter and rank results by scientific relevance"""
        
        filtered_results = []
        
        for result in search_results:
            relevance_score = result.get('distance', 1.0)  # Lower distance = higher relevance
            
            # Boost relevance for matching domains
            content = result.get('document', '').lower()
            domain_boost = 0
            for domain in analysis['domains']:
                domain_keywords = {
                    'molecular_biology': ['gene', 'protein', 'dna', 'cell'],
                    'medicine': ['patient', 'clinical', 'treatment'],
                    'neuroscience': ['brain', 'neural', 'cognitive']
                }.get(domain, [])
                
                if any(keyword in content for keyword in domain_keywords):
                    domain_boost += 0.1
            
            # Boost relevance for matching query type
            query_type = analysis['type']
            if query_type == 'methodology' and any(word in content for word in ['method', 'approach', 'technique']):
                domain_boost += 0.15
            elif query_type == 'findings' and any(word in content for word in ['result', 'finding', 'conclusion']):
                domain_boost += 0.15
            
            # Adjust relevance score
            adjusted_score = relevance_score - domain_boost
            
            result['adjusted_relevance'] = adjusted_score
            result['domain_match'] = domain_boost > 0
            
            filtered_results.append(result)
        
        # Sort by adjusted relevance (lower is better)
        filtered_results.sort(key=lambda x: x['adjusted_relevance'])
        
        return filtered_results
    
    def _select_optimal_context(
        self, 
        results: List[Dict], 
        analysis: Dict,
        max_context_length: int = 8000
    ) -> List[str]:
        """Select optimal context chunks for LLM generation"""
        
        context_chunks = []
        current_length = 0
        
        # Prioritize different section types based on query type
        section_priority = {
            'methodology': ['methods', 'methodology', 'materials'],
            'findings': ['results', 'findings', 'conclusion'],
            'definition': ['introduction', 'background', 'abstract'],
            'review': ['abstract', 'introduction', 'conclusion'],
            'comparison': ['results', 'discussion', 'conclusion']
        }.get(analysis['type'], ['abstract', 'introduction', 'results'])
        
        # First pass: Add high-priority sections
        for result in results:
            chunk_text = result.get('document', '')
            chunk_metadata = result.get('metadata', {})
            chunk_section = chunk_metadata.get('section', 'unknown')
            
            if chunk_section in section_priority and current_length + len(chunk_text) < max_context_length:
                context_chunks.append(chunk_text)
                current_length += len(chunk_text)
        
        # Second pass: Fill remaining space with other relevant chunks
        for result in results:
            chunk_text = result.get('document', '')
            if chunk_text not in context_chunks and current_length + len(chunk_text) < max_context_length:
                context_chunks.append(chunk_text)
                current_length += len(chunk_text)
        
        return context_chunks
    
    def _enhance_scientific_response(
        self, 
        llm_response: Dict, 
        search_results: List[Dict],
        query_analysis: Dict
    ) -> Dict[str, Any]:
        """Enhance LLM response with scientific metadata and sources"""
        
        response_text = llm_response.get('response', '')
        
        # Extract source citations from response
        source_citations = re.findall(r'\[Source\s+(\d+)\]', response_text)
        
        # Build source information
        sources = []
        for i, result in enumerate(search_results[:10]):
            metadata = result.get('metadata', {})
            
            source_info = {
                'source_id': i + 1,
                'relevance_score': 1.0 - result.get('adjusted_relevance', 0.5),
                'section': metadata.get('section', 'unknown'),
                'document_id': metadata.get('document_id', 'unknown'),
                'page': metadata.get('page', 0),
                'text_preview': result.get('document', '')[:300] + "...",
                'cited_in_response': str(i + 1) in source_citations
            }
            
            sources.append(source_info)
        
        # Calculate enhanced confidence score
        confidence_factors = {
            'llm_confidence': llm_response.get('confidence_score', 0.5),
            'source_quality': sum(s['relevance_score'] for s in sources) / len(sources) if sources else 0,
            'citation_coverage': len(source_citations) / len(sources) if sources else 0,
            'domain_match': 1.0 if query_analysis['domains'] else 0.5
        }
        
        overall_confidence = sum(confidence_factors.values()) / len(confidence_factors)
        
        return {
            'response': response_text,
            'sources': sources,
            'confidence_score': overall_confidence,
            'confidence_factors': confidence_factors,
            'query_analysis': query_analysis
        }
    
    async def bulk_process_pdfs(
        self, 
        pdf_paths: List[str], 
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Process multiple PDFs and add to vector store"""
        
        results = {
            'processed': 0,
            'failed': 0,
            'total': len(pdf_paths),
            'documents': [],
            'errors': []
        }
        
        for i, pdf_path in enumerate(pdf_paths):
            try:
                # Process PDF
                document_data = self.pdf_processor.extract_comprehensive_content(pdf_path)
                
                # Create chunks for vector storage
                chunks = self._create_scientific_chunks(document_data)
                
                # Add to vector store
                await self.vector_store.add_document_chunks(
                    document_data['document_id'],
                    chunks
                )
                
                results['processed'] += 1
                results['documents'].append({
                    'document_id': document_data['document_id'],
                    'title': document_data['metadata'].get('title', 'Unknown'),
                    'chunks_created': len(chunks),
                    'processing_quality': document_data['extraction_quality']['assessment']
                })
                
                # Report progress
                if progress_callback:
                    progress = (i + 1) / len(pdf_paths) * 100
                    await progress_callback(progress, document_data['metadata'].get('title', f'Document {i+1}'))
                
            except Exception as e:
                logger.error(f"Failed to process PDF {pdf_path}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'file': pdf_path,
                    'error': str(e)
                })
        
        return results
    
    def _create_scientific_chunks(self, document_data: Dict) -> List[Dict]:
        """Create optimized chunks for scientific documents"""
        chunks = []
        
        # Create section-based chunks
        sections = document_data.get('sections', {})
        for section_name, section_text in sections.items():
            if section_text.strip():
                # For long sections, create multiple chunks
                if len(section_text) > 1500:
                    section_chunks = self._split_text_semantically(section_text, 1000, 200)
                    for i, chunk_text in enumerate(section_chunks):
                        chunks.append({
                            'text': chunk_text,
                            'section': section_name,
                            'chunk_type': 'section_part',
                            'part_number': i + 1,
                            'total_parts': len(section_chunks),
                            'document_metadata': document_data['metadata']
                        })
                else:
                    chunks.append({
                        'text': section_text,
                        'section': section_name,
                        'chunk_type': 'full_section',
                        'document_metadata': document_data['metadata']
                    })
        
        # Create abstract + introduction chunk (often most informative)
        abstract = sections.get('abstract', '')
        introduction = sections.get('introduction', '')
        if abstract and introduction:
            combined_text = f"Abstract: {abstract}\n\nIntroduction: {introduction}"
            chunks.append({
                'text': combined_text,
                'section': 'abstract_introduction',
                'chunk_type': 'combined_overview',
                'document_metadata': document_data['metadata']
            })
        
        # Create results + conclusion chunk
        results_text = sections.get('results', '')
        conclusion = sections.get('conclusion', '')
        if results_text and conclusion:
            combined_text = f"Results: {results_text}\n\nConclusion: {conclusion}"
            chunks.append({
                'text': combined_text,
                'section': 'results_conclusion',
                'chunk_type': 'combined_findings',
                'document_metadata': document_data['metadata']
            })
        
        return chunks
    
    def _split_text_semantically(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into chunks with semantic awareness"""
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk + sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def get_corpus_statistics(self) -> Dict[str, Any]:
        """Get statistics about the scientific corpus"""
        try:
            stats = await self.vector_store.get_collection_stats()
            
            return {
                'total_documents': stats.get('document_count', 0),
                'total_chunks': stats.get('chunk_count', 0),
                'total_embeddings': stats.get('embedding_count', 0),
                'average_document_length': stats.get('avg_doc_length', 0),
                'most_common_sections': stats.get('common_sections', []),
                'processing_quality_distribution': stats.get('quality_distribution', {}),
                'last_updated': stats.get('last_updated', datetime.now().isoformat())
            }
        except Exception as e:
            logger.error(f"Error getting corpus statistics: {e}")
            return {}
    
    async def search_similar_papers(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for papers similar to the query"""
        try:
            results = await self.vector_store.semantic_search(
                query,
                n_results=limit,
                include_metadata=True
            )
            
            # Group results by document
            papers = {}
            for result in results:
                doc_id = result.get('metadata', {}).get('document_id')
                if doc_id:
                    if doc_id not in papers:
                        papers[doc_id] = {
                            'document_id': doc_id,
                            'title': result.get('metadata', {}).get('title', 'Unknown'),
                            'relevance_score': 1.0 - result.get('distance', 0.5),
                            'matching_sections': [],
                            'preview_text': ''
                        }
                    
                    papers[doc_id]['matching_sections'].append({
                        'section': result.get('metadata', {}).get('section', 'unknown'),
                        'text_preview': result.get('document', '')[:200] + "..."
                    })
                    
                    if not papers[doc_id]['preview_text']:
                        papers[doc_id]['preview_text'] = result.get('document', '')[:500] + "..."
            
            return list(papers.values())
            
        except Exception as e:
            logger.error(f"Error searching similar papers: {e}")
            return []

# Global instance
scientific_rag_service = ScientificRAGService()