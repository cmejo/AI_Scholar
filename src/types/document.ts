export interface Document {
  id: string;
  title: string;
  content: string;
  type: 'pdf' | 'text' | 'research_paper' | 'note';
  size: number;
  uploadDate: Date;
  lastModified: Date;
  tags: string[];
  metadata: {
    authors?: string[];
    year?: number;
    journal?: string;
    doi?: string;
    abstract?: string;
  };
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  relevance_score: number;
  source: string;
  type: string;
  metadata: {
    authors?: string[];
    year?: number;
    journal?: string;
  };
}

export interface SearchResponse {
  status: string;
  timestamp: string;
  query: string;
  results: SearchResult[];
  total_results: number;
  service_used: string;
  message: string;
}

export interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}