"""
Celery tasks for AI fine-tuning and model management
"""

import os
import json
import logging
import subprocess
from datetime import datetime
from celery import Celery, Task
from pathlib import Path

# Configure Celery
broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('fine_tuning_tasks', broker=broker_url, backend=result_backend)

logger = logging.getLogger(__name__)

class LoggingTask(Task):
    """Task base class with logging"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] succeeded: {retval}")
        return super().on_success(retval, task_id, args, kwargs)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
        return super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(base=LoggingTask, bind=True, max_retries=3)
def run_dpo_training_task(self, job_id, dataset_file, base_model, training_config):
    """
    Run DPO (Direct Preference Optimization) fine-tuning
    """
    try:
        # Import here to avoid circular imports
        from models import db, FineTuningJob
        from app_enterprise import app
        
        with app.app_context():
            # Get job record
            job = FineTuningJob.query.get(job_id)
            if not job:
                raise Exception(f"Job not found: {job_id}")
            
            # Update job status
            job.status = 'running'
            job.started_at = datetime.utcnow()
            db.session.commit()
            
            try:
                # Run DPO training
                result = self._run_dpo_training(
                    job_id=job_id,
                    dataset_file=dataset_file,
                    base_model=base_model,
                    training_config=training_config
                )
                
                # Update job with results
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.model_path = result.get('model_path')
                job.metrics = result.get('metrics')
                db.session.commit()
                
                logger.info(f"DPO training completed for job {job_id}")
                
                return {
                    'success': True,
                    'job_id': job_id,
                    'model_path': result.get('model_path'),
                    'metrics': result.get('metrics')
                }
                
            except Exception as e:
                # Update job with error
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.session.commit()
                
                logger.error(f"DPO training failed for job {job_id}: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Error in DPO training task: {e}")
        
        # Retry with exponential backoff
        retry_in = 60 * (2 ** self.request.retries)
        self.retry(exc=e, countdown=retry_in)
        
        return {'success': False, 'error': str(e)}

def _run_dpo_training(job_id, dataset_file, base_model, training_config):
    """Run the actual DPO training process"""
    try:
        # Create output directory
        output_dir = Path(f"fine_tuned_models/job_{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we have the required libraries
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            from trl import DPOTrainer, DPOConfig
            from datasets import Dataset
            import pandas as pd
        except ImportError as e:
            raise Exception(f"Required libraries not installed: {e}. Install with: pip install torch transformers trl datasets")
        
        # Load dataset
        dataset_df = pd.read_json(dataset_file, lines=True)
        dataset = Dataset.from_pandas(dataset_df)
        
        # Map model names to HuggingFace model paths
        model_mapping = {
            'llama2:7b-chat': 'meta-llama/Llama-2-7b-chat-hf',
            'llama2:13b-chat': 'meta-llama/Llama-2-13b-chat-hf',
            'mistral:7b': 'mistralai/Mistral-7B-Instruct-v0.1',
            'codellama:7b': 'codellama/CodeLlama-7b-Instruct-hf'
        }
        
        model_name = model_mapping.get(base_model, base_model)
        
        # Load model and tokenizer
        logger.info(f"Loading model: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        # Prepare DPO configuration
        dpo_config = DPOConfig(
            output_dir=str(output_dir),
            learning_rate=training_config.get('learning_rate', 5e-5),
            per_device_train_batch_size=training_config.get('batch_size', 4),
            num_train_epochs=training_config.get('num_epochs', 3),
            max_length=training_config.get('max_length', 512),
            beta=training_config.get('beta', 0.1),
            save_steps=training_config.get('save_steps', 500),
            eval_steps=training_config.get('eval_steps', 500),
            logging_steps=training_config.get('logging_steps', 100),
            gradient_accumulation_steps=training_config.get('gradient_accumulation_steps', 4),
            warmup_steps=training_config.get('warmup_steps', 100),
            remove_unused_columns=False,
            run_name=f"dpo_job_{job_id}"
        )
        
        # Initialize DPO trainer
        trainer = DPOTrainer(
            model=model,
            args=dpo_config,
            train_dataset=dataset,
            tokenizer=tokenizer,
            max_length=training_config.get('max_length', 512),
            max_prompt_length=training_config.get('max_prompt_length', 256),
            max_target_length=training_config.get('max_target_length', 256)
        )
        
        # Start training
        logger.info(f"Starting DPO training for job {job_id}")
        trainer.train()
        
        # Save the fine-tuned model
        model_path = output_dir / "final_model"
        trainer.save_model(str(model_path))
        tokenizer.save_pretrained(str(model_path))
        
        # Get training metrics
        metrics = {}
        if hasattr(trainer.state, 'log_history'):
            # Extract final metrics
            final_log = trainer.state.log_history[-1] if trainer.state.log_history else {}
            metrics = {
                'final_loss': final_log.get('train_loss'),
                'total_steps': trainer.state.global_step,
                'epochs_completed': trainer.state.epoch
            }
        
        logger.info(f"DPO training completed for job {job_id}")
        
        return {
            'model_path': str(model_path),
            'metrics': metrics,
            'training_config': training_config
        }
        
    except Exception as e:
        logger.error(f"Error in DPO training: {e}")
        raise

@celery_app.task(base=LoggingTask, bind=True)
def prepare_feedback_dataset_task(self, min_feedback_pairs=100, days=30):
    """
    Prepare preference dataset from user feedback
    """
    try:
        from services.fine_tuning_service import fine_tuning_service
        from app_enterprise import app
        
        with app.app_context():
            result = fine_tuning_service.prepare_dpo_dataset_from_feedback(
                min_feedback_pairs=min_feedback_pairs,
                days=days
            )
            
            return result
            
    except Exception as e:
        logger.error(f"Error preparing feedback dataset: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask, bind=True)
def evaluate_rag_response_task(self, message_id, query, retrieved_contexts, response):
    """
    Asynchronously evaluate RAG response quality
    """
    try:
        from services.rag_evaluation_service import rag_evaluation_service
        from app_enterprise import app
        
        with app.app_context():
            result = rag_evaluation_service.evaluate_rag_response(
                query=query,
                retrieved_contexts=retrieved_contexts,
                response=response,
                message_id=message_id
            )
            
            return result
            
    except Exception as e:
        logger.error(f"Error evaluating RAG response: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def deploy_fine_tuned_model_task(job_id, model_path):
    """
    Deploy fine-tuned model to Ollama
    """
    try:
        from models import db, FineTuningJob
        from app_enterprise import app
        
        with app.app_context():
            job = FineTuningJob.query.get(job_id)
            if not job:
                raise Exception(f"Job not found: {job_id}")
            
            # Create Ollama model file
            model_name = f"ai_scholar_ft_{job_id}"
            
            # Create Modelfile for Ollama
            modelfile_content = f"""
