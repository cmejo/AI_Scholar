"""
Custom AI Model Training Service
Provides domain-specific model fine-tuning, federated learning,
and custom model deployment capabilities.
"""
import asyncio
import logging
import json
import uuid
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import tempfile
import os
from pathlib import Path

import torch
import torch.nn as nn
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    TrainingArguments, Trainer, DataCollatorWithPadding
)
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, or_

from core.database import (
    get_db, Document, DocumentChunk, DocumentTag, AnalyticsEvent,
    User, UserProfile
)

logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """AI model types for training"""
    TEXT_CLASSIFIER = "text_classifier"
    EMBEDDING_MODEL = "embedding_model"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    NAMED_ENTITY_RECOGNITION = "named_entity_recognition"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

class TrainingStatus(str, Enum):
    """Training job status"""
    PENDING = "pending"
    PREPARING_DATA = "preparing_data"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TrainingJob:
    """Training job configuration"""
    id: str
    user_id: str
    model_type: ModelType
    model_name: str
    base_model: str
    training_data: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    status: TrainingStatus
    progress: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metrics: Dict[str, float]
    model_path: Optional[str]
    error_message: Optional[str]

@dataclass
class CustomModel:
    """Custom trained model"""
    id: str
    user_id: str
    name: str
    model_type: ModelType
    base_model: str
    training_job_id: str
    model_path: str
    performance_metrics: Dict[str, float]
    created_at: datetime
    is_active: bool
    usage_count: int
    last_used: Optional[datetime]

