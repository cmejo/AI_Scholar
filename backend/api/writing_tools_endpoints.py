"""
Writing Tools API Endpoints

Provides REST API endpoints for writing tool integrations:
- Grammar and style checking with Grammarly/LanguageTool
- LaTeX document compilation and preview
- Document format conversion
- Collaborative writing features
- Export to various writing platforms
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import tempfile
import os
import logging

from ..services.writing_tools_service import (
    WritingToolsService,
    WritingSuggestion,
    GrammarCheckResult,
    LaTeXDocument,
    CompilationResult,
    SuggestionType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/writing-tools", tags=["writing-tools"])

# Pydantic models for API
class GrammarCheckRequest(BaseModel):
    text: str = Field(..., description="Text to check for grammar and style")
    language: str = Field("en-US", description="Language code (e.g., en-US, en-GB)")

class ApplySuggestionsRequest(BaseModel):
    text: str = Field(..., description="Original text")
    suggestion_ids: List[str] = Field(..., description="IDs of suggestions to apply")

class WritingSuggestionResponse(BaseModel):
    id: str
    type: str
    text: str
    start: int
    end: int
    message: str
    suggestions: List[str]
    confidence: float
    severity: str
    category: Optional[str] = None

class GrammarCheckResponse(BaseModel):
    original_text: str
    suggestions: List[WritingSuggestionResponse]
    overall_score: float
    word_count: int
    readability_score: Optional[float] = None
    processing_time_ms: int

class LaTeXDocumentRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="LaTeX content")
    preamble: Optional[str] = Field(None, description="Custom LaTeX preamble")

class LaTeXDocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    preamble: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CompilationResultResponse(BaseModel):
    success: bool
    pdf_path: Optional[str] = None
    log_output: str
    errors: List[str]
    warnings: List[str]
    compilation_time_ms: int

class ConversionRequest(BaseModel):
    document_id: str = Field(..., description="LaTeX document ID")
    target_format: str = Field(..., description="Target format (markdown, html)")

class ExportRequest(BaseModel):
    content: str = Field(..., description="Content to export")
    platform: str = Field(..., description="Target platform")
    credentials: Dict[str, Any] = Field(..., description="Platform credentials")

class CollaborativeEditRequest(BaseModel):
    document_id: str = Field(..., description="Document ID")
    changes: List[Dict[str, Any]] = Field(..., description="List of changes")

class WritingAnalysisResponse(BaseModel):
    word_count: int
    sentence_count: int
    paragraph_count: int
    avg_words_per_sentence: float
    avg_sentences_per_paragraph: float
    readability_score: float
    readability_level: str
    estimated_reading_time_minutes: int

# Initialize service
writing_service = WritingToolsService()

@router.get("/supported")
async def get_supported_tools():
    """Get list of supported writing tools and features"""
    try:
        tools = writing_service.get_supported_tools()
        export_platforms = writing_service.get_supported_export_platforms()
        
        return {
            "success": True,
            "tools": tools,
            "export_platforms": export_platforms,
            "features": {
                "grammar_checking": True,
                "style_analysis": True,
                "latex_compilation": True,
                "format_conversion": True,
                "collaborative_editing": True,
                "document_export": True,
                "readability_analysis": True
            },
            "supported_languages": ["en-US", "en-GB", "de-DE", "fr-FR", "es-ES"],
            "suggestion_types": [t.value for t in SuggestionType]
        }
    except Exception as e:
        logger.error(f"Error getting supported tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/grammar/check", response_model=GrammarCheckResponse)
async def check_grammar(request: GrammarCheckRequest):
    """Check text for grammar, spelling, and style issues"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        result = await writing_service.check_grammar(request.text, request.language)
        
        # Convert suggestions to response format
        suggestion_responses = [
            WritingSuggestionResponse(
                id=suggestion.id,
                type=suggestion.type.value,
                text=suggestion.text,
                start=suggestion.start,
                end=suggestion.end,
                message=suggestion.message,
                suggestions=suggestion.suggestions,
                confidence=suggestion.confidence,
                severity=suggestion.severity,
                category=suggestion.category
            )
            for suggestion in result.suggestions
        ]
        
        return GrammarCheckResponse(
            original_text=result.original_text,
            suggestions=suggestion_responses,
            overall_score=result.overall_score,
            word_count=result.word_count,
            readability_score=result.readability_score,
            processing_time_ms=result.processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Grammar check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/grammar/apply")
async def apply_grammar_suggestions(request: ApplySuggestionsRequest):
    """Apply selected grammar suggestions to text"""
    try:
        # This is a simplified implementation
        # In practice, you'd need to store suggestions and retrieve by ID
        
        # For now, return the original text with a message
        return {
            "success": True,
            "original_text": request.text,
            "corrected_text": request.text,  # Placeholder
            "applied_suggestions": len(request.suggestion_ids),
            "message": "Suggestion application is a placeholder implementation"
        }
        
    except Exception as e:
        logger.error(f"Error applying suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/latex/create", response_model=LaTeXDocumentResponse)
async def create_latex_document(request: LaTeXDocumentRequest):
    """Create a new LaTeX document"""
    try:
        document = await writing_service.create_latex_document(
            request.title, request.content, request.preamble
        )
        
        return LaTeXDocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            preamble=document.preamble,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating LaTeX document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/latex/compile", response_model=CompilationResultResponse)
async def compile_latex_document(request: LaTeXDocumentRequest):
    """Compile LaTeX document to PDF"""
    try:
        # Create document first
        document = await writing_service.create_latex_document(
            request.title, request.content, request.preamble
        )
        
        # Compile document
        result = await writing_service.compile_latex(document)
        
        return CompilationResultResponse(
            success=result.success,
            pdf_path=result.pdf_path,
            log_output=result.log_output,
            errors=result.errors,
            warnings=result.warnings,
            compilation_time_ms=result.compilation_time_ms
        )
        
    except Exception as e:
        logger.error(f"LaTeX compilation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latex/download/{document_id}")
async def download_compiled_pdf(document_id: str):
    """Download compiled PDF file"""
    try:
        # In a real implementation, you'd retrieve the document and its PDF path
        # For now, return an error since we don't have persistent storage
        
        raise HTTPException(
            status_code=404,
            detail="PDF download requires persistent document storage (not implemented)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert")
async def convert_document_format(request: ConversionRequest):
    """Convert LaTeX document to other formats"""
    try:
        # This would require retrieving the stored document
        # For now, return placeholder response
        
        return {
            "success": True,
            "document_id": request.document_id,
            "target_format": request.target_format,
            "converted_content": "Conversion placeholder - requires document storage",
            "message": "Document conversion requires persistent storage (not implemented)"
        }
        
    except Exception as e:
        logger.error(f"Document conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_to_platform(request: ExportRequest):
    """Export document to external writing platform"""
    try:
        success = await writing_service.export_to_platform(
            request.content, request.platform, request.credentials
        )
        
        return {
            "success": success,
            "platform": request.platform,
            "message": f"Export to {request.platform} {'successful' if success else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaborate")
async def handle_collaborative_edit(request: CollaborativeEditRequest):
    """Handle collaborative editing changes"""
    try:
        result = await writing_service.collaborative_edit(
            request.document_id, request.changes
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Collaborative editing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=WritingAnalysisResponse)
async def analyze_writing_style(text: str = Form(...)):
    """Analyze writing style and provide insights"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        analysis = await writing_service.analyze_writing_style(text)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        return WritingAnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Writing analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/latex")
async def upload_latex_file(
    file: UploadFile = File(..., description="LaTeX file to upload"),
    title: str = Form(..., description="Document title")
):
    """Upload and process LaTeX file"""
    try:
        if not file.filename.endswith(('.tex', '.latex')):
            raise HTTPException(
                status_code=400,
                detail="Only .tex and .latex files are supported"
            )
        
        # Read file content
        content = await file.read()
        latex_content = content.decode('utf-8')
        
        # Create document
        document = await writing_service.create_latex_document(
            title, latex_content
        )
        
        return {
            "success": True,
            "document": LaTeXDocumentResponse(
                id=document.id,
                title=document.title,
                content=document.content,
                preamble=document.preamble,
                created_at=document.created_at,
                updated_at=document.updated_at
            ),
            "message": f"LaTeX file '{file.filename}' uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LaTeX upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/latex")
async def get_latex_templates():
    """Get available LaTeX document templates"""
    try:
        templates = {
            "article": {
                "name": "Academic Article",
                "description": "Standard academic article template",
                "preamble": r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{natbib}

\title{Your Article Title}
\author{Your Name}
\date{\today}
""",
                "sample_content": r"""
\section{Introduction}
Your introduction here.

\section{Methods}
Describe your methods.

\section{Results}
Present your results.

\section{Conclusion}
Your conclusions.
"""
            },
            "report": {
                "name": "Technical Report",
                "description": "Technical report template",
                "preamble": r"""
\documentclass[12pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{geometry}
\geometry{margin=1in}

\title{Technical Report Title}
\author{Author Name}
\date{\today}
""",
                "sample_content": r"""
\chapter{Introduction}
Introduction to your report.

\chapter{Background}
Background information.

\chapter{Analysis}
Your analysis.

\chapter{Conclusions}
Final conclusions.
"""
            },
            "thesis": {
                "name": "Thesis/Dissertation",
                "description": "Academic thesis template",
                "preamble": r"""
\documentclass[12pt,a4paper]{book}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{setspace}
\doublespacing

\title{Thesis Title}
\author{Student Name}
\date{\today}
""",
                "sample_content": r"""
\frontmatter
\maketitle
\tableofcontents

\mainmatter
\chapter{Introduction}
Introduction chapter.

\chapter{Literature Review}
Review of existing literature.

\chapter{Methodology}
Research methodology.

\chapter{Results}
Research results.

\chapter{Discussion}
Discussion of results.

\chapter{Conclusion}
Final conclusions.

\backmatter
\bibliography{references}
\bibliographystyle{plain}
"""
            }
        }
        
        return {
            "success": True,
            "templates": templates,
            "total_templates": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting LaTeX templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "writing_tools",
        "timestamp": datetime.now().isoformat(),
        "supported_tools": writing_service.get_supported_tools(),
        "features_available": True
    }

@router.get("/stats")
async def get_writing_tools_stats():
    """Get writing tools statistics"""
    try:
        return {
            "supported_tools": writing_service.get_supported_tools(),
            "export_platforms": writing_service.get_supported_export_platforms(),
            "total_tools": len(writing_service.get_supported_tools()),
            "total_export_platforms": len(writing_service.get_supported_export_platforms()),
            "features": {
                "grammar_checking": "LanguageTool API",
                "latex_compilation": "pdflatex/xelatex/lualatex",
                "format_conversion": "LaTeX to Markdown/HTML",
                "collaborative_editing": "Operational transforms (placeholder)",
                "document_export": "Multiple platforms (placeholder)",
                "style_analysis": "Readability scoring"
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))