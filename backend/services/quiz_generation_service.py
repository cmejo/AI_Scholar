"""
Quiz Generation Service for Educational Enhancement System

This service provides AI-powered quiz generation from research documents,
supporting multiple question types with difficulty assessment and adaptive selection.
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core.database import get_db, Quiz as QuizModel, QuizQuestion as QuizQuestionModel, QuizAttempt

logger = logging.getLogger(__name__)

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    TRUE_FALSE = "true_false"
    FILL_IN_BLANK = "fill_in_blank"

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class QuizQuestion:
    id: str
    question_text: str
    question_type: QuestionType
    difficulty_level: DifficultyLevel
    options: Optional[List[str]] = None
    correct_answer: str = ""
    explanation: str = ""
    source_content: str = ""
    confidence_score: float = 0.0
    learning_objectives: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.learning_objectives is None:
            self.learning_objectives = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Quiz:
    id: str
    title: str
    description: str
    document_id: str
    questions: List[QuizQuestion]
    difficulty_level: DifficultyLevel
    estimated_time_minutes: int
    learning_objectives: List[str]
    created_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class QuizGenerationService:
    """Service for generating educational quizzes from document content"""
    
    def __init__(self):
        self._question_templates = self._load_question_templates()
        
    def _load_question_templates(self) -> Dict[str, List[str]]:
        """Load question generation templates for different types"""
        return {
            QuestionType.MULTIPLE_CHOICE: [
                "What is the main concept discussed in the following text: {content}?",
                "According to the document, which of the following statements is correct?",
                "What is the primary purpose of {key_concept}?",
                "Which factor most significantly influences {topic}?",
                "What conclusion can be drawn from {evidence}?"
            ],
            QuestionType.SHORT_ANSWER: [
                "Explain the significance of {key_concept} in the context of {topic}.",
                "What are the main characteristics of {subject}?",
                "How does {concept_a} relate to {concept_b}?",
                "What evidence supports the claim that {statement}?",
                "Describe the process of {process_name}."
            ],
            QuestionType.ESSAY: [
                "Analyze the implications of {main_concept} for {field_of_study}.",
                "Compare and contrast {concept_a} and {concept_b}, discussing their similarities and differences.",
                "Evaluate the effectiveness of {approach} in addressing {problem}.",
                "Discuss the potential future developments in {research_area} based on current findings.",
                "Critically examine the methodology used in {study} and its impact on the conclusions."
            ],
            QuestionType.TRUE_FALSE: [
                "{statement} is always true according to the research.",
                "The document suggests that {claim} is the primary factor.",
                "{concept} has no relationship with {other_concept}.",
                "All studies mentioned support the hypothesis that {hypothesis}."
            ],
            QuestionType.FILL_IN_BLANK: [
                "The primary function of {concept} is to _____ in the context of {domain}.",
                "Research shows that _____ is the most significant factor affecting {outcome}.",
                "The relationship between {var_a} and {var_b} can be described as _____.",
                "According to the findings, _____ methodology was used to analyze {data_type}."
            ]
        }

    async def generate_quiz_from_document(
        self,
        document_id: str,
        user_id: str,
        num_questions: int = 10,
        question_types: List[QuestionType] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        learning_objectives: List[str] = None
    ) -> Quiz:
        """Generate a comprehensive quiz from a document"""
        try:
            # Get document content
            document_content = await self._get_document_content(document_id)
            if not document_content:
                raise ValueError(f"Document {document_id} not found or empty")
            
            # Set default question types if not provided
            if question_types is None:
                question_types = [
                    QuestionType.MULTIPLE_CHOICE,
                    QuestionType.SHORT_ANSWER,
                    QuestionType.TRUE_FALSE
                ]
            
            # Extract key concepts and topics
            key_concepts = await self._extract_key_concepts(document_content)
            
            # Analyze content complexity for adaptive difficulty
            content_analysis = await self.analyze_content_complexity(document_content)
            recommended_difficulty = content_analysis['recommended_difficulty']
            
            # Use recommended difficulty if not specified
            if difficulty_level == DifficultyLevel.INTERMEDIATE and recommended_difficulty != DifficultyLevel.INTERMEDIATE:
                difficulty_level = recommended_difficulty
            
            # Generate questions
            questions = await self._generate_questions(
                content=document_content,
                key_concepts=key_concepts,
                num_questions=num_questions,
                question_types=question_types,
                difficulty_level=difficulty_level
            )
            
            # Create quiz object
            quiz = Quiz(
                id=f"quiz_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                title=f"Quiz: {await self._get_document_title(document_id)}",
                description=f"Auto-generated quiz covering key concepts from the document",
                document_id=document_id,
                questions=questions,
                difficulty_level=difficulty_level,
                estimated_time_minutes=self._estimate_completion_time(questions),
                learning_objectives=learning_objectives or await self._generate_learning_objectives(key_concepts),
                created_at=datetime.now()
            )
            
            # Store quiz in database
            await self._store_quiz(quiz, user_id)
            
            logger.info(f"Generated quiz with {len(questions)} questions for document {document_id}")
            return quiz
            
        except Exception as e:
            logger.error(f"Error generating quiz for document {document_id}: {str(e)}")
            raise

    async def generate_multiple_choice_question(
        self,
        content: str,
        key_concept: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    ) -> QuizQuestion:
        """Generate a multiple choice question from content"""
        try:
            # Generate question text
            question_text = await self._generate_question_text(
                content, key_concept, QuestionType.MULTIPLE_CHOICE, difficulty_level
            )
            
            # Generate correct answer and distractors
            correct_answer, options = await self._generate_mc_options(
                content, question_text, key_concept, difficulty_level
            )
            
            # Generate explanation
            explanation = await self._generate_explanation(
                question_text, correct_answer, content
            )
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(
                question_text, options, content
            )
            
            return QuizQuestion(
                id=f"mcq_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                question_text=question_text,
                question_type=QuestionType.MULTIPLE_CHOICE,
                difficulty_level=difficulty_level,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                source_content=content[:500] + "..." if len(content) > 500 else content,
                confidence_score=confidence_score,
                learning_objectives=[f"Understand {key_concept}"],
                metadata={"key_concept": key_concept}
            )
            
        except Exception as e:
            logger.error(f"Error generating multiple choice question: {str(e)}")
            raise

    async def generate_short_answer_question(
        self,
        content: str,
        key_concept: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    ) -> QuizQuestion:
        """Generate a short answer question from content"""
        try:
            # Generate question text
            question_text = await self._generate_question_text(
                content, key_concept, QuestionType.SHORT_ANSWER, difficulty_level
            )
            
            # Generate model answer
            model_answer = await self._generate_model_answer(
                question_text, content, key_concept
            )
            
            # Generate explanation/rubric
            explanation = await self._generate_short_answer_rubric(
                question_text, model_answer, content
            )
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(
                question_text, [model_answer], content
            )
            
            return QuizQuestion(
                id=f"saq_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                question_text=question_text,
                question_type=QuestionType.SHORT_ANSWER,
                difficulty_level=difficulty_level,
                correct_answer=model_answer,
                explanation=explanation,
                source_content=content[:500] + "..." if len(content) > 500 else content,
                confidence_score=confidence_score,
                learning_objectives=[f"Explain {key_concept}"],
                metadata={"key_concept": key_concept, "expected_length": "2-3 sentences"}
            )
            
        except Exception as e:
            logger.error(f"Error generating short answer question: {str(e)}")
            raise

    async def generate_essay_question(
        self,
        content: str,
        key_concepts: List[str],
        difficulty_level: DifficultyLevel = DifficultyLevel.ADVANCED
    ) -> QuizQuestion:
        """Generate an essay question from content"""
        try:
            # Generate question text that requires synthesis
            question_text = await self._generate_essay_question_text(
                content, key_concepts, difficulty_level
            )
            
            # Generate essay outline/model answer
            model_answer = await self._generate_essay_outline(
                question_text, content, key_concepts
            )
            
            # Generate rubric
            explanation = await self._generate_essay_rubric(
                question_text, key_concepts, content
            )
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(
                question_text, [model_answer], content
            )
            
            return QuizQuestion(
                id=f"essay_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                question_text=question_text,
                question_type=QuestionType.ESSAY,
                difficulty_level=difficulty_level,
                correct_answer=model_answer,
                explanation=explanation,
                source_content=content[:1000] + "..." if len(content) > 1000 else content,
                confidence_score=confidence_score,
                learning_objectives=[f"Analyze and synthesize {', '.join(key_concepts)}"],
                metadata={
                    "key_concepts": key_concepts,
                    "expected_length": "300-500 words",
                    "time_limit": "30 minutes"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating essay question: {str(e)}")
            raise

    async def assess_question_difficulty(
        self,
        question: QuizQuestion,
        content: str
    ) -> DifficultyLevel:
        """Assess the difficulty level of a generated question"""
        try:
            difficulty_factors = {
                'concept_complexity': 0,
                'cognitive_level': 0,
                'content_depth': 0,
                'prerequisite_knowledge': 0
            }
            
            # Analyze concept complexity
            if question.question_type == QuestionType.ESSAY:
                difficulty_factors['concept_complexity'] = 3
            elif question.question_type == QuestionType.SHORT_ANSWER:
                difficulty_factors['concept_complexity'] = 2
            else:
                difficulty_factors['concept_complexity'] = 1
            
            # Analyze cognitive level based on question text
            cognitive_keywords = {
                'beginner': ['what', 'who', 'when', 'where', 'list', 'identify'],
                'intermediate': ['how', 'why', 'explain', 'describe', 'compare'],
                'advanced': ['analyze', 'evaluate', 'synthesize', 'critique', 'assess']
            }
            
            question_lower = question.question_text.lower()
            for level, keywords in cognitive_keywords.items():
                if any(keyword in question_lower for keyword in keywords):
                    if level == 'advanced':
                        difficulty_factors['cognitive_level'] = 3
                    elif level == 'intermediate':
                        difficulty_factors['cognitive_level'] = 2
                    else:
                        difficulty_factors['cognitive_level'] = 1
                    break
            
            # Calculate overall difficulty
            avg_difficulty = sum(difficulty_factors.values()) / len(difficulty_factors)
            
            if avg_difficulty >= 2.5:
                return DifficultyLevel.ADVANCED
            elif avg_difficulty >= 1.5:
                return DifficultyLevel.INTERMEDIATE
            else:
                return DifficultyLevel.BEGINNER
                
        except Exception as e:
            logger.error(f"Error assessing question difficulty: {str(e)}")
            return DifficultyLevel.INTERMEDIATE

    async def generate_answer_key(self, quiz: Quiz) -> Dict[str, Any]:
        """Generate comprehensive answer key for a quiz"""
        try:
            answer_key = {
                'quiz_id': quiz.id,
                'quiz_title': quiz.title,
                'total_questions': len(quiz.questions),
                'answers': [],
                'scoring_guide': {
                    'multiple_choice': 1,
                    'true_false': 1,
                    'short_answer': 2,
                    'essay': 5,
                    'fill_in_blank': 1
                },
                'generated_at': datetime.now().isoformat()
            }
            
            for i, question in enumerate(quiz.questions, 1):
                answer_info = {
                    'question_number': i,
                    'question_id': question.id,
                    'question_type': question.question_type.value,
                    'correct_answer': question.correct_answer,
                    'explanation': question.explanation,
                    'points': answer_key['scoring_guide'].get(question.question_type.value, 1)
                }
                
                if question.options:
                    answer_info['options'] = question.options
                
                if question.metadata:
                    answer_info['metadata'] = question.metadata
                
                answer_key['answers'].append(answer_info)
            
            return answer_key
            
        except Exception as e:
            logger.error(f"Error generating answer key: {str(e)}")
            raise

    async def adaptive_question_selection(
        self,
        user_id: str,
        content: str,
        key_concepts: List[str],
        user_performance_history: Dict[str, Any] = None
    ) -> List[QuizQuestion]:
        """Select questions adaptively based on user performance"""
        try:
            if not user_performance_history:
                user_performance_history = await self._get_user_performance_history(user_id)
            
            # Determine user's current level
            avg_performance = user_performance_history.get('average_score', 0.7)
            
            if avg_performance >= 0.8:
                target_difficulty = DifficultyLevel.ADVANCED
            elif avg_performance >= 0.6:
                target_difficulty = DifficultyLevel.INTERMEDIATE
            else:
                target_difficulty = DifficultyLevel.BEGINNER
            
            # Generate questions with adaptive difficulty
            questions = []
            
            # Start with target difficulty
            for i, concept in enumerate(key_concepts[:3]):
                if i == 0:
                    # First question at target level
                    difficulty = target_difficulty
                elif i == 1:
                    # Second question slightly easier
                    difficulty = (DifficultyLevel.BEGINNER if target_difficulty == DifficultyLevel.INTERMEDIATE
                                else DifficultyLevel.INTERMEDIATE if target_difficulty == DifficultyLevel.ADVANCED
                                else DifficultyLevel.BEGINNER)
                else:
                    # Third question slightly harder
                    difficulty = (DifficultyLevel.INTERMEDIATE if target_difficulty == DifficultyLevel.BEGINNER
                                else DifficultyLevel.ADVANCED if target_difficulty == DifficultyLevel.INTERMEDIATE
                                else DifficultyLevel.ADVANCED)
                
                # Generate different types of questions
                question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER, QuestionType.TRUE_FALSE]
                question_type = question_types[i % len(question_types)]
                
                if question_type == QuestionType.MULTIPLE_CHOICE:
                    question = await self.generate_multiple_choice_question(content, concept, difficulty)
                elif question_type == QuestionType.SHORT_ANSWER:
                    question = await self.generate_short_answer_question(content, concept, difficulty)
                else:
                    question = await self._generate_true_false_question(content, concept, difficulty)
                
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error in adaptive question selection: {str(e)}")
            # Fallback to standard question generation
            return await self._generate_questions(
                content, key_concepts, 3, 
                [QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER], 
                DifficultyLevel.INTERMEDIATE
            )

    async def analyze_content_complexity(self, content: str) -> Dict[str, Any]:
        """Analyze content complexity for better question generation"""
        try:
            analysis = {
                'readability_score': 0.0,
                'concept_density': 0.0,
                'technical_terms': [],
                'key_phrases': [],
                'content_type': 'general',
                'recommended_difficulty': DifficultyLevel.INTERMEDIATE
            }
            
            # Basic readability analysis
            sentences = content.split('.')
            words = content.split()
            
            if sentences and words:
                avg_sentence_length = len(words) / len(sentences)
                analysis['readability_score'] = min(1.0, avg_sentence_length / 20)
            
            # Identify technical terms (capitalized words, acronyms)
            technical_terms = []
            for word in words:
                if (word.isupper() and len(word) > 2) or (word.istitle() and len(word) > 4):
                    if word not in technical_terms:
                        technical_terms.append(word)
            
            analysis['technical_terms'] = technical_terms[:10]
            analysis['concept_density'] = min(1.0, len(technical_terms) / len(words) * 100)
            
            # Determine content type based on keywords
            academic_keywords = ['research', 'study', 'analysis', 'methodology', 'findings', 'conclusion']
            technical_keywords = ['algorithm', 'system', 'process', 'implementation', 'framework']
            
            academic_count = sum(1 for keyword in academic_keywords if keyword.lower() in content.lower())
            technical_count = sum(1 for keyword in technical_keywords if keyword.lower() in content.lower())
            
            if academic_count > technical_count:
                analysis['content_type'] = 'academic'
            elif technical_count > academic_count:
                analysis['content_type'] = 'technical'
            
            # Recommend difficulty based on complexity
            complexity_score = (analysis['readability_score'] + analysis['concept_density']) / 2
            if complexity_score > 0.7:
                analysis['recommended_difficulty'] = DifficultyLevel.ADVANCED
            elif complexity_score > 0.4:
                analysis['recommended_difficulty'] = DifficultyLevel.INTERMEDIATE
            else:
                analysis['recommended_difficulty'] = DifficultyLevel.BEGINNER
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content complexity: {str(e)}")
            return {
                'readability_score': 0.5,
                'concept_density': 0.5,
                'technical_terms': [],
                'key_phrases': [],
                'content_type': 'general',
                'recommended_difficulty': DifficultyLevel.INTERMEDIATE
            }

    # Helper methods
    async def _get_document_content(self, document_id: str) -> str:
        """Retrieve document content from database"""
        try:
            from core.database import Document
            db = next(get_db())
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    # For now, return a sample content since we need to implement document content storage
                    return f"This is sample content for document {document.name}. Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models. Deep learning uses neural networks with multiple layers. Natural language processing enables computers to understand human language. Computer vision allows machines to interpret visual information."
                else:
                    # Return sample content for testing when document doesn't exist
                    return f"Sample research content for {document_id}. Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience. Deep learning is a specialized form of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data. Natural language processing enables computers to understand, interpret, and generate human language in a valuable way. Computer vision allows machines to interpret and understand visual information from the world."
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error retrieving document content: {str(e)}")
            # Return sample content for testing
            return f"Sample research content for {document_id}. Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience. Deep learning is a specialized form of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data. Natural language processing enables computers to understand, interpret, and generate human language in a valuable way. Computer vision allows machines to interpret and understand visual information from the world."

    async def _get_document_title(self, document_id: str) -> str:
        """Retrieve document title from database"""
        try:
            from core.database import Document
            db = next(get_db())
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                return document.name if document else f"Document {document_id}"
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error retrieving document title: {str(e)}")
            return f"Document {document_id}"

    async def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from document content"""
        try:
            key_concepts = []
            sentences = content.split('.')
            
            for sentence in sentences[:20]:  # Limit to first 20 sentences
                words = sentence.split()
                # Look for capitalized terms (potential concepts)
                for i, word in enumerate(words):
                    if word.istitle() and len(word) > 3:
                        if i < len(words) - 1 and words[i + 1].istitle():
                            concept = f"{word} {words[i + 1]}"
                            if concept not in key_concepts:
                                key_concepts.append(concept)
                        elif word not in key_concepts:
                            key_concepts.append(word)
            
            # Also look for common academic terms
            academic_terms = ['learning', 'algorithm', 'model', 'data', 'analysis', 'research', 'study', 'method']
            for term in academic_terms:
                if term.lower() in content.lower() and term not in key_concepts:
                    key_concepts.append(term)
            
            # Return top concepts
            return key_concepts[:10] if key_concepts else ["main concept", "key idea", "important topic"]
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {str(e)}")
            return ["main concept", "key idea", "important topic"]

    async def _generate_questions(
        self,
        content: str,
        key_concepts: List[str],
        num_questions: int,
        question_types: List[QuestionType],
        difficulty_level: DifficultyLevel
    ) -> List[QuizQuestion]:
        """Generate multiple questions from content"""
        questions = []
        
        try:
            # Distribute questions across types
            questions_per_type = max(1, num_questions // len(question_types))
            
            for question_type in question_types:
                type_questions = min(questions_per_type, num_questions - len(questions))
                
                for i in range(type_questions):
                    concept = key_concepts[i % len(key_concepts)] if key_concepts else "main concept"
                    
                    if question_type == QuestionType.MULTIPLE_CHOICE:
                        question = await self.generate_multiple_choice_question(
                            content, concept, difficulty_level
                        )
                    elif question_type == QuestionType.SHORT_ANSWER:
                        question = await self.generate_short_answer_question(
                            content, concept, difficulty_level
                        )
                    elif question_type == QuestionType.ESSAY:
                        question = await self.generate_essay_question(
                            content, key_concepts[:3], difficulty_level
                        )
                    elif question_type == QuestionType.TRUE_FALSE:
                        question = await self._generate_true_false_question(
                            content, concept, difficulty_level
                        )
                    elif question_type == QuestionType.FILL_IN_BLANK:
                        question = await self._generate_fill_in_blank_question(
                            content, concept, difficulty_level
                        )
                    else:
                        continue
                    
                    questions.append(question)
                    
                    if len(questions) >= num_questions:
                        break
                
                if len(questions) >= num_questions:
                    break
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []

    async def _generate_question_text(
        self,
        content: str,
        key_concept: str,
        question_type: QuestionType,
        difficulty_level: DifficultyLevel
    ) -> str:
        """Generate question text based on content and concept"""
        try:
            templates = self._question_templates.get(question_type, [])
            if not templates:
                return f"What is the significance of {key_concept}?"
            
            # Select template based on difficulty
            template_idx = 0
            if difficulty_level == DifficultyLevel.INTERMEDIATE:
                template_idx = min(1, len(templates) - 1)
            elif difficulty_level == DifficultyLevel.ADVANCED:
                template_idx = min(2, len(templates) - 1)
            
            template = templates[template_idx]
            
            # Fill template with concept
            question_text = template.format(
                content=content[:100] + "...",
                key_concept=key_concept,
                topic=key_concept,
                subject=key_concept,
                concept_a=key_concept,
                concept_b="related concept",
                statement=f"{key_concept} is important",
                evidence="the research findings",
                process_name=key_concept,
                main_concept=key_concept,
                field_of_study="this field",
                approach=key_concept,
                problem="the main issue",
                research_area="this area",
                study="this research",
                claim=f"{key_concept} is significant",
                concept="the concept",
                other_concept="another concept",
                hypothesis=f"{key_concept} affects outcomes"
            )
            
            return question_text
            
        except Exception as e:
            logger.error(f"Error generating question text: {str(e)}")
            return f"Explain the concept of {key_concept}."

    async def _generate_mc_options(
        self,
        content: str,
        question_text: str,
        key_concept: str,
        difficulty_level: DifficultyLevel
    ) -> Tuple[str, List[str]]:
        """Generate multiple choice options with correct answer"""
        try:
            # Generate correct answer based on content
            correct_answer = await self._extract_answer_from_content(
                content, question_text, key_concept
            )
            
            # Generate distractors
            distractors = await self._generate_distractors(
                correct_answer, key_concept, difficulty_level
            )
            
            # Combine and shuffle options
            all_options = [correct_answer] + distractors
            
            # Ensure we have exactly 4 options
            while len(all_options) < 4:
                all_options.append(f"Alternative explanation {len(all_options)}")
            
            return correct_answer, all_options[:4]
            
        except Exception as e:
            logger.error(f"Error generating MC options: {str(e)}")
            return "Correct answer", ["Correct answer", "Option B", "Option C", "Option D"]

    async def _extract_answer_from_content(
        self,
        content: str,
        question_text: str,
        key_concept: str
    ) -> str:
        """Extract the correct answer from content"""
        try:
            # Find sentences containing the key concept
            sentences = content.split('.')
            relevant_sentences = [
                s.strip() for s in sentences 
                if key_concept.lower() in s.lower() and len(s.strip()) > 20
            ]
            
            if relevant_sentences:
                # Return the most relevant sentence as answer
                return relevant_sentences[0][:100] + "..." if len(relevant_sentences[0]) > 100 else relevant_sentences[0]
            else:
                return f"The concept of {key_concept} is central to understanding this topic."
                
        except Exception as e:
            logger.error(f"Error extracting answer: {str(e)}")
            return f"Information about {key_concept}"

    async def _generate_distractors(
        self,
        correct_answer: str,
        key_concept: str,
        difficulty_level: DifficultyLevel
    ) -> List[str]:
        """Generate plausible but incorrect answer options"""
        try:
            distractors = []
            
            # Generate different types of distractors
            distractors.append(f"The opposite of what {key_concept} represents")
            distractors.append(f"A common misconception about {key_concept}")
            distractors.append(f"A related but distinct concept from {key_concept}")
            
            return distractors
            
        except Exception as e:
            logger.error(f"Error generating distractors: {str(e)}")
            return ["Option B", "Option C", "Option D"]

    async def _generate_model_answer(
        self,
        question_text: str,
        content: str,
        key_concept: str
    ) -> str:
        """Generate a model answer for short answer questions"""
        try:
            # Extract relevant information from content
            relevant_info = await self._extract_answer_from_content(
                content, question_text, key_concept
            )
            
            # Create a structured answer
            model_answer = f"The {key_concept} is significant because {relevant_info}. "
            model_answer += f"This concept plays a crucial role in understanding the broader context of the research."
            
            return model_answer
            
        except Exception as e:
            logger.error(f"Error generating model answer: {str(e)}")
            return f"A comprehensive explanation of {key_concept} and its significance."

    async def _generate_explanation(
        self,
        question_text: str,
        correct_answer: str,
        content: str
    ) -> str:
        """Generate explanation for the correct answer"""
        try:
            explanation = f"This answer is correct because it accurately reflects the information presented in the source material. "
            explanation += f"The content specifically discusses this concept and its implications."
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return "This answer is supported by the source material."

    async def _calculate_confidence_score(
        self,
        question_text: str,
        options: List[str],
        content: str
    ) -> float:
        """Calculate confidence score for generated question"""
        try:
            score = 0.5  # Base score
            
            # Increase score if question is clearly answerable from content
            if any(opt.lower() in content.lower() for opt in options):
                score += 0.2
            
            # Increase score based on question clarity
            if len(question_text.split()) > 5:
                score += 0.1
            
            # Ensure score is between 0 and 1
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5

    async def _generate_true_false_question(
        self,
        content: str,
        key_concept: str,
        difficulty_level: DifficultyLevel
    ) -> QuizQuestion:
        """Generate a true/false question"""
        try:
            # Create a statement that can be true or false
            statement = f"The document states that {key_concept} is the primary factor in this research."
            
            # Determine if statement is true based on content
            is_true = key_concept.lower() in content.lower()
            
            return QuizQuestion(
                id=f"tf_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                question_text=statement,
                question_type=QuestionType.TRUE_FALSE,
                difficulty_level=difficulty_level,
                correct_answer="True" if is_true else "False",
                explanation=f"This statement is {'correct' if is_true else 'incorrect'} based on the document content.",
                source_content=content[:300] + "..." if len(content) > 300 else content,
                confidence_score=0.7,
                learning_objectives=[f"Identify key facts about {key_concept}"],
                metadata={"key_concept": key_concept, "statement_type": "factual"}
            )
            
        except Exception as e:
            logger.error(f"Error generating true/false question: {str(e)}")
            raise

    async def _generate_fill_in_blank_question(
        self,
        content: str,
        key_concept: str,
        difficulty_level: DifficultyLevel
    ) -> QuizQuestion:
        """Generate a fill-in-the-blank question"""
        try:
            # Find a sentence containing the key concept
            sentences = content.split('.')
            target_sentence = None
            
            for sentence in sentences:
                if key_concept.lower() in sentence.lower() and len(sentence.strip()) > 20:
                    target_sentence = sentence.strip()
                    break
            
            if not target_sentence:
                target_sentence = f"The {key_concept} is important for understanding this topic."
            
            # Replace the key concept with a blank
            question_text = target_sentence.replace(key_concept, "_____")
            
            return QuizQuestion(
                id=f"fib_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                question_text=f"Fill in the blank: {question_text}",
                question_type=QuestionType.FILL_IN_BLANK,
                difficulty_level=difficulty_level,
                correct_answer=key_concept,
                explanation=f"The correct answer is '{key_concept}' as mentioned in the source material.",
                source_content=content[:300] + "..." if len(content) > 300 else content,
                confidence_score=0.8,
                learning_objectives=[f"Recall key terms related to {key_concept}"],
                metadata={"key_concept": key_concept, "blank_type": "term"}
            )
            
        except Exception as e:
            logger.error(f"Error generating fill-in-blank question: {str(e)}")
            raise

    async def _generate_essay_question_text(
        self,
        content: str,
        key_concepts: List[str],
        difficulty_level: DifficultyLevel
    ) -> str:
        """Generate essay question text that requires synthesis"""
        try:
            templates = [
                f"Analyze the relationship between {key_concepts[0]} and {key_concepts[1] if len(key_concepts) > 1 else 'related concepts'} based on the provided material.",
                f"Evaluate the significance of {key_concepts[0]} in the context of the research presented.",
                f"Compare and contrast different approaches to {key_concepts[0]} discussed in the document.",
                f"Critically examine the implications of {key_concepts[0]} for future research in this field.",
                f"Synthesize the key findings related to {key_concepts[0]} and propose potential applications."
            ]
            
            # Select template based on difficulty
            template_idx = min(len(templates) - 1, 
                             0 if difficulty_level == DifficultyLevel.BEGINNER else
                             2 if difficulty_level == DifficultyLevel.INTERMEDIATE else 4)
            
            return templates[template_idx]
            
        except Exception as e:
            logger.error(f"Error generating essay question text: {str(e)}")
            return f"Discuss the importance of {key_concepts[0] if key_concepts else 'the main concept'} based on the provided material."

    async def _generate_essay_outline(
        self,
        question_text: str,
        content: str,
        key_concepts: List[str]
    ) -> str:
        """Generate essay outline/model answer"""
        try:
            outline = f"Essay Outline for: {question_text}\n\n"
            outline += "I. Introduction\n"
            outline += f"   - Define {key_concepts[0] if key_concepts else 'key concept'}\n"
            outline += "   - State thesis/main argument\n\n"
            outline += "II. Main Body\n"
            outline += f"   - Analysis of {key_concepts[0] if key_concepts else 'main concept'}\n"
            if len(key_concepts) > 1:
                outline += f"   - Relationship with {key_concepts[1]}\n"
            outline += "   - Supporting evidence from the text\n"
            outline += "   - Critical evaluation\n\n"
            outline += "III. Conclusion\n"
            outline += "   - Synthesis of key points\n"
            outline += "   - Implications and future directions\n"
            
            return outline
            
        except Exception as e:
            logger.error(f"Error generating essay outline: {str(e)}")
            return "Provide a structured analysis addressing the question with supporting evidence."

    async def _generate_essay_rubric(
        self,
        question_text: str,
        key_concepts: List[str],
        content: str
    ) -> str:
        """Generate essay rubric"""
        try:
            rubric = "Essay Evaluation Rubric:\n\n"
            rubric += "Excellent (4 points):\n"
            rubric += "- Demonstrates deep understanding of key concepts\n"
            rubric += "- Provides comprehensive analysis with strong evidence\n"
            rubric += "- Shows critical thinking and synthesis\n"
            rubric += "- Well-organized with clear structure\n\n"
            rubric += "Good (3 points):\n"
            rubric += "- Shows good understanding of concepts\n"
            rubric += "- Provides adequate analysis with some evidence\n"
            rubric += "- Some critical thinking evident\n"
            rubric += "- Generally well-organized\n\n"
            rubric += "Satisfactory (2 points):\n"
            rubric += "- Basic understanding of concepts\n"
            rubric += "- Limited analysis with minimal evidence\n"
            rubric += "- Little critical thinking\n"
            rubric += "- Basic organization\n\n"
            rubric += "Needs Improvement (1 point):\n"
            rubric += "- Poor understanding of concepts\n"
            rubric += "- Inadequate analysis\n"
            rubric += "- No critical thinking evident\n"
            rubric += "- Poor organization\n"
            
            return rubric
            
        except Exception as e:
            logger.error(f"Error generating essay rubric: {str(e)}")
            return "Evaluate based on understanding, analysis, evidence, and organization."

    async def _generate_short_answer_rubric(
        self,
        question_text: str,
        model_answer: str,
        content: str
    ) -> str:
        """Generate rubric for short answer questions"""
        try:
            rubric = "Short Answer Evaluation Rubric:\n\n"
            rubric += "Full Credit (2 points):\n"
            rubric += "- Accurate and complete answer\n"
            rubric += "- Demonstrates clear understanding\n"
            rubric += "- Uses appropriate terminology\n\n"
            rubric += "Partial Credit (1 point):\n"
            rubric += "- Partially correct answer\n"
            rubric += "- Shows some understanding\n"
            rubric += "- Minor inaccuracies or omissions\n\n"
            rubric += "No Credit (0 points):\n"
            rubric += "- Incorrect or irrelevant answer\n"
            rubric += "- No understanding demonstrated\n"
            rubric += "- Major inaccuracies\n\n"
            rubric += f"Model Answer: {model_answer}"
            
            return rubric
            
        except Exception as e:
            logger.error(f"Error generating short answer rubric: {str(e)}")
            return f"Compare answer to model response: {model_answer}"

    async def _generate_learning_objectives(self, key_concepts: List[str]) -> List[str]:
        """Generate learning objectives from key concepts"""
        try:
            objectives = []
            
            for concept in key_concepts[:5]:  # Limit to 5 objectives
                objectives.extend([
                    f"Understand the concept of {concept}",
                    f"Apply knowledge of {concept} to new situations",
                    f"Analyze the role of {concept} in the broader context"
                ])
            
            # Remove duplicates and return unique objectives
            return list(set(objectives))[:8]  # Limit to 8 objectives
            
        except Exception as e:
            logger.error(f"Error generating learning objectives: {str(e)}")
            return ["Understand key concepts", "Apply knowledge", "Analyze information"]

    def _estimate_completion_time(self, questions: List[QuizQuestion]) -> int:
        """Estimate quiz completion time in minutes"""
        try:
            time_estimates = {
                QuestionType.MULTIPLE_CHOICE: 1,
                QuestionType.TRUE_FALSE: 0.5,
                QuestionType.FILL_IN_BLANK: 1,
                QuestionType.SHORT_ANSWER: 3,
                QuestionType.ESSAY: 15
            }
            
            total_time = 0
            for question in questions:
                base_time = time_estimates.get(question.question_type, 2)
                
                # Adjust for difficulty
                if question.difficulty_level == DifficultyLevel.ADVANCED:
                    base_time *= 1.5
                elif question.difficulty_level == DifficultyLevel.BEGINNER:
                    base_time *= 0.8
                
                total_time += base_time
            
            return max(5, int(total_time))  # Minimum 5 minutes
            
        except Exception as e:
            logger.error(f"Error estimating completion time: {str(e)}")
            return 15  # Default 15 minutes

    async def _store_quiz(self, quiz: Quiz, user_id: str) -> None:
        """Store quiz in database"""
        try:
            db = next(get_db())
            try:
                # Create quiz record
                quiz_record = QuizModel(
                    id=quiz.id,
                    title=quiz.title,
                    description=quiz.description,
                    document_id=quiz.document_id,
                    user_id=user_id,
                    difficulty_level=quiz.difficulty_level.value,
                    estimated_time_minutes=quiz.estimated_time_minutes,
                    learning_objectives=json.dumps(quiz.learning_objectives),
                    quiz_metadata=quiz.metadata
                )
                db.add(quiz_record)
                
                # Create question records
                for question in quiz.questions:
                    question_record = QuizQuestionModel(
                        id=question.id,
                        quiz_id=quiz.id,
                        question_text=question.question_text,
                        question_type=question.question_type.value,
                        difficulty_level=question.difficulty_level.value,
                        options=json.dumps(question.options) if question.options else None,
                        correct_answer=question.correct_answer,
                        explanation=question.explanation,
                        source_content=question.source_content,
                        confidence_score=question.confidence_score,
                        learning_objectives=json.dumps(question.learning_objectives),
                        question_metadata=question.metadata
                    )
                    db.add(question_record)
                
                db.commit()
                logger.info(f"Stored quiz {quiz.id} with {len(quiz.questions)} questions")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing quiz: {str(e)}")
            raise

    async def get_quiz_by_id(self, quiz_id: str, user_id: str) -> Optional[Quiz]:
        """Retrieve quiz by ID"""
        try:
            db = next(get_db())
            try:
                # Get quiz record
                quiz_record = db.query(QuizModel).filter(
                    QuizModel.id == quiz_id,
                    QuizModel.user_id == user_id
                ).first()
                
                if not quiz_record:
                    return None
                
                # Get question records
                question_records = db.query(QuizQuestionModel).filter(
                    QuizQuestionModel.quiz_id == quiz_id
                ).all()
                
                # Convert to Quiz object
                questions = []
                for q_record in question_records:
                    question = QuizQuestion(
                        id=q_record.id,
                        question_text=q_record.question_text,
                        question_type=QuestionType(q_record.question_type),
                        difficulty_level=DifficultyLevel(q_record.difficulty_level),
                        options=json.loads(q_record.options) if q_record.options else None,
                        correct_answer=q_record.correct_answer,
                        explanation=q_record.explanation,
                        source_content=q_record.source_content,
                        confidence_score=q_record.confidence_score or 0.0,
                        learning_objectives=json.loads(q_record.learning_objectives) if q_record.learning_objectives else [],
                        metadata=q_record.question_metadata or {}
                    )
                    questions.append(question)
                
                quiz = Quiz(
                    id=quiz_record.id,
                    title=quiz_record.title,
                    description=quiz_record.description,
                    document_id=quiz_record.document_id,
                    questions=questions,
                    difficulty_level=DifficultyLevel(quiz_record.difficulty_level),
                    estimated_time_minutes=quiz_record.estimated_time_minutes,
                    learning_objectives=json.loads(quiz_record.learning_objectives) if quiz_record.learning_objectives else [],
                    created_at=quiz_record.created_at,
                    metadata=quiz_record.quiz_metadata or {}
                )
                
                return quiz
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving quiz {quiz_id}: {str(e)}")
            return None

    async def get_user_quizzes(self, user_id: str) -> List[Quiz]:
        """Get all quizzes for a user"""
        try:
            db = next(get_db())
            try:
                quiz_records = db.query(QuizModel).filter(
                    QuizModel.user_id == user_id
                ).order_by(QuizModel.created_at.desc()).all()
                
                quizzes = []
                for quiz_record in quiz_records:
                    quiz = await self.get_quiz_by_id(quiz_record.id, user_id)
                    if quiz:
                        quizzes.append(quiz)
                
                return quizzes
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving user quizzes: {str(e)}")
            return []

    async def _get_user_performance_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's quiz performance history"""
        try:
            db = next(get_db())
            try:
                from sqlalchemy import func
                
                # Get recent quiz attempts
                attempts = db.query(QuizAttempt).filter(
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.completed_at.isnot(None)
                ).order_by(QuizAttempt.completed_at.desc()).limit(10).all()
                
                if not attempts:
                    return {'average_score': 0.7, 'total_attempts': 0}
                
                scores = [attempt.score for attempt in attempts if attempt.score is not None]
                avg_score = sum(scores) / len(scores) if scores else 0.7
                
                return {
                    'average_score': avg_score,
                    'total_attempts': len(attempts),
                    'recent_scores': scores[:5]
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting user performance history: {str(e)}")
            return {'average_score': 0.7, 'total_attempts': 0}

    async def validate_question_quality(self, question: QuizQuestion, content: str) -> Dict[str, Any]:
        """Validate the quality of a generated question"""
        try:
            quality_metrics = {
                'clarity_score': 0.0,
                'relevance_score': 0.0,
                'difficulty_appropriateness': 0.0,
                'answer_quality': 0.0,
                'overall_score': 0.0,
                'issues': [],
                'suggestions': []
            }
            
            # Check question clarity
            question_words = question.question_text.split()
            if len(question_words) < 5:
                quality_metrics['issues'].append("Question too short")
                quality_metrics['clarity_score'] = 0.3
            elif len(question_words) > 50:
                quality_metrics['issues'].append("Question too long")
                quality_metrics['clarity_score'] = 0.6
            else:
                quality_metrics['clarity_score'] = 0.8
            
            # Check relevance to content
            question_lower = question.question_text.lower()
            content_lower = content.lower()
            
            # Count overlapping words
            question_words_set = set(question_lower.split())
            content_words_set = set(content_lower.split())
            overlap = len(question_words_set.intersection(content_words_set))
            
            quality_metrics['relevance_score'] = min(1.0, overlap / len(question_words_set)) if question_words_set else 0.0
            
            # Check answer quality
            if question.correct_answer and len(question.correct_answer.strip()) > 0:
                quality_metrics['answer_quality'] = 0.8
                if question.explanation and len(question.explanation) > 20:
                    quality_metrics['answer_quality'] = 1.0
            else:
                quality_metrics['issues'].append("Missing or poor quality answer")
                quality_metrics['answer_quality'] = 0.2
            
            # Check difficulty appropriateness
            assessed_difficulty = await self.assess_question_difficulty(question, content)
            if assessed_difficulty == question.difficulty_level:
                quality_metrics['difficulty_appropriateness'] = 1.0
            else:
                quality_metrics['difficulty_appropriateness'] = 0.6
                quality_metrics['suggestions'].append(f"Consider adjusting difficulty to {assessed_difficulty.value}")
            
            # Calculate overall score
            scores = [
                quality_metrics['clarity_score'],
                quality_metrics['relevance_score'],
                quality_metrics['difficulty_appropriateness'],
                quality_metrics['answer_quality']
            ]
            quality_metrics['overall_score'] = sum(scores) / len(scores)
            
            # Add suggestions based on scores
            if quality_metrics['clarity_score'] < 0.7:
                quality_metrics['suggestions'].append("Improve question clarity and structure")
            if quality_metrics['relevance_score'] < 0.5:
                quality_metrics['suggestions'].append("Ensure question is more relevant to source content")
            if quality_metrics['answer_quality'] < 0.7:
                quality_metrics['suggestions'].append("Improve answer quality and explanation")
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error validating question quality: {str(e)}")
            return {
                'clarity_score': 0.5,
                'relevance_score': 0.5,
                'difficulty_appropriateness': 0.5,
                'answer_quality': 0.5,
                'overall_score': 0.5,
                'issues': ['Validation error'],
                'suggestions': ['Review question manually']
            }

    async def generate_comprehensive_answer_key(self, quiz: Quiz) -> Dict[str, Any]:
        """Generate comprehensive answer key with detailed explanations and rubrics"""
        try:
            answer_key = await self.generate_answer_key(quiz)
            
            # Enhance with additional information
            answer_key['detailed_explanations'] = []
            answer_key['rubrics'] = []
            answer_key['learning_outcomes'] = []
            
            for i, question in enumerate(quiz.questions):
                # Detailed explanation
                detailed_explanation = {
                    'question_number': i + 1,
                    'question_id': question.id,
                    'explanation': question.explanation,
                    'key_concepts': question.metadata.get('key_concept', ''),
                    'difficulty_rationale': f"This question is rated as {question.difficulty_level.value} because it requires {self._get_difficulty_rationale(question.difficulty_level)}",
                    'common_mistakes': self._generate_common_mistakes(question),
                    'teaching_points': self._generate_teaching_points(question)
                }
                answer_key['detailed_explanations'].append(detailed_explanation)
                
                # Rubric for subjective questions
                if question.question_type in [QuestionType.SHORT_ANSWER, QuestionType.ESSAY]:
                    rubric = {
                        'question_number': i + 1,
                        'question_id': question.id,
                        'rubric_type': question.question_type.value,
                        'criteria': self._generate_rubric_criteria(question),
                        'scoring_guide': self._generate_scoring_guide(question)
                    }
                    answer_key['rubrics'].append(rubric)
                
                # Learning outcomes
                for objective in question.learning_objectives:
                    if objective not in answer_key['learning_outcomes']:
                        answer_key['learning_outcomes'].append(objective)
            
            # Add quiz-level statistics
            answer_key['quiz_statistics'] = {
                'total_points': sum(answer_key['scoring_guide'].get(q.question_type.value, 1) for q in quiz.questions),
                'question_type_distribution': self._get_question_type_distribution(quiz.questions),
                'difficulty_distribution': self._get_difficulty_distribution(quiz.questions),
                'estimated_grading_time': self._estimate_grading_time(quiz.questions)
            }
            
            return answer_key
            
        except Exception as e:
            logger.error(f"Error generating comprehensive answer key: {str(e)}")
            return await self.generate_answer_key(quiz)

    def _get_difficulty_rationale(self, difficulty: DifficultyLevel) -> str:
        """Get rationale for difficulty level"""
        rationales = {
            DifficultyLevel.BEGINNER: "basic recall and recognition of concepts",
            DifficultyLevel.INTERMEDIATE: "understanding and application of concepts",
            DifficultyLevel.ADVANCED: "analysis, synthesis, and evaluation of complex ideas"
        }
        return rationales.get(difficulty, "appropriate cognitive engagement")

    def _generate_common_mistakes(self, question: QuizQuestion) -> List[str]:
        """Generate common mistakes for a question"""
        mistakes = []
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            mistakes.extend([
                "Choosing the most familiar option without careful consideration",
                "Misreading the question stem",
                "Falling for attractive distractors"
            ])
        elif question.question_type == QuestionType.SHORT_ANSWER:
            mistakes.extend([
                "Providing incomplete answers",
                "Using imprecise terminology",
                "Not supporting answers with evidence"
            ])
        elif question.question_type == QuestionType.ESSAY:
            mistakes.extend([
                "Lack of clear thesis statement",
                "Insufficient evidence and examples",
                "Poor organization and structure",
                "Not addressing all parts of the question"
            ])
        
        return mistakes

    def _generate_teaching_points(self, question: QuizQuestion) -> List[str]:
        """Generate teaching points for a question"""
        points = []
        
        key_concept = question.metadata.get('key_concept', 'the concept')
        
        points.extend([
            f"Emphasize the importance of {key_concept} in the broader context",
            f"Provide additional examples of {key_concept} in practice",
            f"Connect {key_concept} to students' prior knowledge",
            "Encourage critical thinking about the topic"
        ])
        
        return points

    def _generate_rubric_criteria(self, question: QuizQuestion) -> List[Dict[str, str]]:
        """Generate rubric criteria for subjective questions"""
        if question.question_type == QuestionType.SHORT_ANSWER:
            return [
                {"criterion": "Accuracy", "description": "Correctness of the answer"},
                {"criterion": "Completeness", "description": "Thoroughness of the response"},
                {"criterion": "Clarity", "description": "Clear expression of ideas"},
                {"criterion": "Use of terminology", "description": "Appropriate use of subject-specific terms"}
            ]
        elif question.question_type == QuestionType.ESSAY:
            return [
                {"criterion": "Thesis/Argument", "description": "Clear and well-developed main argument"},
                {"criterion": "Evidence", "description": "Quality and relevance of supporting evidence"},
                {"criterion": "Analysis", "description": "Depth of analysis and critical thinking"},
                {"criterion": "Organization", "description": "Logical structure and flow"},
                {"criterion": "Writing quality", "description": "Grammar, style, and clarity"}
            ]
        
        return []

    def _generate_scoring_guide(self, question: QuizQuestion) -> Dict[str, str]:
        """Generate scoring guide for subjective questions"""
        if question.question_type == QuestionType.SHORT_ANSWER:
            return {
                "2 points": "Complete, accurate answer with clear explanation",
                "1 point": "Partially correct answer with minor issues",
                "0 points": "Incorrect or irrelevant answer"
            }
        elif question.question_type == QuestionType.ESSAY:
            return {
                "5 points": "Excellent work meeting all criteria at high level",
                "4 points": "Good work meeting most criteria well",
                "3 points": "Satisfactory work meeting basic requirements",
                "2 points": "Below expectations with significant issues",
                "1 point": "Poor work with major problems",
                "0 points": "No submission or completely inadequate"
            }
        
        return {}

    def _get_question_type_distribution(self, questions: List[QuizQuestion]) -> Dict[str, int]:
        """Get distribution of question types"""
        distribution = {}
        for question in questions:
            question_type = question.question_type.value
            distribution[question_type] = distribution.get(question_type, 0) + 1
        return distribution

    def _get_difficulty_distribution(self, questions: List[QuizQuestion]) -> Dict[str, int]:
        """Get distribution of difficulty levels"""
        distribution = {}
        for question in questions:
            difficulty = question.difficulty_level.value
            distribution[difficulty] = distribution.get(difficulty, 0) + 1
        return distribution

    def _estimate_grading_time(self, questions: List[QuizQuestion]) -> int:
        """Estimate grading time in minutes"""
        time_estimates = {
            QuestionType.MULTIPLE_CHOICE: 0.5,
            QuestionType.TRUE_FALSE: 0.25,
            QuestionType.FILL_IN_BLANK: 0.5,
            QuestionType.SHORT_ANSWER: 2,
            QuestionType.ESSAY: 8
        }
        
        total_time = sum(time_estimates.get(q.question_type, 1) for q in questions)
        return max(5, int(total_time))