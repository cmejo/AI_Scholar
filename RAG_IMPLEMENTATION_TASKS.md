# AI Scholar RAG Implementation Tasks
## Detailed Task Breakdown with Code Examples

---

## 🔥 **PHASE 1: IMMEDIATE IMPLEMENTATION (Week 1)**

### **Task 1A: Ollama Docker Integration**
```yaml
# Add to docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ai-scholar-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_ORIGINS=*
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:
```

**Implementation Steps:**
1. [ ] Update docker-compose.yml with Ollama service
2. [ ] Create Ollama initialization script
3. [ ] Download scientific LLMs (llama2, mistral, codellama)
4. [ ] Test Ollama API connectivity
5. [ ] Create model management interface

### **Task 1B: Enhanced PDF Processing Service**
```python
# backend/services/pdf_processor.py
import PyMuPDF
import pdfplumber
from typing import Dict, List, Optional
import re

class ScientificPDFProcessor:
    def __init__(self):
        self.section_patterns = {
            'abstract': r'abstract|summary',
            'introduction': r'introduction|background',
            'methods': r'methods|methodology|materials',
            'results': r'results|findings',
            'discussion': r'discussion|conclusion',
            'references': r'references|bibliography'
        }
    
    def extract_structured_content(self, pdf_path: str) -> Dict:
        """Extract structured content from scientific PDF"""
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            metadata = self.extract_metadata(pdf)
            
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            sections = self.identify_sections(full_text)
            citations = self.extract_citations(full_text)
            figures_tables = self.extract_figures_tables(pdf)
            
            return {
                'metadata': metadata,
                'full_text': full_text,
                'sections': sections,
                'citations': citations,
                'figures_tables': figures_tables,
                'word_count': len(full_text.split()),
                'page_count': len(pdf.pages)
            }
```

**Implementation Steps:**
1. [ ] Create ScientificPDFProcessor class
2. [ ] Implement section identification algorithms
3. [ ] Add citation extraction functionality
4. [ ] Create figure/table extraction
5. [ ] Add metadata extraction (DOI, authors, journal)

### **Task 1C: Vector Database Setup**
```python
# backend/services/vector_store.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import uuid

class ScientificVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_scientific_db")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self.client.get_or_create_collection(
            name="scientific_papers",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_document_chunks(self, document_id: str, chunks: List[Dict]):
        """Add document chunks to vector store"""
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts).tolist()
        
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [{
            'document_id': document_id,
            'chunk_index': i,
            'section': chunk.get('section', 'unknown'),
            'page': chunk.get('page', 0),
            'word_count': len(chunk['text'].split())
        } for i, chunk in enumerate(chunks)]
        
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
    
    def semantic_search(self, query: str, n_results: int = 10) -> List[Dict]:
        """Perform semantic search across scientific corpus"""
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        
        return self.format_search_results(results)
```

**Implementation Steps:**
1. [ ] Set up ChromaDB with scientific paper collection
2. [ ] Implement document chunking strategy
3. [ ] Create embedding generation pipeline
4. [ ] Add semantic search functionality
5. [ ] Implement result ranking and filtering

---

## 🚀 **PHASE 2: RAG PIPELINE (Week 2)**

