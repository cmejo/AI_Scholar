"""
Model management and deployment for the RL system.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import torch
import json
import shutil

from ..core.config import RLConfig
from ..networks.policy_network import PolicyNetwork
from ..networks.value_network import ValueNetwork

logger = logging.getLogger(__name__)


@dataclass
class ModelVersion:
    """Represents a model version."""
    version_id: str
    model_type: str  # 'policy' or 'value'
    version_number: int
    file_path: str
    performance_metrics: Dict[str, float]
    created_at: datetime
    is_active: bool = False
    is_production: bool = False


class ModelManager:
    """Manages model versions and deployments."""
    
    def __init__(self, config: RLConfig):
        self.config = config
        self.model_storage_path = Path(config.model_storage_path)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)
        
        self.policy_versions: List[ModelVersion] = []
        self.value_versions: List[ModelVersion] = []
        self.active_policy_version: Optional[ModelVersion] = None
        self.active_value_version: Optional[ModelVersion] = None
    
    async def save_model(
        self,
        model: torch.nn.Module,
        model_type: str,
        performance_metrics: Dict[str, float],
        version_notes: str = ""
    ) -> ModelVersion:
        """Save a model version."""
        
        # Generate version info
        existing_versions = (
            self.policy_versions if model_type == 'policy' else self.value_versions
        )
        version_number = len(existing_versions) + 1
        version_id = f"{model_type}_v{version_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create file path
        file_path = self.model_storage_path / f"{version_id}.pt"
        
        # Save model
        torch.save({
            'model_state_dict': model.state_dict(),
            'model_type': model_type,
            'version_number': version_number,
            'performance_metrics': performance_metrics,
            'config': self.config.network,
            'created_at': datetime.now().isoformat(),
            'version_notes': version_notes
        }, file_path)
        
        # Create version record
        model_version = ModelVersion(
            version_id=version_id,
            model_type=model_type,
            version_number=version_number,
            file_path=str(file_path),
            performance_metrics=performance_metrics,
            created_at=datetime.now()
        )
        
        # Add to appropriate list
        if model_type == 'policy':
            self.policy_versions.append(model_version)
        else:
            self.value_versions.append(model_version)
        
        logger.info(f"Saved {model_type} model version {version_id}")
        return model_version
    
    async def load_model(
        self,
        version_id: str,
        model_class: type
    ) -> torch.nn.Module:
        """Load a model version."""
        
        # Find version
        model_version = self._find_version(version_id)
        if not model_version:
            raise ValueError(f"Model version {version_id} not found")
        
        # Load checkpoint
        checkpoint = torch.load(model_version.file_path, map_location='cpu')
        
        # Create model instance
        model = model_class(checkpoint['config'])
        model.load_state_dict(checkpoint['model_state_dict'])
        
        logger.info(f"Loaded model version {version_id}")
        return model
    
    async def set_active_version(self, version_id: str) -> bool:
        """Set a model version as active."""
        
        model_version = self._find_version(version_id)
        if not model_version:
            return False
        
        # Deactivate current active version
        if model_version.model_type == 'policy':
            if self.active_policy_version:
                self.active_policy_version.is_active = False
            self.active_policy_version = model_version
        else:
            if self.active_value_version:
                self.active_value_version.is_active = False
            self.active_value_version = model_version
        
        model_version.is_active = True
        logger.info(f"Set {version_id} as active {model_version.model_type} model")
        return True
    
    async def deploy_to_production(self, version_id: str) -> bool:
        """Deploy a model version to production."""
        
        model_version = self._find_version(version_id)
        if not model_version:
            return False
        
        # Validation checks
        if not self._validate_for_production(model_version):
            logger.error(f"Model {version_id} failed production validation")
            return False
        
        # Mark as production
        model_version.is_production = True
        
        # Copy to production directory
        prod_path = self.model_storage_path / "production" / f"{model_version.model_type}_current.pt"
        prod_path.parent.mkdir(exist_ok=True)
        shutil.copy2(model_version.file_path, prod_path)
        
        logger.info(f"Deployed {version_id} to production")
        return True
    
    def _find_version(self, version_id: str) -> Optional[ModelVersion]:
        """Find a model version by ID."""
        
        all_versions = self.policy_versions + self.value_versions
        for version in all_versions:
            if version.version_id == version_id:
                return version
        return None
    
    def _validate_for_production(self, model_version: ModelVersion) -> bool:
        """Validate model for production deployment."""
        
        # Check performance thresholds
        metrics = model_version.performance_metrics
        
        if model_version.model_type == 'policy':
            # Policy model validation
            if metrics.get('average_reward', 0) < 0.5:
                return False
            if metrics.get('safety_score', 0) < 0.8:
                return False
        else:
            # Value model validation
            if metrics.get('value_accuracy', 0) < 0.7:
                return False
        
        # Check file exists and is valid
        if not Path(model_version.file_path).exists():
            return False
        
        return True
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get model management statistics."""
        
        return {
            "total_policy_versions": len(self.policy_versions),
            "total_value_versions": len(self.value_versions),
            "active_policy_version": self.active_policy_version.version_id if self.active_policy_version else None,
            "active_value_version": self.active_value_version.version_id if self.active_value_version else None,
            "production_models": [
                v.version_id for v in (self.policy_versions + self.value_versions)
                if v.is_production
            ],
            "storage_path": str(self.model_storage_path)
        }


