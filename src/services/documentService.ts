import { Document, SearchResult, SearchResponse } from '../types/document';

class DocumentService {
  private baseUrl = '/api';

  async searchDocuments(query: string, maxResults: number = 10): Promise<SearchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/advanced/research/search/basic`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          max_results: maxResults
        })
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Document search error:', error);
      throw error;
    }
  }

  async uploadDocument(file: File, onProgress?: (progress: number) => void): Promise<Document> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // For now, we'll simulate upload since the backend doesn't have upload endpoints yet
      // In a real implementation, this would be a proper file upload
      
      // Simulate upload progress
      if (onProgress) {
        for (let i = 0; i <= 100; i += 10) {
          setTimeout(() => onProgress(i), i * 10);
        }
      }

      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Return mock document for now
      const mockDocument: Document = {
        id: `doc_${Date.now()}`,
        title: file.name,
        content: `Mock content for ${file.name}`,
        type: this.getDocumentType(file.name),
        size: file.size,
        uploadDate: new Date(),
        lastModified: new Date(),
        tags: [],
        metadata: {
          authors: ['Unknown Author'],
          year: new Date().getFullYear(),
        }
      };

      return mockDocument;
    } catch (error) {
      console.error('Document upload error:', error);
      throw error;
    }
  }

  async getDocuments(): Promise<Document[]> {
    try {
      // For now, return mock documents since backend doesn't have document list endpoint
      const mockDocuments: Document[] = [
        {
          id: 'doc_1',
          title: 'Sample Research Paper.pdf',
          content: 'This is a sample research paper about AI and machine learning.',
          type: 'pdf',
          size: 1024000,
          uploadDate: new Date(Date.now() - 86400000), // 1 day ago
          lastModified: new Date(Date.now() - 86400000),
          tags: ['AI', 'Machine Learning'],
          metadata: {
            authors: ['Dr. Jane Smith', 'Dr. John Doe'],
            year: 2024,
            journal: 'AI Research Journal',
            doi: '10.1000/sample.doi'
          }
        },
        {
          id: 'doc_2',
          title: 'Research Notes.txt',
          content: 'Personal research notes and observations.',
          type: 'text',
          size: 5120,
          uploadDate: new Date(Date.now() - 172800000), // 2 days ago
          lastModified: new Date(Date.now() - 86400000),
          tags: ['Notes', 'Research'],
          metadata: {
            authors: ['User'],
            year: 2024,
          }
        }
      ];

      return mockDocuments;
    } catch (error) {
      console.error('Get documents error:', error);
      throw error;
    }
  }

  async deleteDocument(documentId: string): Promise<void> {
    try {
      // Mock deletion for now
      console.log(`Mock: Deleting document ${documentId}`);
      await new Promise(resolve => setTimeout(resolve, 500));
    } catch (error) {
      console.error('Delete document error:', error);
      throw error;
    }
  }

  private getDocumentType(filename: string): Document['type'] {
    const extension = filename.toLowerCase().split('.').pop();
    switch (extension) {
      case 'pdf':
        return 'pdf';
      case 'txt':
      case 'md':
        return 'text';
      default:
        return 'text';
    }
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDate(date: Date): string {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }
}

export const documentService = new DocumentService();
export default documentService;