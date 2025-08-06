"""
Writing Tools Integration Service

This service provides integration with popular writing tools:
- Grammarly API for grammar and style checking
- LaTeX editor integration with compilation and preview
- Document export to various writing platforms
- Collaborative writing features

Supports real-time checking, document synchronization, and format conversion.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)

class WritingTool(Enum):
    GRAMMARLY = "grammarly"
    LATEX = "latex"
    OVERLEAF = "overleaf"
    MARKDOWN = "markdown"

class SuggestionType(Enum):
    GRAMMAR = "grammar"
    SPELLING = "spelling"
    STYLE = "style"
    CLARITY = "clarity"
    ENGAGEMENT = "engagement"
    DELIVERY = "delivery"

@dataclass
class WritingSuggestion:
    """Writing improvement suggestion"""
    id: str
    type: SuggestionType
    text: str
    start: int
    end: int
    message: str
    suggestions: List[str]
    confidence: float
    severity: str = "medium"  # low, medium, high, critical
    category: Optional[str] = None
    
@dataclass
class GrammarCheckResult:
    """Result of grammar checking"""
    original_text: str
    suggestions: List[WritingSuggestion]
    overall_score: float
    word_count: int
    readability_score: Optional[float] = None
    processing_time_ms: int = 0

@dataclass
class LaTeXDocument:
    """LaTeX document structure"""
    id: str
    title: str
    content: str
    preamble: str = ""
    bibliography: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    compile_log: Optional[str] = None
    pdf_path: Optional[str] = None
    
@dataclass
class CompilationResult:
    """LaTeX compilation result"""
    success: bool
    pdf_path: Optional[str] = None
    log_output: str = ""
    errors: List[str] = None
    warnings: List[str] = None
    compilation_time_ms: int = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class GrammarlyIntegration:
    """Grammarly API integration (simplified implementation)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # Note: Grammarly doesn't have a public API, so this is a simplified implementation
        # In practice, you might use alternative services like LanguageTool
        self.base_url = "https://api.languagetool.org/v2"
        
    async def check_grammar(self, text: str, language: str = "en-US") -> GrammarCheckResult:
        """Check grammar and style using LanguageTool API"""
        try:
            start_time = datetime.now()
            
            # Use LanguageTool as Grammarly alternative
            suggestions = await self._check_with_languagetool(text, language)
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate overall score (simplified)
            total_issues = len(suggestions)
            word_count = len(text.split())
            overall_score = max(0.0, 1.0 - (total_issues / max(word_count, 1)) * 10)
            
            return GrammarCheckResult(
                original_text=text,
                suggestions=suggestions,
                overall_score=overall_score,
                word_count=word_count,
                readability_score=self._calculate_readability(text),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Grammar check error: {e}")
            return GrammarCheckResult(
                original_text=text,
                suggestions=[],
                overall_score=0.0,
                word_count=len(text.split())
            )
    
    async def _check_with_languagetool(self, text: str, language: str) -> List[WritingSuggestion]:
        """Check text with LanguageTool API"""
        suggestions = []
        
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'text': text,
                    'language': language,
                    'enabledOnly': 'false'
                }
                
                async with session.post(f"{self.base_url}/check", data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        for i, match in enumerate(result.get('matches', [])):
                            suggestion = WritingSuggestion(
                                id=f"lt_{i}",
                                type=self._map_languagetool_category(match.get('rule', {}).get('category', {}).get('id', '')),
                                text=text[match['offset']:match['offset'] + match['length']],
                                start=match['offset'],
                                end=match['offset'] + match['length'],
                                message=match['message'],
                                suggestions=[r['value'] for r in match.get('replacements', [])[:3]],
                                confidence=0.8,  # LanguageTool doesn't provide confidence scores
                                severity=self._map_severity(match.get('rule', {}).get('category', {}).get('id', '')),
                                category=match.get('rule', {}).get('category', {}).get('name', '')
                            )
                            suggestions.append(suggestion)
                            
        except Exception as e:
            logger.error(f"LanguageTool API error: {e}")
        
        return suggestions
    
    def _map_languagetool_category(self, category_id: str) -> SuggestionType:
        """Map LanguageTool category to suggestion type"""
        category_mapping = {
            'TYPOS': SuggestionType.SPELLING,
            'GRAMMAR': SuggestionType.GRAMMAR,
            'STYLE': SuggestionType.STYLE,
            'REDUNDANCY': SuggestionType.CLARITY,
            'PLAIN_ENGLISH': SuggestionType.CLARITY
        }
        return category_mapping.get(category_id, SuggestionType.GRAMMAR)
    
    def _map_severity(self, category_id: str) -> str:
        """Map category to severity level"""
        high_severity = ['TYPOS', 'GRAMMAR']
        medium_severity = ['STYLE', 'REDUNDANCY']
        
        if category_id in high_severity:
            return "high"
        elif category_id in medium_severity:
            return "medium"
        else:
            return "low"
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (Flesch Reading Ease)"""
        try:
            import textstat
            return textstat.flesch_reading_ease(text)
        except ImportError:
            # Simplified readability calculation
            sentences = len(re.findall(r'[.!?]+', text))
            words = len(text.split())
            syllables = sum(self._count_syllables(word) for word in text.split())
            
            if sentences == 0 or words == 0:
                return 0.0
            
            # Flesch Reading Ease formula
            score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
            return max(0.0, min(100.0, score))
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    async def apply_suggestions(self, text: str, suggestions: List[WritingSuggestion]) -> str:
        """Apply selected suggestions to text"""
        # Sort suggestions by position (reverse order to maintain indices)
        sorted_suggestions = sorted(suggestions, key=lambda s: s.start, reverse=True)
        
        result_text = text
        for suggestion in sorted_suggestions:
            if suggestion.suggestions:
                # Apply the first suggestion
                replacement = suggestion.suggestions[0]
                result_text = (
                    result_text[:suggestion.start] + 
                    replacement + 
                    result_text[suggestion.end:]
                )
        
        return result_text

class LaTeXIntegration:
    """LaTeX editor integration with compilation support"""
    
    def __init__(self, latex_command: str = "pdflatex"):
        self.latex_command = latex_command
        self.supported_engines = ["pdflatex", "xelatex", "lualatex"]
        
    async def create_document(self, title: str, content: str, 
                            preamble: str = None) -> LaTeXDocument:
        """Create a new LaTeX document"""
        if preamble is None:
            preamble = self._get_default_preamble()
        
        doc_id = f"latex_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return LaTeXDocument(
            id=doc_id,
            title=title,
            content=content,
            preamble=preamble,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _get_default_preamble(self) -> str:
        """Get default LaTeX preamble"""
        return r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{geometry}
\geometry{margin=1in}

\title{Document Title}
\author{Author Name}
\date{\today}
"""
    
    async def compile_document(self, document: LaTeXDocument, 
                             output_dir: Optional[str] = None) -> CompilationResult:
        """Compile LaTeX document to PDF"""
        try:
            start_time = datetime.now()
            
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix='latex_compile_')
            
            # Create full LaTeX content
            full_content = self._build_full_document(document)
            
            # Write to temporary file
            tex_file = Path(output_dir) / f"{document.id}.tex"
            async with aiofiles.open(tex_file, 'w', encoding='utf-8') as f:
                await f.write(full_content)
            
            # Compile with LaTeX
            result = await self._run_latex_compilation(tex_file)
            
            end_time = datetime.now()
            compilation_time = int((end_time - start_time).total_seconds() * 1000)
            
            result.compilation_time_ms = compilation_time
            return result
            
        except Exception as e:
            logger.error(f"LaTeX compilation error: {e}")
            return CompilationResult(
                success=False,
                log_output=str(e),
                errors=[str(e)]
            )
    
    def _build_full_document(self, document: LaTeXDocument) -> str:
        """Build complete LaTeX document"""
        content_parts = [document.preamble]
        
        content_parts.append(r"\begin{document}")
        content_parts.append(r"\maketitle")
        content_parts.append("")
        content_parts.append(document.content)
        
        if document.bibliography:
            content_parts.append("")
            content_parts.append(r"\bibliography{references}")
            content_parts.append(r"\bibliographystyle{plain}")
        
        content_parts.append(r"\end{document}")
        
        return "\n".join(content_parts)
    
    async def _run_latex_compilation(self, tex_file: Path) -> CompilationResult:
        """Run LaTeX compilation process"""
        try:
            # Change to the directory containing the tex file
            work_dir = tex_file.parent
            tex_filename = tex_file.name
            
            # Run pdflatex
            process = await asyncio.create_subprocess_exec(
                self.latex_command,
                "-interaction=nonstopmode",
                "-output-directory", str(work_dir),
                tex_filename,
                cwd=work_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Check if PDF was created
            pdf_file = work_dir / f"{tex_file.stem}.pdf"
            success = pdf_file.exists()
            
            # Parse log for errors and warnings
            log_content = stdout.decode('utf-8', errors='ignore')
            errors, warnings = self._parse_latex_log(log_content)
            
            return CompilationResult(
                success=success,
                pdf_path=str(pdf_file) if success else None,
                log_output=log_content,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return CompilationResult(
                success=False,
                log_output=str(e),
                errors=[str(e)]
            )
    
    def _parse_latex_log(self, log_content: str) -> tuple[List[str], List[str]]:
        """Parse LaTeX log for errors and warnings"""
        errors = []
        warnings = []
        
        lines = log_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('!'):
                errors.append(line)
            elif 'Warning:' in line:
                warnings.append(line)
        
        return errors, warnings
    
    async def convert_to_format(self, document: LaTeXDocument, 
                              target_format: str) -> Optional[str]:
        """Convert LaTeX document to other formats"""
        try:
            if target_format.lower() == "markdown":
                return await self._latex_to_markdown(document)
            elif target_format.lower() == "html":
                return await self._latex_to_html(document)
            else:
                logger.warning(f"Unsupported conversion format: {target_format}")
                return None
                
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            return None
    
    async def _latex_to_markdown(self, document: LaTeXDocument) -> str:
        """Convert LaTeX to Markdown (simplified)"""
        content = document.content
        
        # Basic LaTeX to Markdown conversions
        conversions = [
            (r'\\section\{([^}]+)\}', r'# \1'),
            (r'\\subsection\{([^}]+)\}', r'## \1'),
            (r'\\subsubsection\{([^}]+)\}', r'### \1'),
            (r'\\textbf\{([^}]+)\}', r'**\1**'),
            (r'\\textit\{([^}]+)\}', r'*\1*'),
            (r'\\emph\{([^}]+)\}', r'*\1*'),
            (r'\\begin\{itemize\}', ''),
            (r'\\end\{itemize\}', ''),
            (r'\\item', '- '),
            (r'\\\\', '\n'),
        ]
        
        for pattern, replacement in conversions:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    async def _latex_to_html(self, document: LaTeXDocument) -> str:
        """Convert LaTeX to HTML (simplified)"""
        content = document.content
        
        # Basic LaTeX to HTML conversions
        conversions = [
            (r'\\section\{([^}]+)\}', r'<h1>\1</h1>'),
            (r'\\subsection\{([^}]+)\}', r'<h2>\1</h2>'),
            (r'\\subsubsection\{([^}]+)\}', r'<h3>\1</h3>'),
            (r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>'),
            (r'\\textit\{([^}]+)\}', r'<em>\1</em>'),
            (r'\\emph\{([^}]+)\}', r'<em>\1</em>'),
            (r'\\begin\{itemize\}', '<ul>'),
            (r'\\end\{itemize\}', '</ul>'),
            (r'\\item', '<li>'),
            (r'\\\\', '<br>'),
        ]
        
        for pattern, replacement in conversions:
            content = re.sub(pattern, replacement, content)
        
        return f"<html><body>{content}</body></html>"

class WritingToolsService:
    """Unified writing tools service"""
    
    def __init__(self, grammarly_api_key: Optional[str] = None):
        self.grammarly = GrammarlyIntegration(grammarly_api_key)
        self.latex = LaTeXIntegration()
        
    async def check_grammar(self, text: str, language: str = "en-US") -> GrammarCheckResult:
        """Check grammar and style"""
        return await self.grammarly.check_grammar(text, language)
    
    async def apply_grammar_suggestions(self, text: str, 
                                      suggestions: List[WritingSuggestion]) -> str:
        """Apply grammar suggestions to text"""
        return await self.grammarly.apply_suggestions(text, suggestions)
    
    async def create_latex_document(self, title: str, content: str, 
                                  preamble: str = None) -> LaTeXDocument:
        """Create LaTeX document"""
        return await self.latex.create_document(title, content, preamble)
    
    async def compile_latex(self, document: LaTeXDocument) -> CompilationResult:
        """Compile LaTeX document"""
        return await self.latex.compile_document(document)
    
    async def convert_document(self, document: LaTeXDocument, 
                             target_format: str) -> Optional[str]:
        """Convert document to different format"""
        return await self.latex.convert_to_format(document, target_format)
    
    async def collaborative_edit(self, document_id: str, 
                               changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle collaborative editing changes"""
        # Placeholder for collaborative editing functionality
        # In a real implementation, this would handle operational transforms
        # or conflict resolution for simultaneous edits
        
        return {
            "document_id": document_id,
            "changes_applied": len(changes),
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    async def export_to_platform(self, content: str, platform: str, 
                                credentials: Dict[str, Any]) -> bool:
        """Export document to external writing platform"""
        try:
            if platform.lower() == "google_docs":
                return await self._export_to_google_docs(content, credentials)
            elif platform.lower() == "microsoft_word":
                return await self._export_to_word_online(content, credentials)
            elif platform.lower() == "overleaf":
                return await self._export_to_overleaf(content, credentials)
            else:
                logger.warning(f"Unsupported export platform: {platform}")
                return False
                
        except Exception as e:
            logger.error(f"Export error to {platform}: {e}")
            return False
    
    async def _export_to_google_docs(self, content: str, 
                                   credentials: Dict[str, Any]) -> bool:
        """Export to Google Docs (placeholder)"""
        # This would use Google Docs API
        logger.info("Google Docs export (placeholder implementation)")
        return True
    
    async def _export_to_word_online(self, content: str, 
                                   credentials: Dict[str, Any]) -> bool:
        """Export to Microsoft Word Online (placeholder)"""
        # This would use Microsoft Graph API
        logger.info("Word Online export (placeholder implementation)")
        return True
    
    async def _export_to_overleaf(self, content: str, 
                                credentials: Dict[str, Any]) -> bool:
        """Export to Overleaf (placeholder)"""
        # This would use Overleaf API if available
        logger.info("Overleaf export (placeholder implementation)")
        return True
    
    def get_supported_tools(self) -> List[str]:
        """Get list of supported writing tools"""
        return [tool.value for tool in WritingTool]
    
    def get_supported_export_platforms(self) -> List[str]:
        """Get list of supported export platforms"""
        return ["google_docs", "microsoft_word", "overleaf", "markdown", "html", "pdf"]
    
    async def analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """Analyze writing style and provide insights"""
        try:
            # Basic writing analysis
            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            paragraphs = text.split('\n\n')
            
            # Calculate metrics
            word_count = len(words)
            sentence_count = len([s for s in sentences if s.strip()])
            paragraph_count = len([p for p in paragraphs if p.strip()])
            
            avg_words_per_sentence = word_count / max(sentence_count, 1)
            avg_sentences_per_paragraph = sentence_count / max(paragraph_count, 1)
            
            # Readability score
            readability = self.grammarly._calculate_readability(text)
            
            return {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_words_per_sentence": round(avg_words_per_sentence, 1),
                "avg_sentences_per_paragraph": round(avg_sentences_per_paragraph, 1),
                "readability_score": round(readability, 1),
                "readability_level": self._get_readability_level(readability),
                "estimated_reading_time_minutes": max(1, word_count // 200)
            }
            
        except Exception as e:
            logger.error(f"Writing analysis error: {e}")
            return {"error": str(e)}
    
    def _get_readability_level(self, score: float) -> str:
        """Get readability level description"""
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"