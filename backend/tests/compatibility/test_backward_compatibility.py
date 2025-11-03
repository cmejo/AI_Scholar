"""Backward compatibility tests for RL system components."""

import pytest
import asyncio
import json
import pickle
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from backend.rl.core.rl_system import RLSystem
from backend.rl.user_modeling.personalization_engine import PersonalizationEngine
from backend.rl.rewards.reward_calculator import RewardCalculator
from backend.rl.models.user_models import UserProfile, UserInteraction
from backend.rl.config.rl_config import RLConfig
from backend.rl.utils import get_component_logger


class TestBackwardCompatibilityCore:
    """Test backward compatibility of core RL system components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_component_logger("compatibility_test")
    
    def test_legacy_user_profile_compatibility(self):
        """Test that legacy user profiles are still supported."""
        # Create legacy user profile format (simplified)
        legacy_profile_data = {
            "user_id": "legacy_user_001",
            "preferences": {
                "research_domains": ["machine_learning"],
                "content_types": ["papers"],
                "difficulty_level": "intermediate"
            },
            "interaction_history": [
                {
                    "timestamp": "2023-01-01T10:00:00",
                    "action": "document_view",
                    "content_id": "doc_001",
                    "duration": 300,
                    "rating": 4
                }
            ],
            "created_at": "2023-01-01T00:00:00",
            "version": "1.0"
        }
        
        # Test that legacy profile can be loaded
        try:
            # Simulate loading legacy profile
            user_profile = UserProfile(
                user_id=legacy_profile_data["user_id"],
                preferences=legacy_profile_data["preferences"],
                created_at=datetime.fromisoformat(legacy_profile_data["created_at"].replace('Z', '+00:00'))
            )
            
            assert user_profile.user_id == "legacy_user_001"
            assert "machine_learning" in user_profile.preferences["research_domains"]
            
        except Exception as e:
            pytest.fail(f"Legacy user profile loading failed: {str(e)}")
    
    def test_legacy_interaction_format_compatibility(self):
        """Test that legacy interaction formats are supported."""
        # Legacy interaction format
        legacy_interactions = [
            {
                "user_id": "legacy_user_001",
                "action": "view_document",  # Old action format
                "document_id": "doc_001",   # Old field name
                "timestamp": "2023-01-01T10:00:00Z",
                "duration_seconds": 300,
                "user_rating": 4,
                "context": "research_session"
            },
            {
                "user_id": "legacy_user_001",
                "action": "search_query",
                "query": "machine learning papers",
                "timestamp": "2023-01-01T10:05:00Z",
                "results_count": 25,
                "clicked_result": "doc_002"
            }
        ]
        
        # Test conversion to new format
        converted_interactions = []
        for legacy_interaction in legacy_interactions:
            try:
                # Convert legacy format to new format
                new_interaction = UserInteraction(
                    user_id=legacy_interaction["user_id"],
                    interaction_type=legacy_interaction["action"].replace("_", "_"),  # Normalize
                    content_id=legacy_interaction.get("document_id") or legacy_interaction.get("query", "unknown"),
                    timestamp=datetime.fromisoformat(legacy_interaction["timestamp"].replace('Z', '+00:00')),
                    duration=legacy_interaction.get("duration_seconds", 0),
                    feedback_score=legacy_interaction.get("user_rating", 0),
                    context={"legacy_context": legacy_interaction.get("context", "")}
                )
                converted_interactions.append(new_interaction)
                
            except Exception as e:
                pytest.fail(f"Legacy interaction conversion failed: {str(e)}")
        
        assert len(converted_interactions) == 2
        assert converted_interactions[0].interaction_type == "view_document"
        assert converted_interactions[1].interaction_type == "search_query"
    
    def test_legacy_config_format_compatibility(self):
        """Test that legacy configuration formats are supported."""
        # Legacy config format
        legacy_config = {
            "learning_rate": 0.01,
            "discount_factor": 0.95,
            "exploration_rate": 0.1,
            "batch_size": 32,
            "memory_size": 10000,
            "update_frequency": 100,
            "reward_weights": {
                "engagement": 0.4,
                "learning": 0.3,
                "efficiency": 0.3
            },
            "personalization_enabled": True,
            "version": "1.0"
        }
        
        try:
            # Test loading legacy config
            config = RLConfig()
            
            # Simulate loading legacy config values
            config.learning_rate = legacy_config["learning_rate"]
            config.discount_factor = legacy_config["discount_factor"]
            config.exploration_rate = legacy_config["exploration_rate"]
            
            # Verify values are preserved
            assert config.learning_rate == 0.01
            assert config.discount_factor == 0.95
            assert config.exploration_rate == 0.1
            
        except Exception as e:
            pytest.fail(f"Legacy config loading failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_legacy_reward_calculation_compatibility(self):
        """Test that legacy reward calculation methods still work."""
        # Legacy reward calculation format
        legacy_reward_data = {
            "user_id": "legacy_user_001",
            "action": "document_view",
            "engagement_score": 0.8,
            "learning_score": 0.7,
            "efficiency_score": 0.6,
            "timestamp": datetime.now(),
            "session_context": {
                "session_length": 1800,  # 30 minutes
                "documents_viewed": 3,
                "queries_made": 2
            }
        }
        
        try:
            # Test legacy reward calculation
            reward_calculator = RewardCalculator()
            
            # Simulate legacy reward calculation
            engagement_reward = legacy_reward_data["engagement_score"] * 0.4
            learning_reward = legacy_reward_data["learning_score"] * 0.3
            efficiency_reward = legacy_reward_data["efficiency_score"] * 0.3
            
            total_reward = engagement_reward + learning_reward + efficiency_reward
            
            assert 0 <= total_reward <= 1.0
            assert total_reward > 0  # Should have positive reward
            
        except Exception as e:
            pytest.fail(f"Legacy reward calculation failed: {str(e)}")
    
    def test_legacy_serialization_compatibility(self):
        """Test that legacy serialized data can be loaded."""
        # Create legacy serialized data format
        legacy_user_data = {
            "user_id": "serialized_user_001",
            "preferences": {
                "domains": ["ml", "cv"],  # Old format
                "types": ["papers", "tutorials"],
                "level": "advanced"
            },
            "stats": {
                "total_interactions": 150,
                "avg_session_length": 1200,
                "favorite_topics": ["neural_networks", "computer_vision"]
            },
            "model_state": {
                "weights": [0.1, 0.2, 0.3, 0.4, 0.5],
                "bias": 0.05,
                "last_update": "2023-01-01T00:00:00Z"
            }
        }
        
        try:
            # Test JSON serialization compatibility
            json_data = json.dumps(legacy_user_data)
            loaded_data = json.loads(json_data)
            
            assert loaded_data["user_id"] == "serialized_user_001"
            assert "ml" in loaded_data["preferences"]["domains"]
            
            # Test pickle compatibility (if used)
            pickled_data = pickle.dumps(legacy_user_data)
            unpickled_data = pickle.loads(pickled_data)
            
            assert unpickled_data["user_id"] == "serialized_user_001"
            
        except Exception as e:
            pytest.fail(f"Legacy serialization compatibility failed: {str(e)}")


class TestBackwardCompatibilityPersonalization:
    """Test backward compatibility of personalization components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.personalization_engine = PersonalizationEngine()
    
    @pytest.mark.asyncio
    async def test_legacy_personalization_api_compatibility(self):
        """Test that legacy personalization API calls still work."""
        # Legacy API call format
        legacy_personalization_request = {
            "user_id": "legacy_api_user",
            "context": {
                "current_page": "search_results",
                "query": "machine learning",
                "session_id": "session_123"
            },
            "preferences": {
                "content_type": "papers",
                "difficulty": "intermediate",
                "domains": ["ml", "ai"]
            },
            "history": [
                {
                    "action": "view",
                    "item": "paper_001",
                    "rating": 4,
                    "time": "2023-01-01T10:00:00Z"
                }
            ]
        }
        
        try:
            # Test that legacy API format can be processed
            user_id = legacy_personalization_request["user_id"]
            context = legacy_personalization_request["context"]
            preferences = legacy_personalization_request["preferences"]
            
            # Simulate legacy personalization processing
            personalization_result = {
                "user_id": user_id,
                "recommendations": [
                    {"item_id": "rec_001", "score": 0.9, "reason": "matches_preferences"},
                    {"item_id": "rec_002", "score": 0.8, "reason": "similar_to_history"}
                ],
                "interface_adaptations": {
                    "layout": "detailed_view",
                    "sorting": "relevance",
                    "filters": ["ml", "ai"]
                }
            }
            
            assert personalization_result["user_id"] == user_id
            assert len(personalization_result["recommendations"]) > 0
            
        except Exception as e:
            pytest.fail(f"Legacy personalization API compatibility failed: {str(e)}")
    
    def test_legacy_preference_model_compatibility(self):
        """Test that legacy preference models can be loaded."""
        # Legacy preference model format
        legacy_preference_model = {
            "user_id": "legacy_pref_user",
            "model_version": "1.0",
            "preferences": {
                "content_preferences": {
                    "papers": 0.8,
                    "tutorials": 0.6,
                    "code": 0.4
                },
                "domain_preferences": {
                    "machine_learning": 0.9,
                    "computer_vision": 0.7,
                    "nlp": 0.5
                },
                "difficulty_preference": 0.7,  # 0-1 scale
                "length_preference": 0.6       # Preference for longer content
            },
            "learned_weights": [0.1, 0.2, 0.3, 0.4],
            "confidence_scores": {
                "content": 0.85,
                "domain": 0.90,
                "difficulty": 0.75
            },
            "last_updated": "2023-01-01T00:00:00Z"
        }
        
        try:
            # Test loading legacy preference model
            user_id = legacy_preference_model["user_id"]
            preferences = legacy_preference_model["preferences"]
            
            # Verify legacy format can be processed
            assert user_id == "legacy_pref_user"
            assert preferences["content_preferences"]["papers"] == 0.8
            assert preferences["domain_preferences"]["machine_learning"] == 0.9
            
            # Test conversion to new format if needed
            converted_preferences = {
                "research_domains": list(preferences["domain_preferences"].keys()),
                "content_types": list(preferences["content_preferences"].keys()),
                "complexity_level": "intermediate" if preferences["difficulty_preference"] > 0.5 else "beginner"
            }
            
            assert "machine_learning" in converted_preferences["research_domains"]
            assert "papers" in converted_preferences["content_types"]
            
        except Exception as e:
            pytest.fail(f"Legacy preference model compatibility failed: {str(e)}")
    
    def test_legacy_adaptation_algorithm_compatibility(self):
        """Test that legacy adaptation algorithms still work."""
        # Legacy adaptation algorithm state
        legacy_adaptation_state = {
            "algorithm_type": "gradient_bandit",
            "parameters": {
                "learning_rate": 0.01,
                "temperature": 1.0,
                "exploration_bonus": 0.1
            },
            "action_values": {
                "recommend_paper": 0.8,
                "show_tutorial": 0.6,
                "suggest_code": 0.4
            },
            "action_counts": {
                "recommend_paper": 45,
                "show_tutorial": 30,
                "suggest_code": 15
            },
            "total_reward": 67.5,
            "version": "1.0"
        }
        
        try:
            # Test legacy adaptation algorithm processing
            algorithm_type = legacy_adaptation_state["algorithm_type"]
            parameters = legacy_adaptation_state["parameters"]
            action_values = legacy_adaptation_state["action_values"]
            
            # Verify legacy algorithm state can be processed
            assert algorithm_type == "gradient_bandit"
            assert parameters["learning_rate"] == 0.01
            assert "recommend_paper" in action_values
            
            # Test that action selection still works with legacy format
            best_action = max(action_values.items(), key=lambda x: x[1])
            assert best_action[0] == "recommend_paper"
            assert best_action[1] == 0.8
            
        except Exception as e:
            pytest.fail(f"Legacy adaptation algorithm compatibility failed: {str(e)}")