FROM {job.base_model}

# Fine-tuned model from job {job_id}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM You are AI Scholar, a helpful AI assistant fine-tuned on user feedback to provide better responses.
"""
            
            modelfile_path = Path(model_path) / "Modelfile"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            # Import model to Ollama
            import subprocess
            result = subprocess.run([
                'ollama', 'create', model_name, '-f', str(modelfile_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully deployed model {model_name} to Ollama")
                return {
                    'success': True,
                    'model_name': model_name,
                    'deployment_time': datetime.utcnow().isoformat()
                }
            else:
                raise Exception(f"Failed to deploy model: {result.stderr}")
                
    except Exception as e:
        logger.error(f"Error deploying fine-tuned model: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def weekly_model_improvement_task():
    """
    Weekly task to check for model improvement opportunities
    """
    try:
        from services.fine_tuning_service import fine_tuning_service
        from app_enterprise import app
        
        with app.app_context():
            # Get feedback statistics
            stats = fine_tuning_service.get_feedback_statistics(days=7)
            
            if stats['success'] and stats['ready_for_fine_tuning']:
                # Prepare dataset
                dataset_result = fine_tuning_service.prepare_dpo_dataset_from_feedback(
                    min_feedback_pairs=100,
                    days=7
                )
                
                if dataset_result['success']:
                    # Start fine-tuning job
                    job_result = fine_tuning_service.start_dpo_fine_tuning(
                        dataset_file=dataset_result['dataset_file'],
                        base_model='llama2:7b-chat'
                    )
                    
                    logger.info(f"Weekly model improvement started: {job_result}")
                    return job_result
                else:
                    logger.info(f"Dataset preparation failed: {dataset_result}")
                    return dataset_result
            else:
                logger.info("Not enough feedback for weekly model improvement")
                return {
                    'success': True,
                    'message': 'Insufficient feedback for model improvement',
                    'stats': stats
                }
                
    except Exception as e:
        logger.error(f"Error in weekly model improvement: {e}")
        return {'success': False, 'error': str(e)}

@celery_app.task(base=LoggingTask)
def model_performance_monitoring_task():
    """
    Monitor model performance and quality metrics
    """
    try:
        from services.rag_evaluation_service import rag_evaluation_service
        from models import db, ModelPerformanceTracking
        from app_enterprise import app
        
        with app.app_context():
            # Get RAG evaluation statistics
            rag_stats = rag_evaluation_service.get_evaluation_statistics(days=7)
            
            if rag_stats['success']:
                # Log performance metrics
                for metric_name, value in rag_stats['average_scores'].items():
                    performance_record = ModelPerformanceTracking(
                        model_name='current_rag_pipeline',
                        version='1.0',
                        metric_name=f'rag_{metric_name}',
                        metric_value=value,
                        evaluation_date=datetime.utcnow(),
                        benchmark_value=0.8,  # Target benchmark
                        evaluation_data=rag_stats
                    )
                    db.session.add(performance_record)
                
                db.session.commit()
                
                logger.info("Model performance monitoring completed")
                return {
                    'success': True,
                    'metrics_logged': len(rag_stats['average_scores']),
                    'rag_stats': rag_stats
                }
            else:
                return rag_stats
                
    except Exception as e:
        logger.error(f"Error in model performance monitoring: {e}")
        return {'success': False, 'error': str(e)}

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'weekly-model-improvement': {
        'task': 'tasks.fine_tuning_tasks.weekly_model_improvement_task',
        'schedule': 604800.0,  # Run weekly (7 days)
    },
    'daily-performance-monitoring': {
        'task': 'tasks.fine_tuning_tasks.model_performance_monitoring_task',
        'schedule': 86400.0,  # Run daily
    },
}

celery_app.conf.timezone = 'UTC'