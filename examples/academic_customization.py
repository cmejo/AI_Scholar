#!/usr/bin/env python3
"""
Academic Customization Example
Demonstrates how to customize the AI Scholar Chatbot for academic use
"""

from flask import Blueprint, request, jsonify
from services.chat_service import chat_service
from services.ollama_service import ollama_service

# Academic-specific blueprint
academic_bp = Blueprint('academic', __name__)

# Academic system prompts
ACADEMIC_PROMPTS = {
    "research_assistant": """
    You are Dr. Scholar, an AI research assistant with expertise across multiple academic disciplines.
    
    Your role:
    - Provide scholarly, well-researched responses
    - Include citations and references when possible
    - Suggest related research areas and papers
    - Help with research methodology and analysis
    - Maintain academic rigor and objectivity
    
    Guidelines:
    - Always fact-check information
    - Acknowledge limitations and uncertainties
    - Encourage critical thinking
    - Use appropriate academic language
    - Provide structured, logical responses
    """,
    
    "tutor": """
    You are Professor AI, a patient and knowledgeable tutor.
    
    Your teaching approach:
    - Break down complex concepts into understandable parts
    - Use examples and analogies to illustrate points
    - Ask questions to check understanding
    - Provide step-by-step explanations
    - Encourage active learning and curiosity
    
    Communication style:
    - Supportive and encouraging
    - Clear and concise
    - Adaptive to student's level
    - Socratic questioning when appropriate
    """,
    
    "writing_assistant": """
    You are Dr. Write, an academic writing specialist.
    
    Your expertise:
    - Academic writing structure and style
    - Citation formats (APA, MLA, Chicago, etc.)
    - Research paper organization
    - Thesis development and argumentation
    - Grammar and clarity improvement
    
    Approach:
    - Provide constructive feedback
    - Suggest specific improvements
    - Explain writing principles
    - Help with academic conventions
    """
}

# Academic model configurations
ACADEMIC_MODELS = {
    "research": {
        "model": "llama2:13b-chat",
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 2048,
        "system_prompt": ACADEMIC_PROMPTS["research_assistant"]
    },
    "tutoring": {
        "model": "llama2:7b-chat",
        "temperature": 0.5,
        "top_p": 0.9,
        "max_tokens": 1500,
        "system_prompt": ACADEMIC_PROMPTS["tutor"]
    },
    "writing": {
        "model": "mistral:7b-instruct",
        "temperature": 0.4,
        "top_p": 0.9,
        "max_tokens": 2000,
        "system_prompt": ACADEMIC_PROMPTS["writing_assistant"]
    }
}

class AcademicService:
    """Service for academic-specific functionality"""
    
    def __init__(self):
        self.citation_formats = {
            "apa": self._format_apa,
            "mla": self._format_mla,
            "chicago": self._format_chicago
        }
    
    def generate_citation(self, source_info: dict, format_type: str = "apa") -> str:
        """Generate academic citation"""
        if format_type in self.citation_formats:
            return self.citation_formats[format_type](source_info)
        return self._format_apa(source_info)  # Default to APA
    
    def _format_apa(self, source: dict) -> str:
        """Format citation in APA style"""
        authors = source.get('authors', ['Unknown'])
        year = source.get('year', 'n.d.')
        title = source.get('title', 'Untitled')
        journal = source.get('journal', '')
        
        author_str = ', '.join(authors[:3])  # Limit to 3 authors
        if len(authors) > 3:
            author_str += ', et al.'
        
        citation = f"{author_str} ({year}). {title}."
        if journal:
            citation += f" {journal}."
        
        return citation
    
    def _format_mla(self, source: dict) -> str:
        """Format citation in MLA style"""
        authors = source.get('authors', ['Unknown'])
        title = source.get('title', 'Untitled')
        journal = source.get('journal', '')
        year = source.get('year', '')
        
        author_str = authors[0] if authors else 'Unknown'
        citation = f'{author_str}. "{title}."'
        if journal:
            citation += f" {journal},"
        if year:
            citation += f" {year}."
        
        return citation
    
    def _format_chicago(self, source: dict) -> str:
        """Format citation in Chicago style"""
        # Simplified Chicago format
        authors = source.get('authors', ['Unknown'])
        title = source.get('title', 'Untitled')
        journal = source.get('journal', '')
        year = source.get('year', '')
        
        author_str = authors[0] if authors else 'Unknown'
        citation = f'{author_str}. "{title}."'
        if journal:
            citation += f" {journal}"
        if year:
            citation += f" ({year})."
        
        return citation
    
    def extract_key_concepts(self, text: str) -> list:
        """Extract key academic concepts from text"""
        # This would use NLP to extract key terms
        # For now, a simple implementation
        import re
        
        # Look for capitalized terms, technical terms, etc.
        concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'Or', 'But'}
        concepts = [c for c in concepts if c not in common_words]
        
        return list(set(concepts))  # Remove duplicates
    
    def suggest_research_questions(self, topic: str) -> list:
        """Suggest research questions for a topic"""
        question_templates = [
            f"What are the current trends in {topic}?",
            f"How has {topic} evolved over the past decade?",
            f"What are the main challenges in {topic}?",
            f"What methodologies are commonly used to study {topic}?",
            f"What are the ethical implications of {topic}?",
            f"How does {topic} relate to other fields of study?",
            f"What are the practical applications of {topic}?",
            f"What gaps exist in current {topic} research?"
        ]
        return question_templates