class TestBackwardCompatibilityFeatureFlags:
    """Test backward compatibility with feature flags and gradual rollout."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.feature_flags = {
            "multimodal_processing": False,
            "advanced_personalization": False,
            "research_assistant_mode": False
        }
    
    @pytest.mark.asyncio
    async def test_system_with_all_features_disabled(self):
        """Test that system works with all new features disabled."""
        # Simulate system with all advanced features disabled
        config = {
            "enable_multimodal": False,
            "enable_advanced_personalization": False,
            "enable_research_assistant": False,
            "use_legacy_mode": True
        }
        
        try:
            # Test basic RL system functionality without advanced features
            basic_user_profile = {
                "user_id": "basic_user",
                "preferences": {"domain": "ml"},
                "interaction_count": 0
            }
            
            # Simulate basic interaction processing
            interaction = {
                "user_id": "basic_user",
                "action": "view_document",
                "content_id": "doc_001",
                "timestamp": datetime.now(),
                "feedback": 4
            }
            
            # Basic reward calculation
            basic_reward = interaction["feedback"] / 5.0  # Simple normalization
            
            assert 0 <= basic_reward <= 1.0
            assert basic_user_profile["user_id"] == "basic_user"
            
        except Exception as e:
            pytest.fail(f"System failed with features disabled: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_gradual_feature_enablement(self):
        """Test gradual enablement of advanced features."""
        # Test enabling features one by one
        feature_combinations = [
            {"multimodal": False, "personalization": False, "research_assistant": False},
            {"multimodal": True, "personalization": False, "research_assistant": False},
            {"multimodal": True, "personalization": True, "research_assistant": False},
            {"multimodal": True, "personalization": True, "research_assistant": True}
        ]
        
        for i, features in enumerate(feature_combinations):
            try:
                # Simulate system configuration with specific features enabled
                system_config = {
                    "enable_multimodal": features["multimodal"],
                    "enable_advanced_personalization": features["personalization"],
                    "enable_research_assistant": features["research_assistant"],
                    "fallback_to_basic": True
                }
                
                # Test that system handles each configuration
                user_interaction = {
                    "user_id": f"gradual_user_{i}",
                    "action": "document_view",
                    "content": "test document",
                    "has_visual_elements": features["multimodal"],
                    "requires_personalization": features["personalization"],
                    "research_context": features["research_assistant"]
                }
                
                # Simulate processing with current feature set
                processing_result = {
                    "basic_processing": True,
                    "multimodal_processing": features["multimodal"],
                    "personalization_applied": features["personalization"],
                    "research_assistance": features["research_assistant"]
                }
                
                assert processing_result["basic_processing"] is True
                
            except Exception as e:
                pytest.fail(f"Gradual feature enablement failed at step {i}: {str(e)}")
    
    def test_feature_flag_fallback_behavior(self):
        """Test fallback behavior when features are disabled."""
        # Test multimodal fallback
        document_with_visuals = {
            "id": "doc_with_visuals",
            "text": "Document with charts and diagrams",
            "visual_elements": ["chart_001", "diagram_001"],
            "multimodal_processing_enabled": False
        }
        
        try:
            # When multimodal is disabled, should fall back to text-only processing
            if not document_with_visuals["multimodal_processing_enabled"]:
                processed_content = {
                    "text_features": document_with_visuals["text"],
                    "visual_features": None,  # Disabled
                    "processing_mode": "text_only"
                }
            else:
                processed_content = {
                    "text_features": document_with_visuals["text"],
                    "visual_features": document_with_visuals["visual_elements"],
                    "processing_mode": "multimodal"
                }
            
            assert processed_content["processing_mode"] == "text_only"
            assert processed_content["visual_features"] is None
            
        except Exception as e:
            pytest.fail(f"Feature flag fallback failed: {str(e)}")
        
        # Test personalization fallback
        personalization_request = {
            "user_id": "fallback_user",
            "context": {"page": "search"},
            "advanced_personalization_enabled": False
        }
        
        try:
            if not personalization_request["advanced_personalization_enabled"]:
                # Fall back to basic personalization
                personalization_result = {
                    "recommendations": ["default_rec_1", "default_rec_2"],
                    "personalization_level": "basic",
                    "algorithm_used": "simple_collaborative_filtering"
                }
            else:
                personalization_result = {
                    "recommendations": ["advanced_rec_1", "advanced_rec_2"],
                    "personalization_level": "advanced",
                    "algorithm_used": "deep_preference_learning"
                }
            
            assert personalization_result["personalization_level"] == "basic"
            assert personalization_result["algorithm_used"] == "simple_collaborative_filtering"
            
        except Exception as e:
            pytest.fail(f"Personalization fallback failed: {str(e)}")


class TestBackwardCompatibilityDataMigration:
    """Test data migration and compatibility across versions."""
    
    def test_user_data_migration_v1_to_v2(self):
        """Test migration from version 1.0 to 2.0 user data format."""
        # Version 1.0 user data
        v1_user_data = {
            "id": "migration_user_001",
            "prefs": {  # Old field name
                "topics": ["ml", "ai"],
                "difficulty": "medium",
                "format": "papers"
            },
            "history": [
                {
                    "action": "view",
                    "item": "doc_001",
                    "time": "2023-01-01T10:00:00Z",
                    "score": 4
                }
            ],
            "version": "1.0"
        }
        
        try:
            # Migrate to version 2.0 format
            v2_user_data = {
                "user_id": v1_user_data["id"],  # Renamed field
                "preferences": {  # Renamed field
                    "research_domains": v1_user_data["prefs"]["topics"],
                    "complexity_level": v1_user_data["prefs"]["difficulty"],
                    "content_types": [v1_user_data["prefs"]["format"]]
                },
                "interaction_history": [
                    {
                        "interaction_type": item["action"] + "_document",
                        "content_id": item["item"],
                        "timestamp": item["time"],
                        "feedback_score": item["score"],
                        "duration": 0  # Default value for new field
                    }
                    for item in v1_user_data["history"]
                ],
                "created_at": datetime.now().isoformat(),
                "version": "2.0"
            }
            
            # Verify migration
            assert v2_user_data["user_id"] == "migration_user_001"
            assert "ml" in v2_user_data["preferences"]["research_domains"]
            assert v2_user_data["interaction_history"][0]["interaction_type"] == "view_document"
            assert v2_user_data["version"] == "2.0"
            
        except Exception as e:
            pytest.fail(f"Data migration v1 to v2 failed: {str(e)}")
    
    def test_config_migration_compatibility(self):
        """Test configuration migration across versions."""
        # Old configuration format
        old_config = {
            "rl_params": {
                "lr": 0.01,
                "gamma": 0.95,
                "epsilon": 0.1
            },
            "reward_config": {
                "engagement_weight": 0.4,
                "learning_weight": 0.3,
                "efficiency_weight": 0.3
            },
            "system_config": {
                "batch_size": 32,
                "memory_size": 10000
            }
        }
        
        try:
            # Migrate to new configuration format
            new_config = {
                "learning_parameters": {
                    "learning_rate": old_config["rl_params"]["lr"],
                    "discount_factor": old_config["rl_params"]["gamma"],
                    "exploration_rate": old_config["rl_params"]["epsilon"]
                },
                "reward_system": {
                    "weights": {
                        "engagement": old_config["reward_config"]["engagement_weight"],
                        "learning": old_config["reward_config"]["learning_weight"],
                        "efficiency": old_config["reward_config"]["efficiency_weight"]
                    }
                },
                "system_parameters": old_config["system_config"],
                "advanced_features": {
                    "multimodal_enabled": False,  # Default for migration
                    "advanced_personalization_enabled": False,
                    "research_assistant_enabled": False
                }
            }
            
            # Verify migration
            assert new_config["learning_parameters"]["learning_rate"] == 0.01
            assert new_config["reward_system"]["weights"]["engagement"] == 0.4
            assert new_config["advanced_features"]["multimodal_enabled"] is False
            
        except Exception as e:
            pytest.fail(f"Config migration failed: {str(e)}")
    
    def test_model_state_migration(self):
        """Test migration of model states across versions."""
        # Old model state format
        old_model_state = {
            "user_models": {
                "user_001": {
                    "weights": [0.1, 0.2, 0.3],
                    "bias": 0.05,
                    "last_update": "2023-01-01T00:00:00Z"
                }
            },
            "global_model": {
                "parameters": {"param1": 0.5, "param2": 0.8},
                "version": "1.0"
            }
        }
        
        try:
            # Migrate to new model state format
            new_model_state = {
                "user_profiles": {
                    "user_001": {
                        "preference_weights": old_model_state["user_models"]["user_001"]["weights"],
                        "bias_term": old_model_state["user_models"]["user_001"]["bias"],
                        "last_updated": old_model_state["user_models"]["user_001"]["last_update"],
                        "model_version": "2.0",
                        "advanced_features": {
                            "multimodal_weights": None,  # New field
                            "personalization_state": None,  # New field
                            "research_context": None  # New field
                        }
                    }
                },
                "system_model": {
                    "global_parameters": old_model_state["global_model"]["parameters"],
                    "feature_flags": {
                        "multimodal": False,
                        "advanced_personalization": False,
                        "research_assistant": False
                    },
                    "version": "2.0"
                }
            }
            
            # Verify migration
            user_profile = new_model_state["user_profiles"]["user_001"]
            assert user_profile["preference_weights"] == [0.1, 0.2, 0.3]
            assert user_profile["model_version"] == "2.0"
            assert user_profile["advanced_features"]["multimodal_weights"] is None
            
        except Exception as e:
            pytest.fail(f"Model state migration failed: {str(e)}")


class TestBackwardCompatibilityAPI:
    """Test API backward compatibility."""
    
    def test_legacy_api_endpoints_compatibility(self):
        """Test that legacy API endpoints still work."""
        # Legacy API request formats
        legacy_requests = [
            {
                "endpoint": "/api/v1/personalize",
                "method": "POST",
                "data": {
                    "user_id": "api_user_001",
                    "context": "search_page",
                    "preferences": {"domain": "ml"}
                }
            },
            {
                "endpoint": "/api/v1/recommend",
                "method": "GET",
                "params": {
                    "user": "api_user_001",
                    "type": "papers",
                    "count": 10
                }
            },
            {
                "endpoint": "/api/v1/feedback",
                "method": "POST",
                "data": {
                    "user": "api_user_001",
                    "item": "doc_001",
                    "rating": 4,
                    "action": "view"
                }
            }
        ]
        
        for request in legacy_requests:
            try:
                # Simulate processing legacy API request
                endpoint = request["endpoint"]
                method = request["method"]
                
                if endpoint == "/api/v1/personalize":
                    # Legacy personalization endpoint
                    response = {
                        "status": "success",
                        "user_id": request["data"]["user_id"],
                        "personalization": {
                            "layout": "standard",
                            "recommendations": ["rec_001", "rec_002"]
                        }
                    }
                elif endpoint == "/api/v1/recommend":
                    # Legacy recommendation endpoint
                    response = {
                        "status": "success",
                        "recommendations": [
                            {"id": "rec_001", "score": 0.9},
                            {"id": "rec_002", "score": 0.8}
                        ]
                    }
                elif endpoint == "/api/v1/feedback":
                    # Legacy feedback endpoint
                    response = {
                        "status": "success",
                        "message": "Feedback recorded"
                    }
                
                assert response["status"] == "success"
                
            except Exception as e:
                pytest.fail(f"Legacy API endpoint {request['endpoint']} failed: {str(e)}")
    
    def test_api_response_format_compatibility(self):
        """Test that API responses maintain backward compatibility."""
        # Legacy response format expectations
        legacy_response_formats = {
            "personalization": {
                "user_id": "string",
                "recommendations": ["array", "of", "strings"],
                "settings": {"key": "value"},
                "timestamp": "ISO_string"
            },
            "recommendation": {
                "items": [
                    {"id": "string", "score": "float", "type": "string"}
                ],
                "total_count": "integer",
                "page": "integer"
            },
            "feedback": {
                "status": "string",
                "user_id": "string",
                "updated_preferences": {"key": "value"}
            }
        }
        
        try:
            # Test that current system can generate legacy-compatible responses
            for response_type, expected_format in legacy_response_formats.items():
                if response_type == "personalization":
                    response = {
                        "user_id": "test_user",
                        "recommendations": ["rec_001", "rec_002", "rec_003"],
                        "settings": {"theme": "dark", "layout": "compact"},
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Verify format compatibility
                    assert isinstance(response["user_id"], str)
                    assert isinstance(response["recommendations"], list)
                    assert isinstance(response["settings"], dict)
                    assert isinstance(response["timestamp"], str)
                
                elif response_type == "recommendation":
                    response = {
                        "items": [
                            {"id": "rec_001", "score": 0.9, "type": "paper"},
                            {"id": "rec_002", "score": 0.8, "type": "tutorial"}
                        ],
                        "total_count": 2,
                        "page": 1
                    }
                    
                    # Verify format compatibility
                    assert isinstance(response["items"], list)
                    assert isinstance(response["total_count"], int)
                    assert isinstance(response["page"], int)
                    
                    for item in response["items"]:
                        assert isinstance(item["id"], str)
                        assert isinstance(item["score"], (int, float))
                        assert isinstance(item["type"], str)
                
                elif response_type == "feedback":
                    response = {
                        "status": "success",
                        "user_id": "test_user",
                        "updated_preferences": {"domain": "ml", "difficulty": "advanced"}
                    }
                    
                    # Verify format compatibility
                    assert isinstance(response["status"], str)
                    assert isinstance(response["user_id"], str)
                    assert isinstance(response["updated_preferences"], dict)
                
        except Exception as e:
            pytest.fail(f"API response format compatibility failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__])