class DeploymentManager:
    """Manages model deployments and rollbacks."""
    
    def __init__(self, config: RLConfig, model_manager: ModelManager):
        self.config = config
        self.model_manager = model_manager
        self.deployment_history: List[Dict[str, Any]] = []
    
    async def deploy_models(
        self,
        policy_version_id: str,
        value_version_id: str,
        deployment_notes: str = ""
    ) -> bool:
        """Deploy both policy and value models together."""
        
        try:
            # Validate versions exist
            policy_version = self.model_manager._find_version(policy_version_id)
            value_version = self.model_manager._find_version(value_version_id)
            
            if not policy_version or not value_version:
                logger.error("One or both model versions not found")
                return False
            
            # Deploy to production
            policy_success = await self.model_manager.deploy_to_production(policy_version_id)
            value_success = await self.model_manager.deploy_to_production(value_version_id)
            
            if not (policy_success and value_success):
                logger.error("Failed to deploy one or both models")
                return False
            
            # Set as active
            await self.model_manager.set_active_version(policy_version_id)
            await self.model_manager.set_active_version(value_version_id)
            
            # Record deployment
            deployment_record = {
                "timestamp": datetime.now().isoformat(),
                "policy_version": policy_version_id,
                "value_version": value_version_id,
                "deployment_notes": deployment_notes,
                "status": "success"
            }
            self.deployment_history.append(deployment_record)
            
            logger.info(f"Successfully deployed models: {policy_version_id}, {value_version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            
            # Record failed deployment
            deployment_record = {
                "timestamp": datetime.now().isoformat(),
                "policy_version": policy_version_id,
                "value_version": value_version_id,
                "deployment_notes": deployment_notes,
                "status": "failed",
                "error": str(e)
            }
            self.deployment_history.append(deployment_record)
            
            return False
    
    async def rollback_deployment(self, target_deployment_index: int = -2) -> bool:
        """Rollback to a previous deployment."""
        
        if len(self.deployment_history) < 2:
            logger.error("No previous deployment to rollback to")
            return False
        
        try:
            # Get target deployment
            target_deployment = self.deployment_history[target_deployment_index]
            
            if target_deployment["status"] != "success":
                logger.error("Target deployment was not successful")
                return False
            
            # Rollback
            policy_version = target_deployment["policy_version"]
            value_version = target_deployment["value_version"]
            
            success = await self.deploy_models(
                policy_version,
                value_version,
                f"Rollback to deployment from {target_deployment['timestamp']}"
            )
            
            if success:
                logger.info(f"Successfully rolled back to {target_deployment['timestamp']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """Get deployment history."""
        return self.deployment_history.copy()
    
    def get_current_deployment(self) -> Optional[Dict[str, Any]]:
        """Get current deployment info."""
        
        successful_deployments = [
            d for d in self.deployment_history if d["status"] == "success"
        ]
        
        return successful_deployments[-1] if successful_deployments else None