# Academic API endpoints
@academic_bp.route('/api/academic/research-chat', methods=['POST'])
def research_chat():
    """Chat endpoint optimized for research assistance"""
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id')
    
    # Use research-optimized model configuration
    config = ACADEMIC_MODELS["research"]
    
    # Generate response with academic context
    try:
        for response in chat_service.generate_response(
            session_id=session_id,
            user_id=1,  # Would get from auth
            message=message,
            model=config["model"],
            parameters={
                "temperature": config["temperature"],
                "top_p": config["top_p"],
                "max_tokens": config["max_tokens"]
            },
            stream=False
        ):
            if response.is_complete:
                return jsonify({
                    "success": True,
                    "response": response.content,
                    "model": config["model"],
                    "type": "research_response"
                })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@academic_bp.route('/api/academic/generate-citation', methods=['POST'])
def generate_citation():
    """Generate academic citation"""
    data = request.get_json()
    source_info = data.get('source', {})
    format_type = data.get('format', 'apa')
    
    academic_service = AcademicService()
    citation = academic_service.generate_citation(source_info, format_type)
    
    return jsonify({
        "citation": citation,
        "format": format_type
    })

@academic_bp.route('/api/academic/extract-concepts', methods=['POST'])
def extract_concepts():
    """Extract key concepts from academic text"""
    data = request.get_json()
    text = data.get('text', '')
    
    academic_service = AcademicService()
    concepts = academic_service.extract_key_concepts(text)
    
    return jsonify({
        "concepts": concepts,
        "count": len(concepts)
    })

@academic_bp.route('/api/academic/research-questions', methods=['POST'])
def suggest_research_questions():
    """Suggest research questions for a topic"""
    data = request.get_json()
    topic = data.get('topic', '')
    
    academic_service = AcademicService()
    questions = academic_service.suggest_research_questions(topic)
    
    return jsonify({
        "topic": topic,
        "questions": questions
    })

@academic_bp.route('/api/academic/paper-analysis', methods=['POST'])
def analyze_paper():
    """Analyze an academic paper"""
    data = request.get_json()
    paper_text = data.get('text', '')
    analysis_type = data.get('type', 'summary')
    
    # Use research model for analysis
    config = ACADEMIC_MODELS["research"]
    
    prompts = {
        "summary": f"Please provide a comprehensive summary of this academic paper:\n\n{paper_text}",
        "methodology": f"Analyze the methodology used in this paper:\n\n{paper_text}",
        "critique": f"Provide a constructive critique of this paper:\n\n{paper_text}",
        "questions": f"Generate discussion questions based on this paper:\n\n{paper_text}"
    }
    
    prompt = prompts.get(analysis_type, prompts["summary"])
    
    try:
        # Generate analysis using Ollama
        result = ollama_service.generate_response(
            model=config["model"],
            prompt=prompt,
            stream=False
        )
        
        return jsonify({
            "analysis": result.get("response", ""),
            "type": analysis_type,
            "model": config["model"]
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# Example usage function
def setup_academic_customization(app):
    """Set up academic customization for the app"""
    
    # Register academic blueprint
    app.register_blueprint(academic_bp)
    
    # Set academic-specific configuration
    app.config.update({
        'ACADEMIC_MODE': True,
        'DEFAULT_SYSTEM_PROMPT': ACADEMIC_PROMPTS["research_assistant"],
        'CITATION_ENABLED': True,
        'RESEARCH_FEATURES': True
    })
    
    print("✅ Academic customization enabled")
    print("📚 Available endpoints:")
    print("  - /api/academic/research-chat")
    print("  - /api/academic/generate-citation")
    print("  - /api/academic/extract-concepts")
    print("  - /api/academic/research-questions")
    print("  - /api/academic/paper-analysis")

if __name__ == "__main__":
    # Example of how to test academic features
    academic_service = AcademicService()
    
    # Test citation generation
    sample_source = {
        "authors": ["Smith, J.", "Doe, A."],
        "year": "2023",
        "title": "Machine Learning in Education",
        "journal": "Journal of Educational Technology"
    }
    
    print("Sample APA Citation:")
    print(academic_service.generate_citation(sample_source, "apa"))
    
    # Test concept extraction
    sample_text = "Machine Learning and Artificial Intelligence are transforming Educational Technology."
    concepts = academic_service.extract_key_concepts(sample_text)
    print(f"\nExtracted concepts: {concepts}")
    
    # Test research questions
    questions = academic_service.suggest_research_questions("machine learning")
    print(f"\nSample research questions:")
    for q in questions[:3]:
        print(f"  - {q}")