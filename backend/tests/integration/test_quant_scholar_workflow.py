"""
Integration tests for Quant Scholar with journal sources.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import sys

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from multi_instance_arxiv_system.core.instance_config import InstanceConfig
    from multi_instance_arxiv_system.downloaders.quant_scholar_downloader import QuantScholarDownloader
    from multi_instance_arxiv_system.processors.quant_scholar_processor import QuantScholarProcessor
    from multi_instance_arxiv_system.journal_sources.jstat_software_handler import JStatSoftwareHandler
    from multi_instance_arxiv_system.journal_sources.r_journal_handler import RJournalHandler
    from multi_instance_arxiv_system.models.paper_models import ArxivPaper, JournalPaper
    from multi_instance_arxiv_system.vector_store.multi_instance_vector_store_service import MultiInstanceVectorStoreService
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class TestQuantScholarEndToEndWorkflow:
    """End-to-end integration tests for Quant Scholar workflow."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def quant_scholar_config(self, temp_dir):
        """Create Quant Scholar configuration."""
        return InstanceConfig(
            instance_name="quant_scholar",
            storage_path=str(temp_dir),
            arxiv_categories=["q-fin.*", "stat.AP", "stat.ME", "math.ST"],
            journal_sources=["jstatsoft", "rjournal"],
            max_papers_per_run=50,
            processing_batch_size=10,
            vector_store_collection="quant_scholar_papers",
            email_notifications=True
        )
    
    @pytest.fixture
    def sample_qfin_papers(self):
        """Create sample q-fin ArXiv papers."""
        return [
            {
                'id': '2023.qfin001',
                'title': 'Portfolio Optimization with Machine Learning',
                'authors': ['Alice Quant', 'Bob Finance'],
                'abstract': 'This paper presents ML approaches for portfolio optimization.',
                'categories': ['q-fin.PM', 'stat.ML'],
                'published': datetime.now() - timedelta(days=1),
                'pdf_url': 'https://arxiv.org/pdf/2023.qfin001.pdf'
            },
            {
                'id': '2023.stat001',
                'title': 'Statistical Methods for Risk Management',
                'authors': ['Carol Stats', 'David Risk'],
                'abstract': 'We explore statistical approaches to financial risk management.',
                'categories': ['stat.AP', 'q-fin.RM'],
                'published': datetime.now() - timedelta(days=2),
                'pdf_url': 'https://arxiv.org/pdf/2023.stat001.pdf'
            }
        ]
    
    @pytest.fixture
    def sample_jss_papers(self):
        """Create sample JSS journal papers."""
        return [
            {
                'title': 'R Package for Financial Time Series Analysis',
                'authors': ['John R. Developer', 'Jane Stats'],
                'abstract': 'This paper introduces an R package for analyzing financial time series.',
                'volume': '95',
                'issue': '2',
                'year': '2023',
                'doi': '10.18637/jss.v095.i02',
                'pdf_url': 'https://www.jstatsoft.org/article/view/v095i02/v095i02.pdf',
                'journal_name': 'Journal of Statistical Software'
            }
        ]
    
    @pytest.fixture
    def sample_rjournal_papers(self):
        """Create sample R Journal papers."""
        return [
            {
                'title': 'Advanced Econometric Modeling in R',
                'authors': ['Robert Economist', 'Sarah Modeler'],
                'abstract': 'This article presents advanced econometric modeling techniques using R.',
                'volume': '15',
                'issue': '1',
                'year': '2023',
                'pages': '45-67',
                'pdf_url': 'https://journal.r-project.org/archive/2023-1/economist-modeler.pdf',
                'journal_name': 'The R Journal'
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_quant_scholar_pipeline(self, quant_scholar_config, sample_qfin_papers, 
                                                  sample_jss_papers, sample_rjournal_papers, temp_dir):
        """Test complete Quant Scholar download and processing pipeline with multiple sources."""
        
        downloader = QuantScholarDownloader(quant_scholar_config)
        processor = QuantScholarProcessor(quant_scholar_config)
        
        # Mock ArXiv API responses
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get, \
             patch.object(downloader.jss_handler, 'fetch_recent_papers') as mock_jss_fetch, \
             patch.object(downloader.rjournal_handler, 'fetch_recent_papers') as mock_rj_fetch, \
             patch.object(downloader.jss_handler, 'extract_paper_metadata') as mock_jss_metadata, \
             patch.object(downloader.rjournal_handler, 'extract_paper_metadata') as mock_rj_metadata:
            
            # Mock ArXiv RSS feed response
            mock_feed = Mock()
            mock_feed.entries = []
            
            for paper_data in sample_qfin_papers:
                entry = Mock()
                entry.id = paper_data['id']
                entry.title = paper_data['title']
                entry.authors = [{'name': author} for author in paper_data['authors']]
                entry.summary = paper_data['abstract']
                entry.tags = [{'term': cat} for cat in paper_data['categories']]
                entry.published = paper_data['published'].strftime('%Y-%m-%dT%H:%M:%SZ')
                entry.links = [{'href': paper_data['pdf_url'], 'type': 'application/pdf'}]
                mock_feed.entries.append(entry)
            
            mock_feedparser.return_value = mock_feed
            
            # Mock journal source responses
            mock_jss_fetch.return_value = [{'link': 'https://www.jstatsoft.org/article/view/v095i02'}]
            mock_rj_fetch.return_value = [{'link': 'https://journal.r-project.org/archive/2023-1/economist-modeler.pdf'}]
            
            mock_jss_metadata.return_value = sample_jss_papers[0]
            mock_rj_metadata.return_value = sample_rjournal_papers[0]
            
            # Mock PDF download responses
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content = b'Mock PDF content for testing'
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            # Step 1: Download papers from all sources
            download_result = await downloader.download_recent_papers(days_back=7)
            
            assert download_result['success'] == True
            assert download_result['arxiv_papers_downloaded'] == 2
            assert download_result['journal_papers_downloaded'] == 2
            assert download_result['total_papers_downloaded'] == 4
            
            # Verify papers were saved to storage
            papers_dir = temp_dir / "papers"
            assert papers_dir.exists()
            
            pdf_files = list(papers_dir.glob("*.pdf"))
            assert len(pdf_files) == 4
            
            # Verify metadata was saved
            metadata_dir = temp_dir / "metadata"
            assert metadata_dir.exists()
            
            metadata_files = list(metadata_dir.glob("*.json"))
            assert len(metadata_files) == 4
            
            # Step 2: Process papers
            with patch.object(processor.vector_store, 'add_documents') as mock_add_docs:
                mock_add_docs.return_value = True
                
                processing_result = await processor.process_downloaded_papers()
                
                assert processing_result['success'] == True
                assert processing_result['papers_processed'] == 4
                
                # Verify vector store was called
                mock_add_docs.assert_called()
                
                # Check that documents were created with proper metadata
                call_args = mock_add_docs.call_args[1]
                documents = call_args['documents']
                
                assert len(documents) == 4
                
                # Verify mixed document types (ArXiv and Journal papers)
                arxiv_docs = [doc for doc in documents if 'arxiv_id' in doc['metadata']]
                journal_docs = [doc for doc in documents if 'journal_name' in doc['metadata']]
                
                assert len(arxiv_docs) == 2
                assert len(journal_docs) == 2
                
                # Verify all documents have quant_scholar instance
                for doc in documents:
                    assert doc['metadata']['instance_name'] == 'quant_scholar'
    
    @pytest.mark.asyncio
    async def test_quant_scholar_wildcard_category_matching(self, quant_scholar_config, temp_dir):
        """Test wildcard category matching for q-fin.* categories."""
        
        downloader = QuantScholarDownloader(quant_scholar_config)
        
        # Create papers with various q-fin subcategories
        qfin_papers = [
            {
                'id': '2023.qfin.cp',
                'title': 'Computational Finance Paper',
                'categories': ['q-fin.CP'],  # Should match q-fin.*
                'published': datetime.now()
            },
            {
                'id': '2023.qfin.ec',
                'title': 'Economics Paper',
                'categories': ['q-fin.EC'],  # Should match q-fin.*
                'published': datetime.now()
            },
            {
                'id': '2023.qfin.mf',
                'title': 'Mathematical Finance Paper',
                'categories': ['q-fin.MF'],  # Should match q-fin.*
                'published': datetime.now()
            },
            {
                'id': '2023.physics',
                'title': 'Physics Paper',
                'categories': ['physics.gen-ph'],  # Should not match
                'published': datetime.now()
            }
        ]
        
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get:
            
            mock_feed = Mock()
            mock_feed.entries = []
            
            for paper_data in qfin_papers:
                entry = Mock()
                entry.id = paper_data['id']
                entry.title = paper_data['title']
                entry.authors = [{'name': 'Test Author'}]
                entry.summary = 'Test abstract'
                entry.tags = [{'term': cat} for cat in paper_data['categories']]
                entry.published = paper_data['published'].strftime('%Y-%m-%dT%H:%M:%SZ')
                entry.links = [{'href': f'https://arxiv.org/pdf/{paper_data["id"]}.pdf', 'type': 'application/pdf'}]
                mock_feed.entries.append(entry)
            
            mock_feedparser.return_value = mock_feed
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content = b'Mock PDF content'
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            download_result = await downloader.download_recent_papers(days_back=7)
            
            # Should download all q-fin.* papers but not physics
            assert download_result['arxiv_papers_downloaded'] == 3
            
            # Verify correct papers were downloaded
            downloaded_ids = [paper.paper_id for paper in downloader.downloaded_papers]
            assert '2023.qfin.cp' in downloaded_ids
            assert '2023.qfin.ec' in downloaded_ids
            assert '2023.qfin.mf' in downloaded_ids
            assert '2023.physics' not in downloaded_ids
    
    @pytest.mark.asyncio
    async def test_journal_source_integration(self, quant_scholar_config, temp_dir):
        """Test integration with journal sources (JSS and R Journal)."""
        
        downloader = QuantScholarDownloader(quant_scholar_config)
        
        # Mock journal handlers
        with patch.object(downloader.jss_handler, 'fetch_recent_papers') as mock_jss_fetch, \
             patch.object(downloader.rjournal_handler, 'fetch_recent_papers') as mock_rj_fetch, \
             patch.object(downloader.jss_handler, 'extract_paper_metadata') as mock_jss_metadata, \
             patch.object(downloader.rjournal_handler, 'extract_paper_metadata') as mock_rj_metadata, \
             patch.object(downloader.jss_handler, 'download_paper_pdf') as mock_jss_pdf, \
             patch.object(downloader.rjournal_handler, 'download_paper_pdf') as mock_rj_pdf:
            
            # Mock JSS responses
            mock_jss_fetch.return_value = [
                {'link': 'https://www.jstatsoft.org/article/view/v095i01'},
                {'link': 'https://www.jstatsoft.org/article/view/v095i02'}
            ]
            
            mock_jss_metadata.side_effect = [
                {
                    'title': 'JSS Paper 1',
                    'authors': ['Author 1'],
                    'abstract': 'JSS abstract 1',
                    'volume': '95',
                    'issue': '1',
                    'year': '2023',
                    'doi': '10.18637/jss.v095.i01',
                    'pdf_url': 'https://www.jstatsoft.org/article/view/v095i01/v095i01.pdf'
                },
                {
                    'title': 'JSS Paper 2',
                    'authors': ['Author 2'],
                    'abstract': 'JSS abstract 2',
                    'volume': '95',
                    'issue': '2',
                    'year': '2023',
                    'doi': '10.18637/jss.v095.i02',
                    'pdf_url': 'https://www.jstatsoft.org/article/view/v095i02/v095i02.pdf'
                }
            ]
            
            # Mock R Journal responses
            mock_rj_fetch.return_value = [
                {'link': 'https://journal.r-project.org/archive/2023-1/paper1.pdf'}
            ]
            
            mock_rj_metadata.return_value = {
                'title': 'R Journal Paper',
                'authors': ['R Author'],
                'abstract': 'R Journal abstract',
                'volume': '15',
                'issue': '1',
                'year': '2023',
                'pages': '1-20',
                'pdf_url': 'https://journal.r-project.org/archive/2023-1/paper1.pdf'
            }
            
            # Mock PDF downloads
            mock_jss_pdf.return_value = b'JSS PDF content'
            mock_rj_pdf.return_value = b'R Journal PDF content'
            
            # Mock ArXiv (no papers)
            with patch('feedparser.parse') as mock_feedparser:
                mock_feed = Mock()
                mock_feed.entries = []
                mock_feedparser.return_value = mock_feed
                
                # Download from journal sources only
                download_result = await downloader.download_recent_papers(days_back=7)
                
                assert download_result['success'] == True
                assert download_result['arxiv_papers_downloaded'] == 0
                assert download_result['journal_papers_downloaded'] == 3  # 2 JSS + 1 R Journal
                
                # Verify journal papers were created correctly
                journal_papers = [p for p in downloader.downloaded_papers if isinstance(p, JournalPaper)]
                assert len(journal_papers) == 3
                
                # Check JSS papers
                jss_papers = [p for p in journal_papers if p.journal_name == 'Journal of Statistical Software']
                assert len(jss_papers) == 2
                
                # Check R Journal papers
                rj_papers = [p for p in journal_papers if p.journal_name == 'The R Journal']
                assert len(rj_papers) == 1
    
    @pytest.mark.asyncio
    async def test_quant_scholar_duplicate_detection_across_sources(self, quant_scholar_config, temp_dir):
        """Test duplicate detection across ArXiv and journal sources."""
        
        downloader = QuantScholarDownloader(quant_scholar_config)
        
        # Create existing metadata to simulate duplicates
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Existing ArXiv paper
        existing_arxiv = {
            'paper_id': '2023.existing',
            'title': 'Existing ArXiv Paper',
            'source_type': 'arxiv',
            'downloaded_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'instance_name': 'quant_scholar'
        }
        
        with open(metadata_dir / "2023.existing.json", 'w') as f:
            json.dump(existing_arxiv, f)
        
        # Existing journal paper
        existing_journal = {
            'paper_id': 'jss_v095_i01',
            'title': 'Existing JSS Paper',
            'source_type': 'journal',
            'journal_name': 'Journal of Statistical Software',
            'downloaded_at': (datetime.now() - timedelta(days=2)).isoformat(),
            'instance_name': 'quant_scholar'
        }
        
        with open(metadata_dir / "jss_v095_i01.json", 'w') as f:
            json.dump(existing_journal, f)
        
        # Mock sources returning both new and existing papers
        with patch('feedparser.parse') as mock_feedparser, \
             patch('aiohttp.ClientSession.get') as mock_http_get, \
             patch.object(downloader.jss_handler, 'fetch_recent_papers') as mock_jss_fetch, \
             patch.object(downloader.jss_handler, 'extract_paper_metadata') as mock_jss_metadata:
            
            # Mock ArXiv returning existing + new paper
            mock_feed = Mock()
            mock_feed.entries = []
            
            # Existing paper (should be skipped)
            existing_entry = Mock()
            existing_entry.id = '2023.existing'
            existing_entry.title = 'Existing ArXiv Paper'
            existing_entry.authors = [{'name': 'Test Author'}]
            existing_entry.summary = 'Test abstract'
            existing_entry.tags = [{'term': 'q-fin.PM'}]
            existing_entry.published = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            existing_entry.links = [{'href': 'https://arxiv.org/pdf/2023.existing.pdf', 'type': 'application/pdf'}]
            mock_feed.entries.append(existing_entry)
            
            # New paper (should be downloaded)
            new_entry = Mock()
            new_entry.id = '2023.new'
            new_entry.title = 'New ArXiv Paper'
            new_entry.authors = [{'name': 'Test Author'}]
            new_entry.summary = 'Test abstract'
            new_entry.tags = [{'term': 'q-fin.PM'}]
            new_entry.published = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            new_entry.links = [{'href': 'https://arxiv.org/pdf/2023.new.pdf', 'type': 'application/pdf'}]
            mock_feed.entries.append(new_entry)
            
            mock_feedparser.return_value = mock_feed
            
            # Mock JSS returning existing + new paper
            mock_jss_fetch.return_value = [
                {'link': 'https://www.jstatsoft.org/article/view/v095i01'},  # Existing
                {'link': 'https://www.jstatsoft.org/article/view/v095i02'}   # New
            ]
            
            mock_jss_metadata.side_effect = [
                {
                    'title': 'Existing JSS Paper',
                    'volume': '95',
                    'issue': '1',
                    'year': '2023',
                    'doi': '10.18637/jss.v095.i01'
                },
                {
                    'title': 'New JSS Paper',
                    'volume': '95',
                    'issue': '2',
                    'year': '2023',
                    'doi': '10.18637/jss.v095.i02'
                }
            ]
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.content = b'Mock PDF content'
            mock_http_get.return_value.__aenter__.return_value = mock_response
            
            download_result = await downloader.download_recent_papers(days_back=7)
            
            # Should download only new papers
            assert download_result['arxiv_papers_downloaded'] == 1  # Only new ArXiv paper
            assert download_result['journal_papers_downloaded'] == 1  # Only new JSS paper
            assert download_result['duplicates_skipped'] == 2  # Both existing papers skipped
    
    @pytest.mark.asyncio
    async def test_quant_scholar_unified_processing(self, quant_scholar_config, temp_dir):
        """Test unified processing pipeline for multiple source types."""
        
        processor = QuantScholarProcessor(quant_scholar_config)
        
        # Create mixed paper types in storage
        papers_dir = temp_dir / "papers"
        papers_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_dir = temp_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # ArXiv paper
        arxiv_metadata = {
            'paper_id': '2023.qfin001',
            'title': 'ArXiv Quant Paper',
            'authors': ['ArXiv Author'],
            'abstract': 'ArXiv abstract about quantitative finance',
            'categories': ['q-fin.PM'],
            'source_type': 'arxiv',
            'instance_name': 'quant_scholar',
            'downloaded_at': datetime.now().isoformat()
        }
        
        with open(papers_dir / "2023.qfin001.pdf", 'wb') as f:
            f.write(b'ArXiv PDF content')
        
        with open(metadata_dir / "2023.qfin001.json", 'w') as f:
            json.dump(arxiv_metadata, f)
        
        # Journal paper (JSS)
        jss_metadata = {
            'paper_id': 'jss_v095_i01',
            'title': 'JSS Statistical Software Paper',
            'authors': ['JSS Author'],
            'abstract': 'JSS abstract about statistical software',
            'journal_name': 'Journal of Statistical Software',
            'volume': '95',
            'issue': '1',
            'year': '2023',
            'source_type': 'journal',
            'instance_name': 'quant_scholar',
            'downloaded_at': datetime.now().isoformat()
        }
        
        with open(papers_dir / "jss_v095_i01.pdf", 'wb') as f:
            f.write(b'JSS PDF content')
        
        with open(metadata_dir / "jss_v095_i01.json", 'w') as f:
            json.dump(jss_metadata, f)
        
        # Journal paper (R Journal)
        rj_metadata = {
            'paper_id': 'rjournal_2023_1_paper1',
            'title': 'R Journal Econometrics Paper',
            'authors': ['R Journal Author'],
            'abstract': 'R Journal abstract about econometric methods',
            'journal_name': 'The R Journal',
            'volume': '15',
            'issue': '1',
            'year': '2023',
            'source_type': 'journal',
            'instance_name': 'quant_scholar',
            'downloaded_at': datetime.now().isoformat()
        }
        
        with open(papers_dir / "rjournal_2023_1_paper1.pdf", 'wb') as f:
            f.write(b'R Journal PDF content')
        
        with open(metadata_dir / "rjournal_2023_1_paper1.json", 'w') as f:
            json.dump(rj_metadata, f)
        
        # Mock vector store and PDF processing
        with patch.object(processor.vector_store, 'add_documents') as mock_add_docs, \
             patch.object(processor.pdf_processor, 'extract_text') as mock_extract_text:
            
            # Mock PDF text extraction
            mock_extract_text.side_effect = [
                'Extracted text from ArXiv quantitative finance paper',
                'Extracted text from JSS statistical software paper',
                'Extracted text from R Journal econometrics paper'
            ]
            
            mock_add_docs.return_value = True
            
            # Process all papers
            result = await processor.process_downloaded_papers()
            
            assert result['success'] == True
            assert result['papers_processed'] == 3
            assert result['arxiv_papers_processed'] == 1
            assert result['journal_papers_processed'] == 2
            
            # Verify vector store was called with unified documents
            mock_add_docs.assert_called_once()
            
            call_args = mock_add_docs.call_args[1]
            documents = call_args['documents']
            collection_name = call_args['collection_name']
            
            assert collection_name == 'quant_scholar_papers'
            assert len(documents) == 3
            
            # Verify document metadata includes source type information
            arxiv_docs = [doc for doc in documents if doc['metadata'].get('source_type') == 'arxiv']
            journal_docs = [doc for doc in documents if doc['metadata'].get('source_type') == 'journal']
            
            assert len(arxiv_docs) == 1
            assert len(journal_docs) == 2
            
            # Verify all documents have quant_scholar instance
            for doc in documents:
                assert doc['metadata']['instance_name'] == 'quant_scholar'
                assert 'paper_id' in doc['metadata']
                assert 'title' in doc['metadata']


class TestQuantScholarJournalHandlers:
    """Integration tests for journal handlers in Quant Scholar context."""
    
    @pytest.mark.asyncio
    async def test_jss_handler_integration(self):
        """Test JSS handler integration with Quant Scholar."""
        
        handler = JStatSoftwareHandler()
        
        # Mock JSS RSS feed and paper pages
        with patch('aiohttp.ClientSession.get') as mock_get:
            
            # Mock RSS feed response
            rss_response = AsyncMock()
            rss_response.status = 200
            rss_response.text = AsyncMock(return_value="""<?xml version="1.0"?>
                <rss version="2.0">
                    <channel>
                        <item>
                            <title>Financial Time Series Analysis in R</title>
                            <link>https://www.jstatsoft.org/article/view/v095i01</link>
                            <description>Statistical software for financial analysis</description>
                            <pubDate>Mon, 15 May 2023 00:00:00 GMT</pubDate>
                        </item>
                    </channel>
                </rss>""")
            
            # Mock paper page response
            paper_response = AsyncMock()
            paper_response.status = 200
            paper_response.text = AsyncMock(return_value="""
                <html>
                    <head>
                        <title>Financial Time Series Analysis in R</title>
                        <meta name="citation_author" content="John Statistician">
                        <meta name="citation_volume" content="95">
                        <meta name="citation_issue" content="1">
                        <meta name="citation_publication_date" content="2023">
                        <meta name="citation_doi" content="10.18637/jss.v095.i01">
                        <meta name="citation_pdf_url" content="https://www.jstatsoft.org/article/view/v095i01/v095i01.pdf">
                    </head>
                    <body>
                        <div class="abstract">
                            <p>This paper presents statistical software for financial time series analysis.</p>
                        </div>
                    </body>
                </html>
            """)
            
            # Mock PDF download response
            pdf_response = AsyncMock()
            pdf_response.status = 200
            pdf_response.read = AsyncMock(return_value=b'Mock JSS PDF content')
            
            # Configure mock responses
            mock_get.return_value.__aenter__.side_effect = [
                rss_response,  # RSS feed
                paper_response,  # Paper page
                pdf_response   # PDF download
            ]
            
            # Test complete workflow
            papers = await handler.fetch_recent_papers(days_back=30)
            assert len(papers) == 1
            
            paper_url = papers[0]['link']
            metadata = await handler.extract_paper_metadata(paper_url)
            
            assert metadata is not None
            assert metadata['title'] == 'Financial Time Series Analysis in R'
            assert metadata['volume'] == '95'
            assert metadata['issue'] == '1'
            
            pdf_content = await handler.download_paper_pdf(metadata['pdf_url'])
            assert pdf_content == b'Mock JSS PDF content'
    
    @pytest.mark.asyncio
    async def test_rjournal_handler_integration(self):
        """Test R Journal handler integration with Quant Scholar."""
        
        handler = RJournalHandler()
        
        # Mock R Journal archive page and paper content
        with patch('aiohttp.ClientSession.get') as mock_get:
            
            # Mock archive page response
            archive_response = AsyncMock()
            archive_response.status = 200
            archive_response.text = AsyncMock(return_value="""
                <html>
                    <body>
                        <div class="issue">
                            <h2>Volume 15, Issue 1 (2023)</h2>
                            <div class="article">
                                <h3><a href="/archive/2023-1/econometric-methods.pdf">Econometric Methods in R</a></h3>
                                <p class="authors">Jane Econometrician, Bob Statistician</p>
                                <p class="abstract">Advanced econometric modeling techniques using R packages.</p>
                            </div>
                        </div>
                    </body>
                </html>
            """)
            
            # Mock paper page response
            paper_response = AsyncMock()
            paper_response.status = 200
            paper_response.text = AsyncMock(return_value="""
                <html>
                    <head>
                        <title>Econometric Methods in R</title>
                    </head>
                    <body>
                        <div class="paper-metadata">
                            <h1>Econometric Methods in R</h1>
                            <p class="authors">Jane Econometrician, Bob Statistician</p>
                            <p class="volume-issue">Volume 15, Issue 1 (2023), pages 23-45</p>
                            <div class="abstract">
                                <p>Advanced econometric modeling techniques using R packages.</p>
                            </div>
                        </div>
                    </body>
                </html>
            """)
            
            # Mock PDF download response
            pdf_response = AsyncMock()
            pdf_response.status = 200
            pdf_response.read = AsyncMock(return_value=b'Mock R Journal PDF content')
            
            # Configure mock responses
            mock_get.return_value.__aenter__.side_effect = [
                archive_response,  # Archive page
                paper_response,    # Paper page
                pdf_response       # PDF download
            ]
            
            # Test complete workflow
            papers = await handler.fetch_recent_papers(days_back=30)
            assert len(papers) == 1
            
            paper_url = papers[0]['link']
            metadata = await handler.extract_paper_metadata(paper_url)
            
            assert metadata is not None
            assert 'Econometric Methods' in metadata['title']
            assert 'Jane Econometrician' in metadata['authors']
            
            pdf_content = await handler.download_paper_pdf(paper_url)
            assert pdf_content == b'Mock R Journal PDF content'