### **Task 2A: Document Chunking Strategy**
```python
# backend/services/chunking_service.py
from typing import List, Dict
import re

class ScientificChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_by_sections(self, document: Dict) -> List[Dict]:
        """Create chunks based on scientific paper sections"""
        chunks = []
        
        for section_name, content in document['sections'].items():
            if len(content) > self.chunk_size:
                # Split large sections into smaller chunks
                section_chunks = self.split_text_with_overlap(content)
                for i, chunk_text in enumerate(section_chunks):
                    chunks.append({
                        'text': chunk_text,
                        'section': section_name,
                        'chunk_type': 'section_part',
                        'metadata': {
                            'section': section_name,
                            'part': i + 1,
                            'total_parts': len(section_chunks)
                        }
                    })
            else:
                chunks.append({
                    'text': content,
                    'section': section_name,
                    'chunk_type': 'full_section',
                    'metadata': {'section': section_name}
                })
        
        return chunks
    
    def create_contextual_chunks(self, document: Dict) -> List[Dict]:
        """Create chunks with surrounding context"""
        chunks = []
        sentences = self.split_into_sentences(document['full_text'])
        
        for i in range(0, len(sentences), self.chunk_size // 50):  # ~50 chars per sentence avg
            chunk_sentences = sentences[i:i + self.chunk_size // 50]
            chunk_text = ' '.join(chunk_sentences)
            
            # Add context from previous and next chunks
            context_before = ' '.join(sentences[max(0, i-5):i]) if i > 0 else ""
            context_after = ' '.join(sentences[i + len(chunk_sentences):i + len(chunk_sentences) + 5])
            
            chunks.append({
                'text': chunk_text,
                'context_before': context_before,
                'context_after': context_after,
                'chunk_type': 'contextual',
                'position': i
            })
        
        return chunks
```

### **Task 2B: Ollama Integration Service**
```python
# backend/services/ollama_service.py
import requests
import json
from typing import Dict, List, Optional

class OllamaService:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.available_models = []
        self.current_model = "llama2"
    
    async def generate_response(self, prompt: str, context: List[str], model: str = None) -> Dict:
        """Generate response using Ollama LLM with scientific context"""
        model = model or self.current_model
        
        # Construct scientific prompt with context
        scientific_prompt = self.build_scientific_prompt(prompt, context)
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": scientific_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for scientific accuracy
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'response': result['response'],
                'model': model,
                'context_used': len(context),
                'prompt_tokens': len(scientific_prompt.split()),
                'citations': self.extract_citations_from_context(context)
            }
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def build_scientific_prompt(self, query: str, context: List[str]) -> str:
        """Build scientific research prompt with context"""
        context_text = "\n\n".join([f"Source {i+1}: {ctx}" for i, ctx in enumerate(context)])
        
        prompt = f"""You are a scientific research assistant with access to a corpus of peer-reviewed scientific literature. 
        
Based on the following research papers and scientific sources, please provide a comprehensive and accurate answer to the user's question.

SCIENTIFIC SOURCES:
{context_text}

RESEARCH QUESTION: {query}

Please provide a detailed, evidence-based response that:
1. Directly addresses the research question
2. Cites specific sources using [Source X] notation
3. Highlights key findings and methodologies
4. Notes any limitations or conflicting evidence
5. Suggests areas for further research if relevant

RESPONSE:"""
        
        return prompt
```

### **Task 2C: RAG Query Pipeline**
```python
# backend/services/rag_service.py
from typing import Dict, List
import asyncio

class ScientificRAGService:
    def __init__(self, vector_store, ollama_service, pdf_processor):
        self.vector_store = vector_store
        self.ollama_service = ollama_service
        self.pdf_processor = pdf_processor
    
    async def process_scientific_query(self, query: str, filters: Dict = None) -> Dict:
        """Process scientific research query using RAG pipeline"""
        
        # Step 1: Query preprocessing and expansion
        expanded_query = await self.expand_scientific_query(query)
        
        # Step 2: Retrieve relevant document chunks
        search_results = self.vector_store.semantic_search(
            expanded_query, 
            n_results=20
        )
        
        # Step 3: Filter and rank results
        filtered_results = self.filter_by_relevance(search_results, query)
        
        # Step 4: Select best context chunks
        context_chunks = self.select_context_chunks(filtered_results[:10])
        
        # Step 5: Generate response with LLM
        response = await self.ollama_service.generate_response(
            query, 
            context_chunks
        )
        
        # Step 6: Post-process and add citations
        final_response = self.add_citations_and_sources(response, filtered_results)
        
        return {
            'query': query,
            'response': final_response['response'],
            'sources': final_response['sources'],
            'context_used': len(context_chunks),
            'total_results_found': len(search_results),
            'processing_time': final_response.get('processing_time', 0)
        }
    
    async def expand_scientific_query(self, query: str) -> str:
        """Expand query with scientific synonyms and related terms"""
        # Add scientific term expansion logic
        scientific_synonyms = {
            'gene': ['genetic', 'genomic', 'allele', 'locus'],
            'protein': ['polypeptide', 'enzyme', 'peptide'],
            'cell': ['cellular', 'cytoplasm', 'membrane'],
            # Add more scientific term mappings
        }
        
        expanded_terms = []
        for word in query.lower().split():
            if word in scientific_synonyms:
                expanded_terms.extend(scientific_synonyms[word])
        
        return f"{query} {' '.join(expanded_terms)}"
```

