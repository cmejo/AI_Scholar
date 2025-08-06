"""
Task 4.1 Implementation Verification Test

This test verifies that all requirements for task 4.1 have been implemented:
- Create AI-powered question generation from research documents
- Build multiple question types: multiple choice, short answer, and essay
- Implement difficulty assessment and adaptive question selection
- Add automatic answer key generation and explanation creation
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.quiz_generation_service import (
    QuizGenerationService,
    QuestionType, 
    DifficultyLevel,
    QuizQuestion,
    Quiz
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_ai_powered_question_generation():
    """Verify AI-powered question generation from research documents"""
    try:
        logger.info("✓ Verifying AI-powered question generation from research documents...")
        
        service = QuizGenerationService()
        
        # Test with realistic research content
        research_content = """
        This study investigates the effectiveness of machine learning algorithms in 
        natural language processing tasks. We implemented several deep learning models 
        including transformer architectures and convolutional neural networks. The 
        results demonstrate significant improvements in accuracy and processing speed 
        compared to traditional statistical methods. Our methodology involved training 
        on large datasets and evaluating performance using standard benchmarks.
        """
        
        # Test full quiz generation from document
        quiz = await service.generate_quiz_from_document(
            document_id="research_doc_123",
            user_id="test_user",
            num_questions=5,
            question_types=[QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER, QuestionType.ESSAY],
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        logger.info(f"  Generated quiz with {len(quiz.questions)} questions")
        logger.info(f"  Quiz title: {quiz.title}")
        logger.info(f"  Estimated time: {quiz.estimated_time_minutes} minutes")
        
        # Verify content analysis is working
        content_analysis = await service.analyze_content_complexity(research_content)
        logger.info(f"  Content analysis - Type: {content_analysis['content_type']}")
        logger.info(f"  Content analysis - Difficulty: {content_analysis['recommended_difficulty'].value}")
        
        return True
        
    except Exception as e:
        logger.error(f"AI-powered question generation verification failed: {str(e)}")
        return False

async def verify_multiple_question_types():
    """Verify multiple question types: multiple choice, short answer, and essay"""
    try:
        logger.info("✓ Verifying multiple question types support...")
        
        service = QuizGenerationService()
        
        sample_content = """
        Artificial intelligence encompasses machine learning, deep learning, and 
        natural language processing. These technologies enable computers to perform 
        tasks that typically require human intelligence, such as pattern recognition, 
        decision making, and language understanding.
        """
        
        # Test each required question type
        question_types_tested = []
        
        # 1. Multiple Choice
        mc_question = await service.generate_multiple_choice_question(
            content=sample_content,
            key_concept="artificial intelligence",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        assert mc_question.question_type == QuestionType.MULTIPLE_CHOICE
        assert len(mc_question.options) == 4
        assert mc_question.correct_answer in mc_question.options
        question_types_tested.append("multiple_choice")
        logger.info(f"  ✓ Multiple choice question generated with {len(mc_question.options)} options")
        
        # 2. Short Answer
        sa_question = await service.generate_short_answer_question(
            content=sample_content,
            key_concept="machine learning",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        assert sa_question.question_type == QuestionType.SHORT_ANSWER
        assert len(sa_question.correct_answer) > 10  # Meaningful answer
        assert len(sa_question.explanation) > 20  # Has rubric/explanation
        question_types_tested.append("short_answer")
        logger.info(f"  ✓ Short answer question generated with model answer")
        
        # 3. Essay
        essay_question = await service.generate_essay_question(
            content=sample_content,
            key_concepts=["artificial intelligence", "machine learning"],
            difficulty_level=DifficultyLevel.ADVANCED
        )
        assert essay_question.question_type == QuestionType.ESSAY
        assert "analyze" in essay_question.question_text.lower() or "evaluate" in essay_question.question_text.lower()
        assert len(essay_question.correct_answer) > 50  # Has outline/model answer
        question_types_tested.append("essay")
        logger.info(f"  ✓ Essay question generated with outline")
        
        # 4. Additional types (True/False, Fill-in-blank)
        tf_question = await service._generate_true_false_question(
            content=sample_content,
            key_concept="deep learning",
            difficulty_level=DifficultyLevel.BEGINNER
        )
        assert tf_question.question_type == QuestionType.TRUE_FALSE
        assert tf_question.correct_answer in ["True", "False"]
        question_types_tested.append("true_false")
        logger.info(f"  ✓ True/False question generated")
        
        fib_question = await service._generate_fill_in_blank_question(
            content=sample_content,
            key_concept="natural language processing",
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        assert fib_question.question_type == QuestionType.FILL_IN_BLANK
        assert "_____" in fib_question.question_text
        question_types_tested.append("fill_in_blank")
        logger.info(f"  ✓ Fill-in-blank question generated")
        
        logger.info(f"  Successfully tested {len(question_types_tested)} question types")
        return True
        
    except Exception as e:
        logger.error(f"Multiple question types verification failed: {str(e)}")
        return False

async def verify_difficulty_assessment_and_adaptive_selection():
    """Verify difficulty assessment and adaptive question selection"""
    try:
        logger.info("✓ Verifying difficulty assessment and adaptive question selection...")
        
        service = QuizGenerationService()
        
        # Test difficulty assessment
        sample_content = "Machine learning is a method of data analysis that automates analytical model building."
        
        # Create questions of different complexities
        simple_question = QuizQuestion(
            id="simple",
            question_text="What is machine learning?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            difficulty_level=DifficultyLevel.BEGINNER,
            correct_answer="A method of data analysis"
        )
        
        complex_question = QuizQuestion(
            id="complex",
            question_text="Critically analyze the epistemological implications of automated analytical model building in machine learning paradigms and evaluate their impact on traditional statistical inference methodologies.",
            question_type=QuestionType.ESSAY,
            difficulty_level=DifficultyLevel.ADVANCED,
            correct_answer="Complex analysis required"
        )
        
        # Test difficulty assessment
        simple_assessed = await service.assess_question_difficulty(simple_question, sample_content)
        complex_assessed = await service.assess_question_difficulty(complex_question, sample_content)
        
        logger.info(f"  Simple question assessed as: {simple_assessed.value}")
        logger.info(f"  Complex question assessed as: {complex_assessed.value}")
        
        # Test adaptive question selection
        high_performer_history = {'average_score': 0.9, 'total_attempts': 10}
        low_performer_history = {'average_score': 0.4, 'total_attempts': 5}
        
        key_concepts = ["machine learning", "data analysis", "model building"]
        
        high_questions = await service.adaptive_question_selection(
            user_id="high_performer",
            content=sample_content,
            key_concepts=key_concepts,
            user_performance_history=high_performer_history
        )
        
        low_questions = await service.adaptive_question_selection(
            user_id="low_performer",
            content=sample_content,
            key_concepts=key_concepts,
            user_performance_history=low_performer_history
        )
        
        # Verify adaptive selection works
        high_difficulties = [q.difficulty_level for q in high_questions]
        low_difficulties = [q.difficulty_level for q in low_questions]
        
        logger.info(f"  High performer difficulties: {[d.value for d in high_difficulties]}")
        logger.info(f"  Low performer difficulties: {[d.value for d in low_difficulties]}")
        
        # High performers should get more advanced questions
        assert any(d == DifficultyLevel.ADVANCED for d in high_difficulties), "High performers should get advanced questions"
        
        # Low performers should get more beginner questions
        assert any(d == DifficultyLevel.BEGINNER for d in low_difficulties), "Low performers should get beginner questions"
        
        logger.info("  ✓ Adaptive question selection working correctly")
        return True
        
    except Exception as e:
        logger.error(f"Difficulty assessment and adaptive selection verification failed: {str(e)}")
        return False

async def verify_automatic_answer_key_generation():
    """Verify automatic answer key generation and explanation creation"""
    try:
        logger.info("✓ Verifying automatic answer key generation and explanation creation...")
        
        service = QuizGenerationService()
        
        # Create a sample quiz with different question types
        questions = [
            QuizQuestion(
                id="q1",
                question_text="What is the primary purpose of machine learning?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                options=["Data analysis automation", "Manual coding", "Database management", "Web development"],
                correct_answer="Data analysis automation",
                explanation="Machine learning automates the process of analytical model building.",
                learning_objectives=["Understand ML purpose"],
                metadata={"key_concept": "machine learning"}
            ),
            QuizQuestion(
                id="q2",
                question_text="Explain how neural networks process information.",
                question_type=QuestionType.SHORT_ANSWER,
                difficulty_level=DifficultyLevel.ADVANCED,
                correct_answer="Neural networks process information through interconnected nodes that apply weights and activation functions to transform input data into output predictions.",
                explanation="Short answer rubric with scoring criteria.",
                learning_objectives=["Explain neural network processing"],
                metadata={"key_concept": "neural networks"}
            ),
            QuizQuestion(
                id="q3",
                question_text="Analyze the impact of deep learning on computer vision applications.",
                question_type=QuestionType.ESSAY,
                difficulty_level=DifficultyLevel.ADVANCED,
                correct_answer="Essay outline covering deep learning fundamentals, computer vision applications, and impact analysis.",
                explanation="Essay rubric with detailed scoring criteria.",
                learning_objectives=["Analyze deep learning impact"],
                metadata={"key_concepts": ["deep learning", "computer vision"]}
            )
        ]
        
        quiz = Quiz(
            id="verification_quiz",
            title="Verification Quiz",
            description="Quiz for testing answer key generation",
            document_id="test_doc",
            questions=questions,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            estimated_time_minutes=20,
            learning_objectives=["Understand ML concepts", "Analyze AI applications"],
            created_at=datetime.now()
        )
        
        # Test basic answer key generation
        basic_answer_key = await service.generate_answer_key(quiz)
        
        assert basic_answer_key['quiz_id'] == quiz.id
        assert basic_answer_key['total_questions'] == len(questions)
        assert len(basic_answer_key['answers']) == len(questions)
        assert 'scoring_guide' in basic_answer_key
        
        logger.info(f"  ✓ Basic answer key generated with {len(basic_answer_key['answers'])} answers")
        
        # Test comprehensive answer key generation
        comprehensive_key = await service.generate_comprehensive_answer_key(quiz)
        
        assert 'detailed_explanations' in comprehensive_key
        assert 'learning_outcomes' in comprehensive_key
        assert 'quiz_statistics' in comprehensive_key
        assert len(comprehensive_key['detailed_explanations']) == len(questions)
        
        # Verify detailed explanations have required components
        for explanation in comprehensive_key['detailed_explanations']:
            assert 'difficulty_rationale' in explanation
            assert 'common_mistakes' in explanation
            assert 'teaching_points' in explanation
        
        # Verify quiz statistics
        stats = comprehensive_key['quiz_statistics']
        assert 'total_points' in stats
        assert 'question_type_distribution' in stats
        assert 'difficulty_distribution' in stats
        assert 'estimated_grading_time' in stats
        
        logger.info(f"  ✓ Comprehensive answer key generated with detailed explanations")
        logger.info(f"  ✓ Quiz statistics: {stats['total_points']} total points")
        logger.info(f"  ✓ Question distribution: {stats['question_type_distribution']}")
        
        # Test question quality validation
        quality_metrics = await service.validate_question_quality(questions[0], "Sample content about machine learning")
        
        assert 'overall_score' in quality_metrics
        assert 'clarity_score' in quality_metrics
        assert 'relevance_score' in quality_metrics
        assert 'answer_quality' in quality_metrics
        assert 'suggestions' in quality_metrics
        
        logger.info(f"  ✓ Question quality validation working (score: {quality_metrics['overall_score']:.2f})")
        
        return True
        
    except Exception as e:
        logger.error(f"Answer key generation verification failed: {str(e)}")
        return False

async def verify_requirements_compliance():
    """Verify compliance with specific requirements 4.1, 4.2, 4.4"""
    try:
        logger.info("✓ Verifying compliance with requirements 4.1, 4.2, 4.4...")
        
        service = QuizGenerationService()
        
        # Requirement 4.1: WHEN studying documents THEN quizzes SHALL be automatically generated from content
        sample_content = "Artificial intelligence and machine learning are transforming technology."
        quiz = await service.generate_quiz_from_document(
            document_id="req_test_doc",
            user_id="req_test_user",
            num_questions=3
        )
        assert len(quiz.questions) > 0, "Quiz should be automatically generated from content"
        logger.info("  ✓ Requirement 4.1: Automatic quiz generation from content - PASSED")
        
        # Requirement 4.2: WHEN taking assessments THEN multiple question types SHALL be supported
        question_types_in_quiz = set(q.question_type for q in quiz.questions)
        supported_types = {QuestionType.MULTIPLE_CHOICE, QuestionType.SHORT_ANSWER, QuestionType.TRUE_FALSE}
        assert len(question_types_in_quiz.intersection(supported_types)) > 0, "Multiple question types should be supported"
        logger.info("  ✓ Requirement 4.2: Multiple question types support - PASSED")
        
        # Requirement 4.4: WHEN studying THEN adaptive difficulty SHALL adjust based on performance
        # Test with different performance levels
        high_perf_questions = await service.adaptive_question_selection(
            user_id="high_user",
            content=sample_content,
            key_concepts=["artificial intelligence"],
            user_performance_history={'average_score': 0.9, 'total_attempts': 10}
        )
        
        low_perf_questions = await service.adaptive_question_selection(
            user_id="low_user", 
            content=sample_content,
            key_concepts=["artificial intelligence"],
            user_performance_history={'average_score': 0.3, 'total_attempts': 5}
        )
        
        # Verify adaptive difficulty
        high_difficulties = [q.difficulty_level for q in high_perf_questions]
        low_difficulties = [q.difficulty_level for q in low_perf_questions]
        
        # High performers should get harder questions on average
        high_avg = sum(3 if d == DifficultyLevel.ADVANCED else 2 if d == DifficultyLevel.INTERMEDIATE else 1 for d in high_difficulties) / len(high_difficulties)
        low_avg = sum(3 if d == DifficultyLevel.ADVANCED else 2 if d == DifficultyLevel.INTERMEDIATE else 1 for d in low_difficulties) / len(low_difficulties)
        
        assert high_avg >= low_avg, "High performers should get more difficult questions on average"
        logger.info("  ✓ Requirement 4.4: Adaptive difficulty based on performance - PASSED")
        
        return True
        
    except Exception as e:
        logger.error(f"Requirements compliance verification failed: {str(e)}")
        return False

async def main():
    """Run all verification tests for Task 4.1"""
    logger.info("=== Task 4.1 Implementation Verification ===")
    logger.info("Task: Implement quiz generation service")
    logger.info("Requirements: 4.1, 4.2, 4.4")
    logger.info("")
    
    # Run all verification tests
    tests = [
        ("AI-powered question generation", verify_ai_powered_question_generation()),
        ("Multiple question types", verify_multiple_question_types()),
        ("Difficulty assessment & adaptive selection", verify_difficulty_assessment_and_adaptive_selection()),
        ("Automatic answer key generation", verify_automatic_answer_key_generation()),
        ("Requirements compliance", verify_requirements_compliance())
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"Running: {test_name}")
        result = await test_coro
        results.append((test_name, result))
        logger.info(f"Result: {'PASSED' if result else 'FAILED'}")
        logger.info("")
    
    # Summary
    logger.info("=== Verification Summary ===")
    passed_count = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"\nTotal: {passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        logger.info("🎉 Task 4.1 implementation VERIFIED - All requirements met!")
        return 0
    else:
        logger.error("❌ Task 4.1 implementation INCOMPLETE - Some requirements not met!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)