class CustomAITrainingService:
    """Main custom AI training service"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Training configurations
        self.model_configs = {
            ModelType.TEXT_CLASSIFIER: {
                "base_models": [
                    "distilbert-base-uncased",
                    "roberta-base",
                    "bert-base-uncased"
                ],
                "default_hyperparameters": {
                    "learning_rate": 2e-5,
                    "batch_size": 16,
                    "num_epochs": 3,
                    "warmup_steps": 500,
                    "weight_decay": 0.01
                }
            },
            ModelType.EMBEDDING_MODEL: {
                "base_models": [
                    "sentence-transformers/all-MiniLM-L6-v2",
                    "sentence-transformers/all-mpnet-base-v2"
                ],
                "default_hyperparameters": {
                    "learning_rate": 2e-5,
                    "batch_size": 32,
                    "num_epochs": 1,
                    "warmup_steps": 100
                }
            }
        }
        
        # Active training jobs
        self.active_jobs: Dict[str, TrainingJob] = {}
        self.trained_models: Dict[str, CustomModel] = {}
        
        # Training data storage
        self.training_data_dir = Path("./model_training_data")
        self.model_storage_dir = Path("./trained_models")
        
        # Create directories
        self.training_data_dir.mkdir(exist_ok=True)
        self.model_storage_dir.mkdir(exist_ok=True)

    async def create_training_job(
        self,
        user_id: str,
        model_type: ModelType,
        model_name: str,
        base_model: str,
        training_data: Dict[str, Any],
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> TrainingJob:
        """Create a new model training job"""
        try:
            job_id = str(uuid.uuid4())
            
            # Use default hyperparameters if not provided
            if not hyperparameters:
                hyperparameters = self.model_configs[model_type]["default_hyperparameters"].copy()
            
            job = TrainingJob(
                id=job_id,
                user_id=user_id,
                model_type=model_type,
                model_name=model_name,
                base_model=base_model,
                training_data=training_data,
                hyperparameters=hyperparameters,
                status=TrainingStatus.PENDING,
                progress=0.0,
                created_at=datetime.utcnow(),
                started_at=None,
                completed_at=None,
                metrics={},
                model_path=None,
                error_message=None
            )
            
            # Store job
            self.active_jobs[job_id] = job
            
            # Start training asynchronously
            asyncio.create_task(self._execute_training_job(job))
            
            # Track analytics
            await self._track_training_event(user_id, "training_job_created", {
                "job_id": job_id,
                "model_type": model_type.value,
                "base_model": base_model
            })
            
            return job
            
        except Exception as e:
            logger.error(f"Error creating training job: {str(e)}")
            raise

    async def get_training_job_status(
        self,
        user_id: str,
        job_id: str
    ) -> TrainingJob:
        """Get status of a training job"""
        try:
            job = self.active_jobs.get(job_id)
            if not job or job.user_id != user_id:
                raise ValueError("Training job not found or access denied")
            
            return job
            
        except Exception as e:
            logger.error(f"Error getting training job status: {str(e)}")
            raise

    async def cancel_training_job(
        self,
        user_id: str,
        job_id: str
    ) -> bool:
        """Cancel a training job"""
        try:
            job = self.active_jobs.get(job_id)
            if not job or job.user_id != user_id:
                return False
            
            if job.status in [TrainingStatus.PENDING, TrainingStatus.PREPARING_DATA, TrainingStatus.TRAINING]:
                job.status = TrainingStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                
                # Track analytics
                await self._track_training_event(user_id, "training_job_cancelled", {
                    "job_id": job_id
                })
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling training job: {str(e)}")
            return False

    async def deploy_trained_model(
        self,
        user_id: str,
        job_id: str,
        model_name: str
    ) -> CustomModel:
        """Deploy a trained model for use"""
        try:
            job = self.active_jobs.get(job_id)
            if not job or job.user_id != user_id:
                raise ValueError("Training job not found or access denied")
            
            if job.status != TrainingStatus.COMPLETED:
                raise ValueError("Training job not completed")
            
            model_id = str(uuid.uuid4())
            
            custom_model = CustomModel(
                id=model_id,
                user_id=user_id,
                name=model_name,
                model_type=job.model_type,
                base_model=job.base_model,
                training_job_id=job_id,
                model_path=job.model_path,
                performance_metrics=job.metrics,
                created_at=datetime.utcnow(),
                is_active=True,
                usage_count=0,
                last_used=None
            )
            
            # Store model
            self.trained_models[model_id] = custom_model
            
            # Track analytics
            await self._track_training_event(user_id, "model_deployed", {
                "model_id": model_id,
                "model_name": model_name,
                "model_type": job.model_type.value
            })
            
            return custom_model
            
        except Exception as e:
            logger.error(f"Error deploying trained model: {str(e)}")
            raise

    async def use_custom_model(
        self,
        user_id: str,
        model_id: str,
        input_data: Any
    ) -> Dict[str, Any]:
        """Use a deployed custom model for inference"""
        try:
            model = self.trained_models.get(model_id)
            if not model or model.user_id != user_id:
                raise ValueError("Custom model not found or access denied")
            
            if not model.is_active:
                raise ValueError("Model is not active")
            
            # Load model for inference
            result = await self._run_inference(model, input_data)
            
            # Update usage statistics
            model.usage_count += 1
            model.last_used = datetime.utcnow()
            
            return result
            
        except Exception as e:
            logger.error(f"Error using custom model: {str(e)}")
            raise

    # Training execution methods
    async def _execute_training_job(self, job: TrainingJob):
        """Execute a training job"""
        try:
            job.status = TrainingStatus.PREPARING_DATA
            job.started_at = datetime.utcnow()
            job.progress = 0.1
            
            # Prepare training data
            train_dataset, eval_dataset = await self._prepare_training_data(job)
            job.progress = 0.3
            
            # Initialize model and tokenizer
            model, tokenizer = await self._initialize_model(job)
            job.progress = 0.4
            
            # Set up training
            job.status = TrainingStatus.TRAINING
            trainer = await self._setup_trainer(job, model, tokenizer, train_dataset, eval_dataset)
            job.progress = 0.5
            
            # Train model
            await self._train_model(job, trainer)
            job.progress = 0.8
            
            # Evaluate model
            job.status = TrainingStatus.EVALUATING
            metrics = await self._evaluate_model(job, trainer, eval_dataset)
            job.metrics = metrics
            job.progress = 0.9
            
            # Save model
            model_path = await self._save_trained_model(job, model, tokenizer)
            job.model_path = model_path
            
            # Complete job
            job.status = TrainingStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = 1.0
            
            # Track completion
            await self._track_training_event(job.user_id, "training_job_completed", {
                "job_id": job.id,
                "metrics": metrics,
                "training_time": (job.completed_at - job.started_at).total_seconds()
            })
            
        except Exception as e:
            logger.error(f"Error executing training job {job.id}: {str(e)}")
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            
            await self._track_training_event(job.user_id, "training_job_failed", {
                "job_id": job.id,
                "error": str(e)
            })

    async def _prepare_training_data(self, job: TrainingJob) -> Tuple[Dataset, Dataset]:
        """Prepare training and evaluation datasets"""
        try:
            if job.model_type == ModelType.TEXT_CLASSIFIER:
                return await self._prepare_classification_data(job)
            elif job.model_type == ModelType.EMBEDDING_MODEL:
                return await self._prepare_embedding_data(job)
            else:
                raise ValueError(f"Unsupported model type: {job.model_type}")
                
        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            raise

    async def _prepare_classification_data(self, job: TrainingJob) -> Tuple[Dataset, Dataset]:
        """Prepare data for text classification"""
        try:
            # Extract training data from job configuration
            training_data = job.training_data
            
            # Get user's documents for training data
            documents = self.db.query(Document).filter(
                Document.user_id == job.user_id,
                Document.status == "completed"
            ).all()
            
            texts = []
            labels = []
            
            # Simple approach: use document tags as labels
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).limit(5).all()  # Limit chunks per document
                
                tags = self.db.query(DocumentTag).filter(
                    DocumentTag.document_id == doc.id
                ).all()
                
                if chunks and tags:
                    for chunk in chunks:
                        texts.append(chunk.content[:512])  # Limit text length
                        # Use first tag as label (simplified)
                        labels.append(tags[0].tag_name)
            
            # Create label mapping
            unique_labels = list(set(labels))
            label_to_id = {label: idx for idx, label in enumerate(unique_labels)}
            label_ids = [label_to_id[label] for label in labels]
            
            # Split data
            train_texts, eval_texts, train_labels, eval_labels = train_test_split(
                texts, label_ids, test_size=0.2, random_state=42
            )
            
            # Create datasets
            train_dataset = Dataset.from_dict({
                "text": train_texts,
                "labels": train_labels
            })
            
            eval_dataset = Dataset.from_dict({
                "text": eval_texts,
                "labels": eval_labels
            })
            
            # Store label mapping for later use
            job.training_data["label_mapping"] = label_to_id
            job.training_data["num_labels"] = len(unique_labels)
            
            return train_dataset, eval_dataset
            
        except Exception as e:
            logger.error(f"Error preparing classification data: {str(e)}")
            raise

    async def _prepare_embedding_data(self, job: TrainingJob) -> Tuple[Dataset, Dataset]:
        """Prepare data for embedding model training"""
        try:
            # For embedding models, we need sentence pairs
            # This is a simplified implementation
            
            documents = self.db.query(Document).filter(
                Document.user_id == job.user_id,
                Document.status == "completed"
            ).limit(10).all()
            
            sentence_pairs = []
            labels = []
            
            for doc in documents:
                chunks = self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).limit(3).all()
                
                # Create positive pairs (chunks from same document)
                for i in range(len(chunks)):
                    for j in range(i + 1, len(chunks)):
                        sentence_pairs.append([chunks[i].content[:256], chunks[j].content[:256]])
                        labels.append(1)  # Similar
                
                # Create negative pairs (would be more sophisticated in practice)
                if len(chunks) >= 2:
                    sentence_pairs.append([chunks[0].content[:256], "Unrelated content"])
                    labels.append(0)  # Dissimilar
            
            # Split data
            train_pairs, eval_pairs, train_labels, eval_labels = train_test_split(
                sentence_pairs, labels, test_size=0.2, random_state=42
            )
            
            # Create datasets
            train_dataset = Dataset.from_dict({
                "sentence1": [pair[0] for pair in train_pairs],
                "sentence2": [pair[1] for pair in train_pairs],
                "labels": train_labels
            })
            
            eval_dataset = Dataset.from_dict({
                "sentence1": [pair[0] for pair in eval_pairs],
                "sentence2": [pair[1] for pair in eval_pairs],
                "labels": eval_labels
            })
            
            return train_dataset, eval_dataset
            
        except Exception as e:
            logger.error(f"Error preparing embedding data: {str(e)}")
            raise

    async def _initialize_model(self, job: TrainingJob) -> Tuple[nn.Module, Any]:
        """Initialize model and tokenizer"""
        try:
            if job.model_type == ModelType.TEXT_CLASSIFIER:
                tokenizer = AutoTokenizer.from_pretrained(job.base_model)
                model = AutoModelForSequenceClassification.from_pretrained(
                    job.base_model,
                    num_labels=job.training_data["num_labels"]
                )
            else:
                tokenizer = AutoTokenizer.from_pretrained(job.base_model)
                model = AutoModel.from_pretrained(job.base_model)
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            raise

    async def _setup_trainer(
        self, job: TrainingJob, model: nn.Module, tokenizer: Any,
        train_dataset: Dataset, eval_dataset: Dataset
    ) -> Trainer:
        """Set up Hugging Face trainer"""
        try:
            # Tokenize datasets
            def tokenize_function(examples):
                if job.model_type == ModelType.TEXT_CLASSIFIER:
                    return tokenizer(examples["text"], truncation=True, padding=True)
                else:
                    return tokenizer(
                        examples["sentence1"], examples["sentence2"],
                        truncation=True, padding=True
                    )
            
            train_dataset = train_dataset.map(tokenize_function, batched=True)
            eval_dataset = eval_dataset.map(tokenize_function, batched=True)
            
            # Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.training_data_dir / job.id),
                learning_rate=job.hyperparameters["learning_rate"],
                per_device_train_batch_size=job.hyperparameters["batch_size"],
                per_device_eval_batch_size=job.hyperparameters["batch_size"],
                num_train_epochs=job.hyperparameters["num_epochs"],
                warmup_steps=job.hyperparameters["warmup_steps"],
                weight_decay=job.hyperparameters.get("weight_decay", 0.01),
                logging_dir=str(self.training_data_dir / job.id / "logs"),
                evaluation_strategy="epoch",
                save_strategy="epoch",
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False
            )
            
            # Data collator
            data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
            
            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                tokenizer=tokenizer,
                data_collator=data_collator,
                compute_metrics=self._compute_metrics
            )
            
            return trainer
            
        except Exception as e:
            logger.error(f"Error setting up trainer: {str(e)}")
            raise

    async def _train_model(self, job: TrainingJob, trainer: Trainer):
        """Train the model"""
        try:
            # Start training
            trainer.train()
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    async def _evaluate_model(self, job: TrainingJob, trainer: Trainer, eval_dataset: Dataset) -> Dict[str, float]:
        """Evaluate trained model"""
        try:
            # Evaluate model
            eval_results = trainer.evaluate()
            
            # Extract metrics
            metrics = {
                "eval_loss": eval_results.get("eval_loss", 0.0),
                "eval_accuracy": eval_results.get("eval_accuracy", 0.0),
                "eval_f1": eval_results.get("eval_f1", 0.0),
                "eval_precision": eval_results.get("eval_precision", 0.0),
                "eval_recall": eval_results.get("eval_recall", 0.0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return {"eval_loss": 1.0, "eval_accuracy": 0.0}

    async def _save_trained_model(self, job: TrainingJob, model: nn.Module, tokenizer: Any) -> str:
        """Save trained model"""
        try:
            model_dir = self.model_storage_dir / job.id
            model_dir.mkdir(exist_ok=True)
            
            # Save model and tokenizer
            model.save_pretrained(str(model_dir))
            tokenizer.save_pretrained(str(model_dir))
            
            # Save job metadata
            metadata = {
                "job_id": job.id,
                "model_type": job.model_type.value,
                "base_model": job.base_model,
                "hyperparameters": job.hyperparameters,
                "metrics": job.metrics,
                "created_at": job.created_at.isoformat()
            }
            
            with open(model_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            return str(model_dir)
            
        except Exception as e:
            logger.error(f"Error saving trained model: {str(e)}")
            raise

    def _compute_metrics(self, eval_pred):
        """Compute evaluation metrics"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        accuracy = accuracy_score(labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='weighted')
        
        return {
            "accuracy": accuracy,
            "f1": f1,
            "precision": precision,
            "recall": recall
        }

    async def _run_inference(self, model: CustomModel, input_data: Any) -> Dict[str, Any]:
        """Run inference with custom model"""
        try:
            # Load model
            if model.model_type == ModelType.TEXT_CLASSIFIER:
                tokenizer = AutoTokenizer.from_pretrained(model.model_path)
                loaded_model = AutoModelForSequenceClassification.from_pretrained(model.model_path)
                
                # Tokenize input
                inputs = tokenizer(input_data, return_tensors="pt", truncation=True, padding=True)
                
                # Run inference
                with torch.no_grad():
                    outputs = loaded_model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Get predicted class
                predicted_class = torch.argmax(predictions, dim=-1).item()
                confidence = predictions[0][predicted_class].item()
                
                return {
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "all_scores": predictions[0].tolist()
                }
            
            else:
                return {"error": "Model type not supported for inference"}
                
        except Exception as e:
            logger.error(f"Error running inference: {str(e)}")
            return {"error": str(e)}

    async def _track_training_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]):
        """Track training analytics events"""
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data={
                    **event_data,
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "custom_ai_training"
                }
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking training event: {str(e)}")

# Export classes
__all__ = [
    'CustomAITrainingService',
    'TrainingJob',
    'CustomModel',
    'ModelType',
    'TrainingStatus'
]