---

## 📊 **PHASE 3: FRONTEND INTEGRATION (Week 3)**

### **Task 3A: Enhanced Document Upload Interface**
```typescript
// src/components/ScientificCorpusManager.tsx
import React, { useState, useCallback } from 'react';
import { Upload, FileText, Database, Search, BarChart } from 'lucide-react';

interface CorpusStats {
  totalDocuments: number;
  totalChunks: number;
  averageProcessingTime: number;
  lastUpdated: string;
}

export const ScientificCorpusManager: React.FC = () => {
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [corpusStats, setCorpusStats] = useState<CorpusStats | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleBulkUpload = useCallback(async (files: FileList) => {
    setIsProcessing(true);
    const formData = new FormData();
    
    Array.from(files).forEach((file, index) => {
      formData.append(`pdf_${index}`, file);
    });

    try {
      const response = await fetch('/api/corpus/bulk-upload', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        // Handle successful upload
        await refreshCorpusStats();
      }
    } catch (error) {
      console.error('Bulk upload failed:', error);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  return (
    <div className="p-6 bg-gray-900 text-white">
      <h2 className="text-2xl font-bold mb-6">📚 Scientific Corpus Management</h2>
      
      {/* Corpus Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-800 p-4 rounded-lg">
          <FileText className="w-8 h-8 text-blue-400 mb-2" />
          <h3 className="text-lg font-semibold">{corpusStats?.totalDocuments || 0}</h3>
          <p className="text-gray-400">Scientific Papers</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <Database className="w-8 h-8 text-green-400 mb-2" />
          <h3 className="text-lg font-semibold">{corpusStats?.totalChunks || 0}</h3>
          <p className="text-gray-400">Text Chunks</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <BarChart className="w-8 h-8 text-purple-400 mb-2" />
          <h3 className="text-lg font-semibold">{corpusStats?.averageProcessingTime || 0}s</h3>
          <p className="text-gray-400">Avg Processing</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <Search className="w-8 h-8 text-yellow-400 mb-2" />
          <h3 className="text-lg font-semibold">Ready</h3>
          <p className="text-gray-400">Search Status</p>
        </div>
      </div>

      {/* Bulk Upload Interface */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">📤 Bulk PDF Upload</h3>
        <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-400 mb-4">
            Drop your scientific PDFs here or click to browse
          </p>
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={(e) => e.target.files && handleBulkUpload(e.target.files)}
            className="hidden"
            id="bulk-upload"
          />
          <label
            htmlFor="bulk-upload"
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg cursor-pointer inline-block"
          >
            Select PDF Files
          </label>
        </div>
        
        {isProcessing && (
          <div className="mt-4">
            <div className="bg-gray-700 rounded-full h-2">
              <div 
                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-400 mt-2">
              Processing documents... {uploadProgress}%
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
```

