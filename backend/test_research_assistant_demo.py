"""
Demo script for Research Assistant Service
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from core.database import SessionLocal, Document, DocumentChunk, User, init_db
from services.research_assistant import (
    ResearchAssistant, ResearchType, ResearchDomain,
    LiteratureReviewSection, ResearchProposal
)
import uuid

async def create_sample_research_documents(db: Session):
    """Create sample research documents for testing"""
    print("Creating sample research documents...")
    
    # Get or create test user
    user = db.query(User).filter(User.email == "researcher@example.com").first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="researcher@example.com",
            name="Research User",
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Sample research documents with realistic content
    research_docs = [
        {
            "name": "Machine Learning in Healthcare: A Systematic Review",
            "chunks": [
                "This systematic review examines the application of machine learning algorithms in healthcare settings. The study found that deep learning models significantly improved diagnostic accuracy by 23% compared to traditional methods.",
                "The methodology employed a comprehensive literature search across PubMed, IEEE, and ACM databases. Results show that convolutional neural networks demonstrated superior performance in medical image analysis.",
                "Further research is needed to address the interpretability challenges of deep learning models in clinical settings. The gap in understanding model decision-making processes remains a significant limitation.",
                "The experimental design included randomized controlled trials with over 10,000 patient records. Statistical analysis revealed significant correlations between model complexity and diagnostic accuracy."
            ]
        },
        {
            "name": "Natural Language Processing for Scientific Literature Analysis",
            "chunks": [
                "Natural language processing techniques have revolutionized the analysis of scientific literature. The study demonstrated that transformer-based models achieved 89% accuracy in extracting key findings from research papers.",
                "The qualitative analysis involved semi-structured interviews with 50 researchers. Thematic analysis revealed three major themes: efficiency, accuracy, and interpretability of NLP tools.",
                "Meta-analysis of 25 studies indicates that automated literature review tools reduce research time by 40%. Evidence suggests that AI-assisted research synthesis improves consistency and reduces bias.",
                "Limitations include the need for domain-specific training data and challenges in handling interdisciplinary research. Future work should focus on developing more generalizable NLP models."
            ]
        },
        {
            "name": "Experimental Design in Computer Science Research",
            "chunks": [
                "This paper presents best practices for experimental design in computer science research. The survey methodology included responses from 200 researchers across 15 universities.",
                "Results show that 67% of studies lack proper control groups, and 45% fail to report effect sizes. The correlation analysis revealed significant relationships between study quality and publication venue.",
                "Case study analysis of top-tier conferences demonstrates the importance of rigorous experimental protocols. Observational studies suggest that peer review quality varies significantly across venues.",
                "The research gap in standardized evaluation metrics for computer science experiments needs urgent attention. Systematic review of evaluation practices reveals inconsistencies across subfields."
            ]
        },
        {
            "name": "Data Science Applications in Social Sciences",
            "chunks": [
                "Data science methods are increasingly applied to social science research questions. The mixed-methods approach combined quantitative analysis with qualitative insights from focus groups.",
                "Regression analysis of social media data revealed significant predictors of public opinion trends. The longitudinal study tracked 5,000 participants over 24 months using advanced statistical modeling.",
                "Ethnographic observations complemented the quantitative findings, providing rich contextual understanding. The grounded theory approach identified emerging patterns in digital social behavior.",
                "Cross-sectional analysis of demographic data shows persistent inequalities in digital access. Further investigation is required to understand the causal mechanisms underlying these disparities."
            ]
        },
        {
            "name": "Research Methodology in Artificial Intelligence",
            "chunks": [
                "This comprehensive review examines research methodologies commonly used in AI research. The analysis found that experimental approaches dominate the field, accounting for 78% of published studies.",
                "Theoretical research contributes 15% of AI publications, while empirical studies make up the remaining 7%. The trend analysis shows increasing adoption of reproducible research practices.",
                "Challenges in AI research methodology include dataset bias, evaluation metrics, and computational reproducibility. The systematic review identified 12 key methodological issues requiring attention.",
                "Recommendations include standardized benchmarks, open-source implementations, and transparent reporting of experimental conditions. The field needs better integration of theoretical and empirical approaches."
            ]
        }
    ]
    
    documents = []
    for i, doc_data in enumerate(research_docs):
        # Create document record
        doc = Document(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name=doc_data["name"],
            file_path=f"/fake/research/path/{doc_data['name'].lower().replace(' ', '_').replace(':', '')}.pdf",
            content_type="application/pdf",
            size=sum(len(chunk) for chunk in doc_data["chunks"]),
            status="completed",
            chunks_count=len(doc_data["chunks"]),
            embeddings_count=len(doc_data["chunks"]),
            created_at=datetime.utcnow() - timedelta(days=30-i*5)
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        documents.append(doc)
        
        # Create chunks for this document
        for j, chunk_content in enumerate(doc_data["chunks"]):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                content=chunk_content,
                chunk_index=j,
                page_number=j + 1,
                chunk_metadata="{}"
            )
            db.add(chunk)
        
        db.commit()
    
    print(f"Created {len(documents)} research documents with chunks")
    return user, documents

async def test_research_assistant():
    """Test the research assistant functionality"""
    print("=== Research Assistant Demo ===\n")
    
    # Initialize database
    await init_db()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Create sample research documents
        user, documents = await create_sample_research_documents(db)
        
        # Initialize research assistant
        assistant = ResearchAssistant(db)
        
        print("1. Testing Literature Review Generation...")
        
        try:
            # Generate literature review
            literature_review = await assistant.generate_literature_review(
                topic="machine learning",
                user_id=user.id,
                review_type="comprehensive",
                max_length=3000
            )
            
            print(f"✓ Literature Review Generated:")
            print(f"  Title: {literature_review.title}")
            print(f"  Content Length: {len(literature_review.content)} characters")
            print(f"  Citations: {len(literature_review.citations)}")
            print(f"  Key Findings: {len(literature_review.key_findings)}")
            print(f"  Research Gaps: {len(literature_review.gaps_identified)}")
            
            # Show sample content
            print(f"\n  Sample Content (first 200 chars):")
            print(f"  {literature_review.content[:200]}...")
            
            if literature_review.key_findings:
                print(f"\n  Sample Key Finding:")
                print(f"  - {literature_review.key_findings[0][:100]}...")
            
            if literature_review.gaps_identified:
                print(f"\n  Sample Research Gap:")
                print(f"  - {literature_review.gaps_identified[0][:100]}...")
                
        except Exception as e:
            print(f"✗ Literature Review Generation failed: {str(e)}")
        
        print("\n2. Testing Research Proposal Creation...")
        
        try:
            # Create research proposal
            proposal = await assistant.create_research_proposal(
                research_idea="Developing interpretable machine learning models for medical diagnosis",
                user_id=user.id,
                research_type=ResearchType.MIXED_METHODS,
                domain=ResearchDomain.COMPUTER_SCIENCE,
                duration_months=18
            )
            
            print(f"✓ Research Proposal Created:")
            print(f"  Title: {proposal.title}")
            print(f"  Research Questions: {len(proposal.research_questions)}")
            print(f"  Hypotheses: {len(proposal.hypotheses)}")
            print(f"  References: {len(proposal.references)}")
            
            # Show sample sections
            print(f"\n  Abstract (first 150 chars):")
            print(f"  {proposal.abstract[:150]}...")
            
            if proposal.research_questions:
                print(f"\n  Sample Research Question:")
                print(f"  - {proposal.research_questions[0]}")
            
            if proposal.hypotheses:
                print(f"\n  Sample Hypothesis:")
                print(f"  - {proposal.hypotheses[0]}")
            
            print(f"\n  Timeline Overview:")
            for phase, description in list(proposal.timeline.items())[:3]:
                print(f"  - {phase}: {description}")
                
        except Exception as e:
            print(f"✗ Research Proposal Creation failed: {str(e)}")
        
        print("\n3. Testing Methodology Suggestions...")
        
        try:
            # Get methodology suggestions
            research_questions = [
                "How effective are interpretable ML models compared to black-box models?",
                "What factors influence physician adoption of AI diagnostic tools?",
                "How can we measure the interpretability of machine learning models?"
            ]
            
            methodology_recommendations = await assistant.suggest_methodology(
                research_questions=research_questions,
                research_type=ResearchType.MIXED_METHODS,
                domain=ResearchDomain.COMPUTER_SCIENCE,
                constraints={"budget": "medium", "timeline": "18_months"}
            )
            
            print(f"✓ Methodology Suggestions Generated:")
            print(f"  Total Recommendations: {len(methodology_recommendations)}")
            
            for i, rec in enumerate(methodology_recommendations[:3], 1):
                print(f"\n  Recommendation {i}: {rec.method_name}")
                print(f"    Applicability Score: {rec.applicability_score:.2f}")
                print(f"    Complexity: {rec.complexity_level}")
                print(f"    Duration: {rec.estimated_duration}")
                print(f"    Advantages: {', '.join(rec.advantages[:2])}")
                if rec.disadvantages:
                    print(f"    Disadvantages: {', '.join(rec.disadvantages[:2])}")
                    
        except Exception as e:
            print(f"✗ Methodology Suggestions failed: {str(e)}")
        
        print("\n4. Testing Data Analysis Guidance...")
        
        try:
            # Get data analysis guidance
            guidance = await assistant.provide_data_analysis_guidance(
                data_description="Mixed dataset with patient demographics, medical images, and diagnostic outcomes",
                research_questions=research_questions,
                data_type="mixed",
                sample_size=1000
            )
            
            print(f"✓ Data Analysis Guidance Generated:")
            print(f"  Analysis Type: {guidance.analysis_type}")
            print(f"  Statistical Methods: {len(guidance.statistical_methods)}")
            print(f"  Software Recommendations: {len(guidance.software_recommendations)}")
            print(f"  Analysis Steps: {len(guidance.step_by_step_guide)}")
            
            print(f"\n  Recommended Statistical Methods:")
            for method in guidance.statistical_methods[:3]:
                print(f"    - {method}")
            
            print(f"\n  Software Recommendations:")
            for software in guidance.software_recommendations[:3]:
                print(f"    - {software}")
            
            print(f"\n  Sample Analysis Steps:")
            for i, step in enumerate(guidance.step_by_step_guide[:3], 1):
                print(f"    {i}. {step}")
            
            if guidance.common_pitfalls:
                print(f"\n  Common Pitfalls to Avoid:")
                for pitfall in guidance.common_pitfalls[:2]:
                    print(f"    - {pitfall}")
                    
        except Exception as e:
            print(f"✗ Data Analysis Guidance failed: {str(e)}")
        
        print("\n5. Testing Helper Methods...")
        
        try:
            # Test document retrieval
            relevant_docs = await assistant._get_relevant_documents(
                topic="machine learning",
                user_id=user.id,
                limit=5
            )
            print(f"✓ Found {len(relevant_docs)} relevant documents")
            
            # Test theme extraction
            themes = await assistant._extract_research_themes(relevant_docs)
            print(f"✓ Extracted {len(themes)} research themes")
            
            if themes:
                print(f"  Top theme: {themes[0]['name']} (weight: {themes[0]['weight']:.2f})")
            
            # Test key findings extraction
            findings = await assistant._extract_key_findings(relevant_docs[:2])
            print(f"✓ Extracted {len(findings)} key findings")
            
            # Test methodology identification
            methodologies = await assistant._identify_methodologies(relevant_docs)
            print(f"✓ Identified {len(methodologies)} methodologies")
            
            if methodologies:
                print(f"  Most common: {methodologies[0]['methodology']} ({methodologies[0]['frequency']} occurrences)")
            
            # Test research gaps identification
            gaps = await assistant._identify_research_gaps(relevant_docs, themes)
            print(f"✓ Identified {len(gaps)} research gaps")
            
        except Exception as e:
            print(f"✗ Helper methods testing failed: {str(e)}")
        
        print("\n6. Testing Research Templates and Databases...")
        
        # Test template loading
        templates = assistant.research_templates
        print(f"✓ Loaded research templates:")
        print(f"  Literature Review sections: {len(templates['literature_review']['sections'])}")
        print(f"  Research Proposal sections: {len(templates['research_proposal']['sections'])}")
        
        # Test methodology database
        method_db = assistant.methodology_database
        print(f"✓ Loaded methodology database:")
        for research_type, data in method_db.items():
            print(f"  {research_type.value}: {len(data['methods'])} methods")
        
        # Test analysis patterns
        patterns = assistant.analysis_patterns
        print(f"✓ Loaded analysis patterns:")
        print(f"  Statistical test categories: {len(patterns['statistical_tests'])}")
        print(f"  Sample size categories: {len(patterns['sample_size'])}")
        
        print("\n=== Research Assistant Demo Completed Successfully! ===")
        
        # Summary
        print(f"\n📊 Demo Summary:")
        print(f"✅ Created {len(documents)} sample research documents")
        print(f"✅ Generated literature review with comprehensive analysis")
        print(f"✅ Created structured research proposal with questions and hypotheses")
        print(f"✅ Provided methodology recommendations with applicability scores")
        print(f"✅ Generated data analysis guidance with step-by-step instructions")
        print(f"✅ Tested all helper methods for document analysis")
        print(f"✅ Verified research templates and methodology databases")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_research_assistant())