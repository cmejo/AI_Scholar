"""
Quiz Generation API Endpoints for Educational Enhancement System
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from services.quiz_generation_service import (
    QuizGenerationService, 
    Quiz, 
    QuizQuestion, 
    QuestionType, 
    DifficultyLevel
)
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quiz", tags=["quiz"])
auth_service = AuthService()
quiz_service = QuizGenerationService()

# Pydantic Models for API

class QuizGenerationRequest(BaseModel):
    document_id: str
    num_questions: int = 10
    question_types: List[QuestionType] = [
        QuestionType.MULTIPLE_CHOICE,
        QuestionType.SHORT_ANSWER,
        QuestionType.TRUE_FALSE
    ]
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_objectives: Optional[List[str]] = None

class QuestionGenerationRequest(BaseModel):
    document_id: str
    question_type: QuestionType
    key_concept: str
    difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE

class QuizQuestionResponse(BaseModel):
    id: str
    question_text: str
    question_type: str
    difficulty_level: str
    options: Optional[List[str]] = None
    explanation: str
    source_content: str
    confidence_score: float
    learning_objectives: List[str]
    metadata: Dict[str, Any]

class QuizResponse(BaseModel):
    id: str
    title: str
    description: str
    document_id: str
    questions: List[QuizQuestionResponse]
    difficulty_level: str
    estimated_time_minutes: int
    learning_objectives: List[str]
    created_at: datetime
    metadata: Dict[str, Any]

class AnswerKeyResponse(BaseModel):
    quiz_id: str
    quiz_title: str
    total_questions: int
    answers: List[Dict[str, Any]]
    scoring_guide: Dict[str, int]
    generated_at: str

class QuizListResponse(BaseModel):
    quizzes: List[QuizResponse]
    total_count: int

# Helper function to convert Quiz to QuizResponse
def quiz_to_response(quiz: Quiz) -> QuizResponse:
    """Convert Quiz object to API response format"""
    questions = [
        QuizQuestionResponse(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type.value,
            difficulty_level=q.difficulty_level.value,
            options=q.options,
            explanation=q.explanation,
            source_content=q.source_content,
            confidence_score=q.confidence_score,
            learning_objectives=q.learning_objectives,
            metadata=q.metadata
        )
        for q in quiz.questions
    ]
    
    return QuizResponse(
        id=quiz.id,
        title=quiz.title,
        description=quiz.description,
        document_id=quiz.document_id,
        questions=questions,
        difficulty_level=quiz.difficulty_level.value,
        estimated_time_minutes=quiz.estimated_time_minutes,
        learning_objectives=quiz.learning_objectives,
        created_at=quiz.created_at,
        metadata=quiz.metadata
    )

# Dependency for authentication
async def get_current_user(token: str = Depends(auth_service.get_current_user)):
    """Get current authenticated user"""
    return token

@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizGenerationRequest,
    user = Depends(get_current_user)
):
    """Generate a comprehensive quiz from a document"""
    try:
        logger.info(f"Generating quiz for document {request.document_id} by user {user.id}")
        
        quiz = await quiz_service.generate_quiz_from_document(
            document_id=request.document_id,
            user_id=user.id,
            num_questions=request.num_questions,
            question_types=request.question_types,
            difficulty_level=request.difficulty_level,
            learning_objectives=request.learning_objectives
        )
        
        return quiz_to_response(quiz)
        
    except ValueError as e:
        logger.error(f"Invalid request for quiz generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")

@router.post("/generate-question", response_model=QuizQuestionResponse)
async def generate_single_question(
    request: QuestionGenerationRequest,
    user = Depends(get_current_user)
):
    """Generate a single question from document content"""
    try:
        logger.info(f"Generating single question for document {request.document_id}")
        
        # Get document content
        document_content = await quiz_service._get_document_content(request.document_id)
        if not document_content:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate question based on type
        if request.question_type == QuestionType.MULTIPLE_CHOICE:
            question = await quiz_service.generate_multiple_choice_question(
                content=document_content,
                key_concept=request.key_concept,
                difficulty_level=request.difficulty_level
            )
        elif request.question_type == QuestionType.SHORT_ANSWER:
            question = await quiz_service.generate_short_answer_question(
                content=document_content,
                key_concept=request.key_concept,
                difficulty_level=request.difficulty_level
            )
        elif request.question_type == QuestionType.ESSAY:
            question = await quiz_service.generate_essay_question(
                content=document_content,
                key_concepts=[request.key_concept],
                difficulty_level=request.difficulty_level
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported question type")
        
        return QuizQuestionResponse(
            id=question.id,
            question_text=question.question_text,
            question_type=question.question_type.value,
            difficulty_level=question.difficulty_level.value,
            options=question.options,
            explanation=question.explanation,
            source_content=question.source_content,
            confidence_score=question.confidence_score,
            learning_objectives=question.learning_objectives,
            metadata=question.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating single question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate question")

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    user = Depends(get_current_user)
):
    """Get a specific quiz by ID"""
    try:
        quiz = await quiz_service.get_quiz_by_id(quiz_id, user.id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        return quiz_to_response(quiz)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quiz")

@router.get("/", response_model=QuizListResponse)
async def get_user_quizzes(
    user = Depends(get_current_user),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get all quizzes for the current user"""
    try:
        all_quizzes = await quiz_service.get_user_quizzes(user.id)
        
        # Apply pagination
        paginated_quizzes = all_quizzes[offset:offset + limit]
        
        quiz_responses = [quiz_to_response(quiz) for quiz in paginated_quizzes]
        
        return QuizListResponse(
            quizzes=quiz_responses,
            total_count=len(all_quizzes)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user quizzes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quizzes")

@router.get("/{quiz_id}/answer-key", response_model=AnswerKeyResponse)
async def get_quiz_answer_key(
    quiz_id: str,
    user = Depends(get_current_user)
):
    """Get the answer key for a quiz"""
    try:
        quiz = await quiz_service.get_quiz_by_id(quiz_id, user.id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        answer_key = await quiz_service.generate_answer_key(quiz)
        
        return AnswerKeyResponse(**answer_key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating answer key for quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate answer key")

@router.post("/{quiz_id}/assess-difficulty")
async def assess_quiz_difficulty(
    quiz_id: str,
    user = Depends(get_current_user)
):
    """Assess and update the difficulty level of quiz questions"""
    try:
        quiz = await quiz_service.get_quiz_by_id(quiz_id, user.id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get document content for assessment
        document_content = await quiz_service._get_document_content(quiz.document_id)
        
        difficulty_assessments = []
        for question in quiz.questions:
            assessed_difficulty = await quiz_service.assess_question_difficulty(
                question, document_content
            )
            difficulty_assessments.append({
                "question_id": question.id,
                "current_difficulty": question.difficulty_level.value,
                "assessed_difficulty": assessed_difficulty.value,
                "confidence_score": question.confidence_score
            })
        
        return {
            "quiz_id": quiz_id,
            "assessments": difficulty_assessments,
            "overall_difficulty": quiz.difficulty_level.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing quiz difficulty: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assess difficulty")

@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    user = Depends(get_current_user)
):
    """Delete a quiz"""
    try:
        # Verify quiz exists and belongs to user
        quiz = await quiz_service.get_quiz_by_id(quiz_id, user.id)
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Delete quiz from database
        from core.database import get_db, Quiz as QuizModel, QuizQuestion as QuizQuestionModel
        db = next(get_db())
        try:
            # Delete questions first (foreign key constraint)
            db.query(QuizQuestionModel).filter(QuizQuestionModel.quiz_id == quiz_id).delete()
            # Delete quiz
            db.query(QuizModel).filter(QuizModel.id == quiz_id, QuizModel.user_id == user.id).delete()
            db.commit()
        finally:
            db.close()
        
        logger.info(f"Deleted quiz {quiz_id} for user {user.id}")
        return {"success": True, "message": "Quiz deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete quiz")

@router.get("/document/{document_id}/quizzes", response_model=QuizListResponse)
async def get_document_quizzes(
    document_id: str,
    user = Depends(get_current_user)
):
    """Get all quizzes for a specific document"""
    try:
        from core.database import get_db, Quiz as QuizModel
        
        db = next(get_db())
        try:
            quiz_ids = db.query(QuizModel.id).filter(
                QuizModel.document_id == document_id,
                QuizModel.user_id == user.id
            ).order_by(QuizModel.created_at.desc()).all()
            
            quiz_ids = [row[0] for row in quiz_ids]
        finally:
            db.close()
        
        quizzes = []
        for quiz_id in quiz_ids:
            quiz = await quiz_service.get_quiz_by_id(quiz_id, user.id)
            if quiz:
                quizzes.append(quiz)
        
        quiz_responses = [quiz_to_response(quiz) for quiz in quizzes]
        
        return QuizListResponse(
            quizzes=quiz_responses,
            total_count=len(quiz_responses)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving quizzes for document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document quizzes")

@router.get("/stats/overview")
async def get_quiz_stats(
    user = Depends(get_current_user)
):
    """Get quiz statistics for the user"""
    try:
        from core.database import get_db, Quiz as QuizModel, QuizQuestion as QuizQuestionModel
        from sqlalchemy import func
        
        db = next(get_db())
        try:
            # Get total quizzes
            total_quizzes = db.query(QuizModel).filter(QuizModel.user_id == user.id).count()
            
            # Get total questions
            total_questions = db.query(QuizQuestionModel).join(QuizModel).filter(
                QuizModel.user_id == user.id
            ).count()
            
            # Get difficulty distribution
            difficulty_results = db.query(
                QuizModel.difficulty_level, 
                func.count(QuizModel.id)
            ).filter(QuizModel.user_id == user.id).group_by(QuizModel.difficulty_level).all()
            difficulty_dist = {row[0]: row[1] for row in difficulty_results}
            
            # Get question type distribution
            question_type_results = db.query(
                QuizQuestionModel.question_type,
                func.count(QuizQuestionModel.id)
            ).join(QuizModel).filter(
                QuizModel.user_id == user.id
            ).group_by(QuizQuestionModel.question_type).all()
            question_type_dist = {row[0]: row[1] for row in question_type_results}
        finally:
            db.close()
        
        return {
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "difficulty_distribution": difficulty_dist,
            "question_type_distribution": question_type_dist,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving quiz stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quiz statistics")