### **Task 3B: Scientific Query Interface**
```typescript
// src/components/ScientificQueryInterface.tsx
import React, { useState } from 'react';
import { Search, BookOpen, Quote, ExternalLink } from 'lucide-react';

interface ScientificResponse {
  response: string;
  sources: Array<{
    title: string;
    authors: string[];
    journal: string;
    year: number;
    doi?: string;
    relevance_score: number;
  }>;
  context_used: number;
  processing_time: number;
}

export const ScientificQueryInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<ScientificResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleScientificQuery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const result = await fetch('/api/rag/scientific-query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ 
          query,
          filters: {
            min_relevance: 0.7,
            max_sources: 10
          }
        })
      });

      if (result.ok) {
        const data = await result.json();
        setResponse(data);
      }
    } catch (error) {
      console.error('Scientific query failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <BookOpen className="w-5 h-5 mr-2 text-blue-400" />
          Scientific Literature Query
        </h3>
        
        <div className="flex space-x-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a scientific question (e.g., 'What are the latest findings on CRISPR gene editing?')"
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
            onKeyPress={(e) => e.key === 'Enter' && handleScientificQuery()}
          />
          <button
            onClick={handleScientificQuery}
            disabled={isLoading || !query.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-6 py-3 rounded-lg flex items-center"
          >
            <Search className="w-4 h-4 mr-2" />
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {response && (
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="mb-4 flex items-center justify-between">
            <h4 className="text-lg font-semibold">Research Findings</h4>
            <div className="text-sm text-gray-400">
              {response.context_used} sources • {response.processing_time}s
            </div>
          </div>
          
          <div className="prose prose-invert max-w-none mb-6">
            <p className="whitespace-pre-wrap">{response.response}</p>
          </div>

          <div className="border-t border-gray-700 pt-4">
            <h5 className="font-semibold mb-3 flex items-center">
              <Quote className="w-4 h-4 mr-2" />
              Sources ({response.sources.length})
            </h5>
            <div className="space-y-3">
              {response.sources.map((source, index) => (
                <div key={index} className="bg-gray-700 p-3 rounded">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h6 className="font-medium">{source.title}</h6>
                      <p className="text-sm text-gray-400">
                        {source.authors.join(', ')} • {source.journal} ({source.year})
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-blue-600 px-2 py-1 rounded">
                        {Math.round(source.relevance_score * 100)}% match
                      </span>
                      {source.doi && (
                        <a
                          href={`https://doi.org/${source.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 🎯 **IMMEDIATE ACTION ITEMS (Next 48 Hours)**

### **Priority 1: Quick Setup**
1. [ ] **Add Ollama to docker-compose.yml** (30 minutes)
2. [ ] **Install required Python packages** (15 minutes)
   ```bash
   pip install ollama PyMuPDF pdfplumber sentence-transformers chromadb langchain
   ```
3. [ ] **Create basic PDF processor** (2 hours)
4. [ ] **Set up ChromaDB collection** (1 hour)
5. [ ] **Test with 5 sample PDFs** (1 hour)

### **Priority 2: Basic RAG Pipeline**
1. [ ] **Create Ollama service class** (2 hours)
2. [ ] **Implement document chunking** (3 hours)
3. [ ] **Build basic query interface** (2 hours)
4. [ ] **Test end-to-end pipeline** (1 hour)

### **Priority 3: Frontend Integration**
1. [ ] **Add corpus management page** (3 hours)
2. [ ] **Create scientific query interface** (4 hours)
3. [ ] **Implement file upload with progress** (2 hours)
4. [ ] **Add source citation display** (2 hours)

---

## 📋 **Weekly Milestones**

### **Week 1 Goal:**
- ✅ Ollama running with Llama2/Mistral
- ✅ Process 50+ scientific PDFs
- ✅ Basic semantic search working
- ✅ Simple Q&A interface

### **Week 2 Goal:**
- ✅ Advanced chunking strategies
- ✅ Citation tracking and attribution
- ✅ Query expansion and refinement
- ✅ Response quality evaluation

### **Week 3 Goal:**
- ✅ Production-ready UI
- ✅ Bulk document processing
- ✅ Advanced search filters
- ✅ Research analytics dashboard

This implementation will transform AI Scholar into a powerful scientific research assistant that can intelligently query and synthesize information from your entire corpus of scientific literature using state-of-the-art RAG techniques with local LLMs!