# Docker and Deployment Configuration Validation Report
Generated on: Sun Aug 24 20:26:12 EDT 2025

## Summary
- Files analyzed: 126
- Total issues: 3479
- Critical issues: 1
- High severity issues: 180
- Medium severity issues: 3127
- Low severity issues: 171
- Info issues: 0

## Critical Issues (1)

### docker-compose.ubuntu.yml
**Type:** docker_compose_issue
**Description:** Invalid compose file structure
**Recommendation:** Ensure compose file has proper YAML structure
**Rule ID:** COMPOSE_STRUCTURE_ERROR

## High Issues (180)

### docker-compose.ai-services.yml
**Type:** docker_compose_issue
**Description:** Missing required field: version
**Recommendation:** Add version field to compose file
**Rule ID:** COMPOSE_MISSING_FIELD

### docker-compose.minimal.yml
**Type:** docker_compose_issue
**Description:** Missing required field: version
**Recommendation:** Add version field to compose file
**Rule ID:** COMPOSE_MISSING_FIELD

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Missing required field: version
**Recommendation:** Add version field to compose file
**Rule ID:** COMPOSE_MISSING_FIELD

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'frontend' missing image or build
**Recommendation:** Add either 'image' or 'build' configuration
**Rule ID:** COMPOSE_SERVICE_NO_IMAGE

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'streamlit' missing image or build
**Recommendation:** Add either 'image' or 'build' configuration
**Rule ID:** COMPOSE_SERVICE_NO_IMAGE

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'backend' missing image or build
**Recommendation:** Add either 'image' or 'build' configuration
**Rule ID:** COMPOSE_SERVICE_NO_IMAGE

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'postgres' missing image or build
**Recommendation:** Add either 'image' or 'build' configuration
**Rule ID:** COMPOSE_SERVICE_NO_IMAGE

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'nginx' missing image or build
**Recommendation:** Add either 'image' or 'build' configuration
**Rule ID:** COMPOSE_SERVICE_NO_IMAGE

### production-deploy.sh
**Line:** 197
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 198
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 225
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 328
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 329
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 552
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 582
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 583
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 584
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### production-deploy.sh
**Line:** 619
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-with-monitoring.sh
**Line:** 113
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-with-monitoring.sh
**Line:** 114
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-zotero-production.sh
**Line:** 285
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-zotero-production.sh
**Line:** 286
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-zotero-production.sh
**Line:** 312
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy.sh
**Line:** 108
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy.sh
**Line:** 109
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/validate-deployment.sh
**Line:** 525
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: yum
**Recommendation:** Use apt-get for Ubuntu systems
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/validate-deployment.sh
**Line:** 526
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: yum
**Recommendation:** Use apt-get for Ubuntu systems
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/production-deploy.sh
**Line:** 351
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/production-deploy.sh
**Line:** 352
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/production-deploy.sh
**Line:** 462
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/production-deploy.sh
**Line:** 463
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deployment/blue-green-deployment.sh
**Line:** 290
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-with-monitoring.sh
**Line:** 113
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-with-monitoring.sh
**Line:** 114
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-zotero-production.sh
**Line:** 285
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-zotero-production.sh
**Line:** 286
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy-zotero-production.sh
**Line:** 312
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy.sh
**Line:** 108
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### scripts/deploy.sh
**Line:** 109
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-ssl-setup.sh
**Line:** 132
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: yum
**Recommendation:** Use apt-get for Ubuntu systems
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-ssl-setup.sh
**Line:** 132
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: dnf
**Recommendation:** Use apt-get for Ubuntu systems
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-ssl-setup.sh
**Line:** 152
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-ssl-setup.sh
**Line:** 178
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-ssl-setup.sh
**Line:** 194
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-ssl-setup.sh
**Line:** 291
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### setup-nginx-proxy.sh
**Line:** 88
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: yum
**Recommendation:** Use apt-get for Ubuntu systems
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### setup-nginx-proxy.sh
**Line:** 88
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: dnf
**Recommendation:** Use apt-get for Ubuntu systems
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### setup-nginx-proxy.sh
**Line:** 540
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### setup-nginx-proxy.sh
**Line:** 541
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-monitoring-setup.sh
**Line:** 499
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-monitoring-setup.sh
**Line:** 500
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### nginx-monitoring-setup.sh
**Line:** 620
**Type:** ubuntu_compatibility
**Description:** Ubuntu incompatible command: systemctl
**Recommendation:** May not be available in containers, use service or direct commands
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_UBUNTU_INCOMPATIBLE

### .env.production
**Line:** 15
**Type:** security_issue
**Description:** Sensitive data in environment file: POSTGRES_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 19
**Type:** security_issue
**Description:** Sensitive data in environment file: REDIS_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 25
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 26
**Type:** security_issue
**Description:** Sensitive data in environment file: JWT_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 31
**Type:** security_issue
**Description:** Sensitive data in environment file: OPENAI_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 32
**Type:** security_issue
**Description:** Sensitive data in environment file: HUGGINGFACE_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 33
**Type:** security_issue
**Description:** Sensitive data in environment file: ANTHROPIC_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 77
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_ACCESS_KEY_ID
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 78
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_SECRET_ACCESS_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.production
**Line:** 83
**Type:** security_issue
**Description:** Sensitive data in environment file: GRAFANA_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 15
**Type:** security_issue
**Description:** Sensitive data in environment file: POSTGRES_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 19
**Type:** security_issue
**Description:** Sensitive data in environment file: REDIS_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 25
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 26
**Type:** security_issue
**Description:** Sensitive data in environment file: JWT_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 31
**Type:** security_issue
**Description:** Sensitive data in environment file: OPENAI_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 32
**Type:** security_issue
**Description:** Sensitive data in environment file: HUGGINGFACE_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 33
**Type:** security_issue
**Description:** Sensitive data in environment file: ANTHROPIC_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 77
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_ACCESS_KEY_ID
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 78
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_SECRET_ACCESS_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 83
**Type:** security_issue
**Description:** Sensitive data in environment file: GRAFANA_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 14
**Type:** security_issue
**Description:** Sensitive data in environment file: OPENAI_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 17
**Type:** security_issue
**Description:** Sensitive data in environment file: HUGGINGFACE_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 20
**Type:** security_issue
**Description:** Sensitive data in environment file: ANTHROPIC_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 26
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 29
**Type:** security_issue
**Description:** Sensitive data in environment file: JWT_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 126
**Type:** security_issue
**Description:** Sensitive data in environment file: SMTP_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env.example
**Line:** 202
**Type:** security_issue
**Description:** Sensitive data in environment file: TRANSLATION_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 29
**Type:** security_issue
**Description:** Sensitive data in environment file: POSTGRES_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 33
**Type:** security_issue
**Description:** Sensitive data in environment file: REDIS_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 43
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 44
**Type:** security_issue
**Description:** Sensitive data in environment file: JWT_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 54
**Type:** security_issue
**Description:** Sensitive data in environment file: OPENAI_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 57
**Type:** security_issue
**Description:** Sensitive data in environment file: HUGGINGFACE_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 60
**Type:** security_issue
**Description:** Sensitive data in environment file: ANTHROPIC_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 69
**Type:** security_issue
**Description:** Sensitive data in environment file: SMTP_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 81
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_ACCESS_KEY_ID
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 82
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_SECRET_ACCESS_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 98
**Type:** security_issue
**Description:** Sensitive data in environment file: GRAFANA_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 172
**Type:** security_issue
**Description:** Sensitive data in environment file: PASSWORD_MIN_LENGTH
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 185
**Type:** security_issue
**Description:** Sensitive data in environment file: GOOGLE_TRANSLATE_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/.env.production
**Line:** 186
**Type:** security_issue
**Description:** Sensitive data in environment file: DEEPL_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/.env.example
**Line:** 20
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/.env.example
**Line:** 21
**Type:** security_issue
**Description:** Sensitive data in environment file: ACCESS_TOKEN_EXPIRE_MINUTES
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 448
**Type:** security_issue
**Description:** Sensitive data in environment file: rv.extensions[key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 464
**Type:** security_issue
**Description:** Sensitive data in environment file: return iter(sorted(self.extensions.values(), key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 962
**Type:** security_issue
**Description:** Sensitive data in environment file: cache_key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 978
**Type:** security_issue
**Description:** Sensitive data in environment file: self.cache[cache_key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1442
**Type:** security_issue
**Description:** Sensitive data in environment file: keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1456
**Type:** security_issue
**Description:** Sensitive data in environment file: keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 42
**Type:** security_issue
**Description:** Sensitive data in environment file: - string: `environ[key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 153
**Type:** security_issue
**Description:** Sensitive data in environment file: soft_keywords
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/coverage/__pycache__/env.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 36
**Type:** security_issue
**Description:** Sensitive data in environment file: _secrets_dir: Optional[StrPath]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 46
**Type:** security_issue
**Description:** Sensitive data in environment file: _secrets_dir
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 56
**Type:** security_issue
**Description:** Sensitive data in environment file: _secrets_dir: Optional[StrPath]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 70
**Type:** security_issue
**Description:** Sensitive data in environment file: file_secret_settings
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 87
**Type:** security_issue
**Description:** Sensitive data in environment file: secrets_dir: Optional[StrPath]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 260
**Type:** security_issue
**Description:** Sensitive data in environment file: _, *keys, last_key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 264
**Type:** security_issue
**Description:** Sensitive data in environment file: env_var[last_key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 279
**Type:** security_issue
**Description:** Sensitive data in environment file: self.secrets_dir: Optional[StrPath]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 285
**Type:** security_issue
**Description:** Sensitive data in environment file: secrets: Dict[str, Optional[str]]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 290
**Type:** security_issue
**Description:** Sensitive data in environment file: secrets_path
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 307
**Type:** security_issue
**Description:** Sensitive data in environment file: secret_value
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 310
**Type:** security_issue
**Description:** Sensitive data in environment file: secret_value
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 314
**Type:** security_issue
**Description:** Sensitive data in environment file: secrets[field.alias]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 323
**Type:** security_issue
**Description:** Sensitive data in environment file: return f'SecretsSettingsSource(secrets_dir
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic/__pycache__/env_settings.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/__pycache__/env_settings.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 17
**Type:** security_issue
**Description:** Sensitive data in environment file: environ_key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/virtualenv/config/__pycache__/env_var.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/__pycache__/environment.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/build/__pycache__/env.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/weasel/util/__pycache__/environment.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 147
**Type:** security_issue
**Description:** Sensitive data in environment file: self, field: FieldInfo | Any | None, key: str, case_sensitive: bool | None
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 183
**Type:** security_issue
**Description:** Sensitive data in environment file: type_has_key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 230
**Type:** security_issue
**Description:** Sensitive data in environment file: *keys, last_key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 258
**Type:** security_issue
**Description:** Sensitive data in environment file: if last_key not in env_var or not isinstance(env_val, EnvNoneType) or env_var[last_key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 259
**Type:** security_issue
**Description:** Sensitive data in environment file: env_var[last_key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/__pycache__/env.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/transformers/commands/__pycache__/env.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 31
**Type:** security_issue
**Description:** Sensitive data in environment file: self._key_extractor
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 67
**Type:** security_issue
**Description:** Sensitive data in environment file: before_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 68
**Type:** security_issue
**Description:** Sensitive data in environment file: after_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 71
**Type:** security_issue
**Description:** Sensitive data in environment file: added_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 72
**Type:** security_issue
**Description:** Sensitive data in environment file: removed_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 75
**Type:** security_issue
**Description:** Sensitive data in environment file: common_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 76
**Type:** security_issue
**Description:** Sensitive data in environment file: updated_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 79
**Type:** security_issue
**Description:** Sensitive data in environment file: if self._before_items[key] !
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 103
**Type:** security_issue
**Description:** Sensitive data in environment file: key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 105
**Type:** security_issue
**Description:** Sensitive data in environment file: result[key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 119
**Type:** security_issue
**Description:** Sensitive data in environment file: key_extractor
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/safety/tool/__pycache__/environment_diff.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 404
**Type:** security_issue
**Description:** Sensitive data in environment file: sub_keys
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 412
**Type:** security_issue
**Description:** Sensitive data in environment file: sub_key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/jedi/api/__pycache__/environment.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/pre_commit/__pycache__/envcontext.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 36
**Type:** security_issue
**Description:** Sensitive data in environment file: CREDENTIALS
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 80
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_ACCESS_KEY_ID
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 81
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_SECRET_ACCESS_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 82
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_SESSION_TOKEN
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/google/auth/__pycache__/environment_vars.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/jinja2/__pycache__/environment.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/__pycache__/env.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 215
**Type:** security_issue
**Description:** Sensitive data in environment file: for var in sorted(builder.free_variables[builder.fn_info.fitem], key
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.cpython-313-darwin.so
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xcf in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/__pycache__/env_class.cpython-313.pyc
**Type:** environment_config_issue
**Description:** Failed to read env file: 'utf-8' codec can't decode byte 0xf3 in position 0: invalid continuation byte
**Recommendation:** Ensure file exists and is readable
**Rule ID:** ENV_READ_ERROR

### node_modules/vite/dist/client/env.mjs
**Line:** 13
**Type:** security_issue
**Description:** Sensitive data in environment file: Object.keys(defines).forEach((key)
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 27
**Type:** security_issue
**Description:** Sensitive data in environment file: retv[key]
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 15
**Type:** security_issue
**Description:** Sensitive data in environment file: POSTGRES_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 19
**Type:** security_issue
**Description:** Sensitive data in environment file: REDIS_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 25
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 26
**Type:** security_issue
**Description:** Sensitive data in environment file: JWT_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 31
**Type:** security_issue
**Description:** Sensitive data in environment file: OPENAI_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 32
**Type:** security_issue
**Description:** Sensitive data in environment file: HUGGINGFACE_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 33
**Type:** security_issue
**Description:** Sensitive data in environment file: ANTHROPIC_API_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 77
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_ACCESS_KEY_ID
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 78
**Type:** security_issue
**Description:** Sensitive data in environment file: AWS_SECRET_ACCESS_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### .env
**Line:** 83
**Type:** security_issue
**Description:** Sensitive data in environment file: GRAFANA_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/staging.env
**Line:** 60
**Type:** security_issue
**Description:** Sensitive data in environment file: AI_MAX_TOKENS
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/staging.env
**Line:** 121
**Type:** security_issue
**Description:** Sensitive data in environment file: SSL_KEY_PATH
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/development.env
**Line:** 15
**Type:** security_issue
**Description:** Sensitive data in environment file: DB_PASSWORD
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/development.env
**Line:** 39
**Type:** security_issue
**Description:** Sensitive data in environment file: ZOTERO_WEBHOOK_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/development.env
**Line:** 42
**Type:** security_issue
**Description:** Sensitive data in environment file: ZOTERO_ENCRYPTION_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/development.env
**Line:** 43
**Type:** security_issue
**Description:** Sensitive data in environment file: SECRET_KEY
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/development.env
**Line:** 44
**Type:** security_issue
**Description:** Sensitive data in environment file: JWT_SECRET
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/development.env
**Line:** 60
**Type:** security_issue
**Description:** Sensitive data in environment file: AI_MAX_TOKENS
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/production.env
**Line:** 60
**Type:** security_issue
**Description:** Sensitive data in environment file: AI_MAX_TOKENS
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

### config/deployment/production.env
**Line:** 121
**Type:** security_issue
**Description:** Sensitive data in environment file: SSL_KEY_PATH
**Recommendation:** Use environment variable references or external secrets
**Rule ID:** ENV_SENSITIVE_DATA

## Medium Issues (3127)

### Dockerfile.frontend.simple
**Line:** 47
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 48
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 49
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 50
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 66
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 73
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 72
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 73
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 74
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 75
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 76
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 194
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 201
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 202
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 208
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 56
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 57
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 58
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 59
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 75
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 82
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### backend/Dockerfile
**Type:** dockerfile_issue
**Description:** Missing HEALTHCHECK instruction
**Recommendation:** Add HEALTHCHECK instruction for better container monitoring
**Rule ID:** DOCKERFILE_MISSING_HEALTHCHECK

### config/dockerfiles/Dockerfile.frontend
**Line:** 43
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### config/dockerfiles/Dockerfile.backup
**Line:** 20
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 47
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 48
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 49
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 50
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 66
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend.simple
**Line:** 73
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 72
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 73
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 74
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 75
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 76
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 194
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 201
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 202
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.nginx
**Line:** 208
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 56
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 57
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 58
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 59
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 75
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### Dockerfile.frontend
**Line:** 82
**Type:** dockerfile_issue
**Description:** Deprecated command: ADD
**Recommendation:** Use COPY instead unless you need ADD specific features
**Rule ID:** DOCKERFILE_DEPRECATED_CMD

### docker-compose.ai-services.yml
**Type:** docker_compose_issue
**Description:** External network 'ai-scholar-network' missing name
**Recommendation:** Specify network name for external networks
**Rule ID:** COMPOSE_EXTERNAL_NETWORK_NAME

### docker-compose.green.yml
**Type:** docker_compose_issue
**Description:** Service 'celery-worker-green' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.green.yml
**Type:** docker_compose_issue
**Description:** Service 'celery-beat-green' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.green.yml
**Type:** docker_compose_issue
**Description:** External network 'aischolar-network' missing name
**Recommendation:** Specify network name for external networks
**Rule ID:** COMPOSE_EXTERNAL_NETWORK_NAME

### docker-compose.blue.yml
**Type:** docker_compose_issue
**Description:** Service 'celery-worker-blue' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.blue.yml
**Type:** docker_compose_issue
**Description:** Service 'celery-beat-blue' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.blue.yml
**Type:** docker_compose_issue
**Description:** External network 'aischolar-network' missing name
**Recommendation:** Specify network name for external networks
**Rule ID:** COMPOSE_EXTERNAL_NETWORK_NAME

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'node-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'redis-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'postgres-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'logstash' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'filebeat' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'jaeger' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** Service 'zotero-metrics-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.monitoring.yml
**Type:** docker_compose_issue
**Description:** External network 'aischolar-network' missing name
**Recommendation:** Specify network name for external networks
**Rule ID:** COMPOSE_EXTERNAL_NETWORK_NAME

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'prometheus' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'grafana' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'loki' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'promtail' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'backup' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'worker' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'scheduler' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'certbot' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'prometheus' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'grafana' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'worker' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'scheduler' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'backup' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'node-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'redis-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'postgres-exporter' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.green.yml
**Type:** docker_compose_issue
**Description:** Service 'worker-green' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.green.yml
**Type:** docker_compose_issue
**Description:** External network 'rag-network' missing name
**Recommendation:** Specify network name for external networks
**Rule ID:** COMPOSE_EXTERNAL_NETWORK_NAME

### config/docker-compose.blue.yml
**Type:** docker_compose_issue
**Description:** Service 'worker-blue' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.blue.yml
**Type:** docker_compose_issue
**Description:** External network 'rag-network' missing name
**Recommendation:** Specify network name for external networks
**Rule ID:** COMPOSE_EXTERNAL_NETWORK_NAME

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'ai-scholar-frontend' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'celery-beat' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'prometheus' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'grafana' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'loki' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'promtail' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.zotero.yml
**Type:** docker_compose_issue
**Description:** Service 'backup' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'frontend' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'streamlit' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'backend' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'postgres' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'nginx' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'prometheus' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'grafana' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### backend/docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'backend' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### backend/docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'db' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### backend/docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'ollama' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### backend/docker-compose.yml
**Type:** docker_compose_issue
**Description:** Service 'frontend' missing health check
**Recommendation:** Add healthcheck configuration for better monitoring
**Rule ID:** COMPOSE_NO_HEALTHCHECK

### config/.env.production
**Line:** 220
**Type:** environment_config_issue
**Description:** Duplicate environment variable: LOG_LEVEL
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 55
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 58
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 69
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 70
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 71
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 72
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 75
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 79
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 83
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 84
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 85
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 87
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 90
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 92
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 96
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 97
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 100
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 109
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 111
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 127
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 129
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 134
**Type:** environment_config_issue
**Description:** Duplicate environment variable: !
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 135
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 136
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 137
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 144
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 145
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 146
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 149
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 150
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 154
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 158
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 161
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 164
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 165
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 169
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 171
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 174
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 175
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 176
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 178
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 179
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 180
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 182
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 185
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 186
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 189
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 198
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 207
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 208
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 210
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 211
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 214
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 215
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 217
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 218
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 219
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 220
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 222
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 223
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 224
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 225
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 226
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 227
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 228
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 230
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 231
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 233
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 234
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 236
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 237
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 238
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 239
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 240
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 241
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 243
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 244
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 246
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 247
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 248
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 249
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 250
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 251
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 252
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 254
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 255
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 256
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 257
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 259
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 261
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 262
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 263
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 264
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 292
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 294
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 295
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 318
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 368
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 370
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 371
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 373
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 374
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 375
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 377
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 378
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 379
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 380
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 381
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 382
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 383
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 384
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 386
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 387
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 388
**Type:** environment_config_issue
**Description:** Duplicate environment variable: block_start_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 389
**Type:** environment_config_issue
**Description:** Duplicate environment variable: block_end_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 390
**Type:** environment_config_issue
**Description:** Duplicate environment variable: variable_start_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 391
**Type:** environment_config_issue
**Description:** Duplicate environment variable: variable_end_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 392
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_start_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 393
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_end_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 394
**Type:** environment_config_issue
**Description:** Duplicate environment variable: line_statement_prefix: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 395
**Type:** environment_config_issue
**Description:** Duplicate environment variable: line_comment_prefix: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 396
**Type:** environment_config_issue
**Description:** Duplicate environment variable: trim_blocks: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 397
**Type:** environment_config_issue
**Description:** Duplicate environment variable: lstrip_blocks: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 398
**Type:** environment_config_issue
**Description:** Duplicate environment variable: newline_sequence: "te.Literal['\\n', '\\r\\n', '\\r']"
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 399
**Type:** environment_config_issue
**Description:** Duplicate environment variable: keep_trailing_newline: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 400
**Type:** environment_config_issue
**Description:** Duplicate environment variable: extensions: t.Sequence[t.Union[str, t.Type["Extension"]]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 401
**Type:** environment_config_issue
**Description:** Duplicate environment variable: optimized: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 402
**Type:** environment_config_issue
**Description:** Duplicate environment variable: undefined: t.Type[Undefined]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 403
**Type:** environment_config_issue
**Description:** Duplicate environment variable: finalize: t.Optional[t.Callable[..., t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 404
**Type:** environment_config_issue
**Description:** Duplicate environment variable: autoescape: t.Union[bool, t.Callable[[t.Optional[str]], bool]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 405
**Type:** environment_config_issue
**Description:** Duplicate environment variable: loader: t.Optional["BaseLoader"]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 406
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cache_size: int
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 407
**Type:** environment_config_issue
**Description:** Duplicate environment variable: auto_reload: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 408
**Type:** environment_config_issue
**Description:** Duplicate environment variable: bytecode_cache: t.Optional["BytecodeCache"]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 409
**Type:** environment_config_issue
**Description:** Duplicate environment variable: enable_async: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 410
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 411
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 412
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 413
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 414
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 415
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 417
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 418
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 419
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 420
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 422
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 423
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 425
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 426
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 427
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 428
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 430
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 433
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 437
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 438
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 439
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 441
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 443
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 444
**Type:** environment_config_issue
**Description:** Duplicate environment variable: rv.cache
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 447
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 449
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 450
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 452
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 455
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 457
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 458
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 459
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 460
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 462
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 463
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 466
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 467
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 468
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 469
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 470
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 471
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 472
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 473
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 474
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 476
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 477
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 478
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 479
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 480
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 481
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 482
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 485
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 486
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 487
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 488
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 489
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 490
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 491
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 492
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 493
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 494
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 495
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 496
**Type:** environment_config_issue
**Description:** Duplicate environment variable: return self.undefined(obj
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 498
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 499
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 500
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 501
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 502
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 503
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 504
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 505
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 506
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 507
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 508
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 511
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 512
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_map
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 513
**Type:** environment_config_issue
**Description:** Duplicate environment variable: type_name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 517
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 520
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 521
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 522
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 523
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 524
**Type:** environment_config_issue
**Description:** Duplicate environment variable: msg
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 526
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 528
**Type:** environment_config_issue
**Description:** Duplicate environment variable: args
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 532
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 533
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 534
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 535
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 536
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 538
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 539
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 540
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 541
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 543
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 544
**Type:** environment_config_issue
**Description:** Duplicate environment variable: eval_ctx
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 546
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 547
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 548
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 550
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 552
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 553
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 554
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 555
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 560
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 561
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 563
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 564
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 565
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 567
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 568
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 569
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 570
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 571
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 573
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 574
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 575
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 576
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 577
**Type:** environment_config_issue
**Description:** Duplicate environment variable: args: t.Optional[t.Sequence[t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 578
**Type:** environment_config_issue
**Description:** Duplicate environment variable: kwargs: t.Optional[t.Mapping[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 579
**Type:** environment_config_issue
**Description:** Duplicate environment variable: context: t.Optional[Context]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 580
**Type:** environment_config_issue
**Description:** Duplicate environment variable: eval_ctx: t.Optional[EvalContext]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 581
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 582
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 584
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 585
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 586
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 588
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 589
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 590
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 592
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 593
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 594
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 595
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 596
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 598
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 599
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 600
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 601
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 604
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 605
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 606
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 607
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 608
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 610
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 611
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 612
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 613
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 614
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 615
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 618
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 619
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 620
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 621
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 622
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 624
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 625
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 626
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 627
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 628
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 629
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 630
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 631
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 632
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 633
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 635
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 636
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 637
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 638
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 640
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 641
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 642
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 643
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self.handle_exception(source
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 645
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 646
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 647
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 648
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 649
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 650
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 651
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 652
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 653
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 654
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 655
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 656
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 657
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 658
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 659
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 661
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 662
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 663
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 664
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 665
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 667
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 668
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 669
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 670
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 671
**Type:** environment_config_issue
**Description:** Duplicate environment variable: source
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 674
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 675
**Type:** environment_config_issue
**Description:** Duplicate environment variable: stream
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 677
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 678
**Type:** environment_config_issue
**Description:** Duplicate environment variable: stream
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 680
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 682
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 683
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 684
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 685
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 686
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 688
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 689
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 690
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 692
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 693
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 694
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 695
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 696
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 697
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 698
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 701
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 703
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 704
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 705
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 707
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 708
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 709
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 711
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 712
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 713
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 714
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 715
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 716
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 718
**Type:** environment_config_issue
**Description:** Duplicate environment variable: defer_init: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 719
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 721
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 722
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 723
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 724
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 725
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 726
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 728
**Type:** environment_config_issue
**Description:** Duplicate environment variable: defer_init: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 729
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 731
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 732
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 733
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 734
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 735
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 736
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 738
**Type:** environment_config_issue
**Description:** Duplicate environment variable: defer_init: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 739
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 740
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 741
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 742
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 743
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 744
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 745
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 747
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 748
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 749
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 750
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 752
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 753
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 754
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 756
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 757
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 758
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 760
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 761
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 762
**Type:** environment_config_issue
**Description:** Duplicate environment variable: source_hint
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 763
**Type:** environment_config_issue
**Description:** Duplicate environment variable: source
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 764
**Type:** environment_config_issue
**Description:** Duplicate environment variable: source
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 765
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 766
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 767
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 769
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 770
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 771
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self.handle_exception(source
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 773
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 775
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 776
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 777
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 778
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 780
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 781
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 783
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 788
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 789
**Type:** environment_config_issue
**Description:** Duplicate environment variable: >>> expr(foo
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 790
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 792
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 793
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 794
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 796
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 797
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 799
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 801
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 802
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 804
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 806
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 807
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 808
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 809
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 810
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 811
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 812
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self.handle_exception(source
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 816
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 818
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 819
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 820
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 826
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 827
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 828
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 829
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 830
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 831
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 833
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 834
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 835
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 837
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 838
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 839
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 840
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 842
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 843
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 844
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 846
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 848
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 849
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 851
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 852
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 854
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 855
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 858
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 859
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 860
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 861
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 863
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 864
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 865
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 866
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 867
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 871
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 872
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 873
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 874
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 875
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 876
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 878
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 879
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 881
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 883
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 884
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 885
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 886
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 887
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 889
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filename
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 891
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 892
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 893
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 894
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 895
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 897
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 899
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 900
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 901
**Type:** environment_config_issue
**Description:** Duplicate environment variable: extensions: t.Optional[t.Collection[str]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 902
**Type:** environment_config_issue
**Description:** Duplicate environment variable: filter_func: t.Optional[t.Callable[[str], bool]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 903
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 904
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 905
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 906
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 908
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 909
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 910
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 911
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 912
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 913
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 915
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 917
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 918
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 919
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 922
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 923
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 924
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 925
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 926
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 928
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 929
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 931
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 932
**Type:** environment_config_issue
**Description:** Duplicate environment variable: names
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 934
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 937
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 938
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 939
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 940
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 944
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 945
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 946
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 947
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 948
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 949
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 951
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 952
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 953
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 954
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 956
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 957
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 958
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 959
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 960
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 961
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 963
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 964
**Type:** environment_config_issue
**Description:** Duplicate environment variable: template
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 965
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 966
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 967
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 970
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 971
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 973
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 975
**Type:** environment_config_issue
**Description:** Duplicate environment variable: template
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 977
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 979
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 981
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 982
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 983
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 984
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 987
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 988
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 989
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 990
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 992
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 993
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 994
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 995
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 996
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 997
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 998
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 999
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1000
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1001
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1003
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1004
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1005
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1007
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1008
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1009
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1010
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1011
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1012
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1013
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1016
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1018
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1019
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1020
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1021
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1022
**Type:** environment_config_issue
**Description:** Duplicate environment variable: parent: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1023
**Type:** environment_config_issue
**Description:** Duplicate environment variable: globals: t.Optional[t.MutableMapping[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1024
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1025
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1026
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1027
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1029
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1030
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1031
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1032
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1033
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1034
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1035
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1036
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1038
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1039
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1040
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1042
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1043
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1044
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1045
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1047
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1048
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1049
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1051
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1052
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1053
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1054
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1056
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1057
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1059
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1061
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1062
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1063
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1064
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1065
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1066
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1067
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1068
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1069
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1070
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1072
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1073
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1074
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1075
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1076
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1077
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1078
**Type:** environment_config_issue
**Description:** Duplicate environment variable: parent: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1079
**Type:** environment_config_issue
**Description:** Duplicate environment variable: globals: t.Optional[t.MutableMapping[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1080
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1081
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1082
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1084
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1085
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1086
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1087
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1088
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1089
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1090
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1092
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1093
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1094
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1095
**Type:** environment_config_issue
**Description:** Duplicate environment variable: globals: t.Optional[t.MutableMapping[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1097
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1098
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1099
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1104
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1107
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1111
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1116
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1122
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1124
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1127
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1129
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1133
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1136
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1137
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1143
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1144
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1145
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1146
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1149
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1150
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1151
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1158
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1161
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1163
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1164
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1165
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1167
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1169
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1170
**Type:** environment_config_issue
**Description:** Duplicate environment variable: block_start_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1171
**Type:** environment_config_issue
**Description:** Duplicate environment variable: block_end_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1172
**Type:** environment_config_issue
**Description:** Duplicate environment variable: variable_start_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1173
**Type:** environment_config_issue
**Description:** Duplicate environment variable: variable_end_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1174
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_start_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1175
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_end_string: str
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1176
**Type:** environment_config_issue
**Description:** Duplicate environment variable: line_statement_prefix: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1177
**Type:** environment_config_issue
**Description:** Duplicate environment variable: line_comment_prefix: t.Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1178
**Type:** environment_config_issue
**Description:** Duplicate environment variable: trim_blocks: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1179
**Type:** environment_config_issue
**Description:** Duplicate environment variable: lstrip_blocks: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1180
**Type:** environment_config_issue
**Description:** Duplicate environment variable: newline_sequence: "te.Literal['\\n', '\\r\\n', '\\r']"
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1181
**Type:** environment_config_issue
**Description:** Duplicate environment variable: keep_trailing_newline: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1182
**Type:** environment_config_issue
**Description:** Duplicate environment variable: extensions: t.Sequence[t.Union[str, t.Type["Extension"]]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1183
**Type:** environment_config_issue
**Description:** Duplicate environment variable: optimized: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1184
**Type:** environment_config_issue
**Description:** Duplicate environment variable: undefined: t.Type[Undefined]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1185
**Type:** environment_config_issue
**Description:** Duplicate environment variable: finalize: t.Optional[t.Callable[..., t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1186
**Type:** environment_config_issue
**Description:** Duplicate environment variable: autoescape: t.Union[bool, t.Callable[[t.Optional[str]], bool]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1187
**Type:** environment_config_issue
**Description:** Duplicate environment variable: enable_async: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1189
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1197
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1198
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1202
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1204
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1207
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1208
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1209
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1210
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1211
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1212
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1216
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1217
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1218
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1219
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1220
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1221
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1223
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1224
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1225
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1226
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1228
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1229
**Type:** environment_config_issue
**Description:** Duplicate environment variable: rv
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1231
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1233
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1234
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1235
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1236
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1237
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1238
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1239
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1240
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1241
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1243
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1244
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1245
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1247
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1248
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1249
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1250
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1251
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1252
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1253
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1273
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1275
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1276
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1277
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1278
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1281
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1283
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1284
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1285
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1286
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1288
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1292
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1293
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1294
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1295
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1297
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1298
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1299
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1300
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1302
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1305
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1306
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1307
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1308
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1309
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1311
**Type:** environment_config_issue
**Description:** Duplicate environment variable: ctx
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1313
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1314
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1315
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1316
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1317
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1318
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1320
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1321
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1322
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1323
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1324
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1326
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1327
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1328
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1329
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1330
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1332
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1333
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1334
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1335
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1337
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1338
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1340
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1341
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1343
**Type:** environment_config_issue
**Description:** Duplicate environment variable: ctx
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1345
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1346
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1347
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1348
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1350
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1351
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1352
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1353
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1354
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1355
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1356
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1357
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1358
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1359
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1361
**Type:** environment_config_issue
**Description:** Duplicate environment variable: ctx
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1363
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1365
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1366
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1367
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1368
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1371
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1372
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1373
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1375
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1376
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1380
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1381
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1382
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1383
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1384
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1386
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1387
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1388
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1389
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1390
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1392
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1393
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1394
**Type:** environment_config_issue
**Description:** Duplicate environment variable: vars: t.Optional[t.Dict[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1395
**Type:** environment_config_issue
**Description:** Duplicate environment variable: shared: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1396
**Type:** environment_config_issue
**Description:** Duplicate environment variable: locals: t.Optional[t.Mapping[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1397
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1398
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1399
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1400
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1401
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1402
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1403
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1404
**Type:** environment_config_issue
**Description:** Duplicate environment variable: ctx
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1405
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1407
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1408
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1409
**Type:** environment_config_issue
**Description:** Duplicate environment variable: vars: t.Optional[t.Dict[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1410
**Type:** environment_config_issue
**Description:** Duplicate environment variable: shared: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1411
**Type:** environment_config_issue
**Description:** Duplicate environment variable: locals: t.Optional[t.Mapping[str, t.Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1412
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1413
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1414
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1415
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1416
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1417
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1418
**Type:** environment_config_issue
**Description:** Duplicate environment variable: ctx
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1419
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1420
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1421
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1422
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1423
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1425
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1427
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1428
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1429
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1430
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1432
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1433
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1434
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1435
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1436
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1437
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1438
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1439
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1441
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1444
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1445
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1447
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1450
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1452
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1454
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1455
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1456
**Type:** environment_config_issue
**Description:** Duplicate environment variable: keys
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1458
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1459
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1461
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1462
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self._module
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1464
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1466
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1467
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1468
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1469
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1470
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1473
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1474
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1476
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1478
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1479
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1480
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1482
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1483
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1484
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1485
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1486
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1488
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1489
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1491
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1492
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1493
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1494
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1495
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1496
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1498
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1499
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1500
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1501
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1502
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1504
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1505
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1507
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1509
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1510
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1511
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1512
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1513
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1514
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1517
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1518
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1519
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1520
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1521
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1523
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1524
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1525
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1526
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1528
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1529
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1530
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1531
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1532
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1533
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1534
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1535
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1540
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1543
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1544
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1546
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1547
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1549
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1550
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1551
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1552
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1553
**Type:** environment_config_issue
**Description:** Duplicate environment variable: name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1554
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1557
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1558
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1559
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1560
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1561
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1563
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1567
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1569
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1570
**Type:** environment_config_issue
**Description:** Duplicate environment variable: rv
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1571
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1572
**Type:** environment_config_issue
**Description:** Duplicate environment variable: rv
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1573
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1576
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1577
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1578
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1579
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1580
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1582
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1583
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1584
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1585
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1587
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1589
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1591
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1592
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1593
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1596
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1597
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1598
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1599
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1601
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1604
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1607
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1608
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1612
**Type:** environment_config_issue
**Description:** Duplicate environment variable: close
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1613
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1616
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1617
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1619
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1620
**Type:** environment_config_issue
**Description:** Duplicate environment variable: iterable
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1622
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1623
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1624
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1625
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1626
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1627
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1628
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1629
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1631
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1632
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1636
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1641
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1642
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1643
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1645
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1646
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1648
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1649
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1650
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1651
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1652
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1653
**Type:** environment_config_issue
**Description:** Duplicate environment variable: c_size
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1656
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1658
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1660
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self.buffered
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1661
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self._next
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1663
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1664
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1666
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jinja2/environment.py
**Line:** 1667
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 55
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 56
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env[k]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 58
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 59
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pre_commit/envcontext.py
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 55
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 56
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 66
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 67
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 68
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 70
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 73
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 81
**Type:** environment_config_issue
**Description:** Duplicate environment variable: path
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 84
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 90
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self._env_backend
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 92
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 93
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 96
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 97
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 107
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 111
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 116
**Type:** environment_config_issue
**Description:** Duplicate environment variable: path
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 124
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 125
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 127
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 129
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 133
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 135
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 136
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 143
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 145
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 151
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 158
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 164
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 165
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 167
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 169
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 170
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 171
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 175
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 177
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 179
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 180
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 198
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 202
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 204
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 212
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 217
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 219
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 220
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 221
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 225
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 227
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 228
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 229
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 230
**Type:** environment_config_issue
**Description:** Duplicate environment variable: path
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 231
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 236
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 237
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 238
**Type:** environment_config_issue
**Description:** Duplicate environment variable: path
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 239
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 240
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 242
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 246
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 248
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 249
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 251
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 252
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cmd
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 254
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 257
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cmd +
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 258
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 259
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 260
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 261
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 262
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 263
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 264
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 265
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 267
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 268
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 270
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 271
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 272
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 275
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 276
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 277
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 281
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 282
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 285
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 287
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 289
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 291
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 292
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self._uv_bin
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 294
**Type:** environment_config_issue
**Description:** Duplicate environment variable: venv.EnvBuilder(symlinks
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 297
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 298
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cmd
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 299
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 300
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cmd +
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 303
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 304
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 305
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 309
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 310
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 313
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 318
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 319
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 320
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 321
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 322
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 323
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 326
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 327
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 328
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 330
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 331
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 332
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 336
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 344
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 350
**Type:** environment_config_issue
**Description:** Duplicate environment variable: paths
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 351
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 357
**Type:** environment_config_issue
**Description:** Duplicate environment variable: paths
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 358
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 359
**Type:** environment_config_issue
**Description:** Duplicate environment variable: paths
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 362
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 363
**Type:** environment_config_issue
**Description:** Duplicate environment variable: msg
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 364
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 366
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 370
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 371
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/build/env.py
**Line:** 372
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/env_settings.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/env_settings.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Duplicate environment variable: PYPYVERSION
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 187
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/coverage/env.py
**Line:** 197
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Duplicate environment variable: _env_file: Optional[DotenvType]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Duplicate environment variable: _env_file_encoding: Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 55
**Type:** environment_config_issue
**Description:** Duplicate environment variable: _env_nested_delimiter: Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 56
**Type:** environment_config_issue
**Description:** Duplicate environment variable: _secrets_dir: Optional[StrPath]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 66
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 67
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 69
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 73
**Type:** environment_config_issue
**Description:** Duplicate environment variable: init_settings
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 75
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 80
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 93
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 94
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 100
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 104
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 109
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_names
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 111
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_names
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 113
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_names
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_names
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 122
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 124
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 125
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 127
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 135
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 144
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 145
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 151
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 152
**Type:** environment_config_issue
**Description:** Duplicate environment variable: __slots__
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 154
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 158
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_nested_delimiter: Optional[str]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 167
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 169
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 174
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 178
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 179
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_vars
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 181
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 183
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 185
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 186
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 189
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 197
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 198
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_val
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 204
**Type:** environment_config_issue
**Description:** Duplicate environment variable: d[field.alias]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 206
**Type:** environment_config_issue
**Description:** Duplicate environment variable: d[field.alias]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 207
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 209
**Type:** environment_config_issue
**Description:** Duplicate environment variable: d[field.alias]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 211
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 215
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 216
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 218
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 219
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_files
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 221
**Type:** environment_config_issue
**Description:** Duplicate environment variable: dotenv_vars
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 222
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 224
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 225
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 227
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 229
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 231
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 232
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 233
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 234
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 235
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 236
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 238
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 240
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 241
**Type:** environment_config_issue
**Description:** Duplicate environment variable: allow_parse_failure
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 242
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 243
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 245
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 247
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 248
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 249
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 251
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 252
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 255
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 256
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 257
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 262
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 263
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_var
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 266
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 268
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 269
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 272
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 275
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 276
**Type:** environment_config_issue
**Description:** Duplicate environment variable: __slots__
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 278
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 281
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 282
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 283
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 284
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 287
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 288
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 292
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 293
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 294
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 296
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 297
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 299
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 300
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 302
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 304
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 306
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 308
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 309
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 310
**Type:** environment_config_issue
**Description:** Duplicate environment variable: secret_value
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 311
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 312
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 315
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 316
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 317
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 319
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 320
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 322
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 326
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 328
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 329
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 330
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 331
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 332
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 335
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 336
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 337
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 338
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 341
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 342
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 343
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 344
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 345
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 347
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 349
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic/v1/env_settings.py
**Line:** 350
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/virtualenv/config/env_var.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env["PATH"]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 65
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env["PATH"]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 67
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cmd
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 72
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Duplicate environment variable: shell
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 78
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 80
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 85
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 86
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 91
**Type:** environment_config_issue
**Description:** Duplicate environment variable: data
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 92
**Type:** environment_config_issue
**Description:** Duplicate environment variable: data
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/setuptools/tests/environment.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/weasel/util/environment.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 65
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 67
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 68
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 69
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 71
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 72
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 73
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 79
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 80
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 84
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 85
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 86
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 88
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 91
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 92
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 93
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 96
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 100
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 107
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 109
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 116
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Duplicate environment variable: value
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 122
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 124
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 125
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 133
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 134
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 136
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 137
**Type:** environment_config_issue
**Description:** Duplicate environment variable: allow_parse_failure
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 146
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 149
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 150
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 154
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 158
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 163
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 164
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 167
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 170
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 171
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 173
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 175
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 176
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 177
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 178
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 179
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 182
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 185
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 186
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 197
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 207
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 208
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 210
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 211
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 212
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 214
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 220
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 221
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 223
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 224
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 226
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 227
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 233
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 235
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 236
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_var
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 239
**Type:** environment_config_issue
**Description:** Duplicate environment variable: target_field
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 242
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 243
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 245
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 246
**Type:** environment_config_issue
**Description:** Duplicate environment variable: enum_val
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 247
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_val
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 248
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 250
**Type:** environment_config_issue
**Description:** Duplicate environment variable: is_complex, allow_json_failure
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 251
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 252
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 253
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_val
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 254
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 255
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 256
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 257
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 261
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 263
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 264
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/pydantic_settings/sources/providers/env.py
**Line:** 267
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 58
**Type:** environment_config_issue
**Description:** Duplicate environment variable: download_parser.set_defaults(func
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 65
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 66
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 68
**Type:** environment_config_issue
**Description:** Duplicate environment variable: safetensors_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 69
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 70
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 72
**Type:** environment_config_issue
**Description:** Duplicate environment variable: safetensors_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 78
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 80
**Type:** environment_config_issue
**Description:** Duplicate environment variable: accelerate_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 83
**Type:** environment_config_issue
**Description:** Duplicate environment variable: accelerate_config
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 86
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 87
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 88
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 94
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 97
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pt_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 98
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pt_cuda_available
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 104
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pt_accelerator
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pt_accelerator
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 107
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pt_accelerator
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 109
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 110
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pt_accelerator
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Duplicate environment variable: tf_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 120
**Type:** environment_config_issue
**Description:** Duplicate environment variable: tf_cuda_available
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Duplicate environment variable: tf_cuda_available
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 129
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 130
**Type:** environment_config_issue
**Description:** Duplicate environment variable: deepspeed_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 136
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 137
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 141
**Type:** environment_config_issue
**Description:** Duplicate environment variable: flax_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 142
**Type:** environment_config_issue
**Description:** Duplicate environment variable: jax_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 143
**Type:** environment_config_issue
**Description:** Duplicate environment variable: jaxlib_version
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 144
**Type:** environment_config_issue
**Description:** Duplicate environment variable: jax_backend
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 149
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 150
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 151
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 153
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 154
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 158
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 161
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 163
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 169
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 177
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 178
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 180
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 182
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 183
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/transformers/commands/env.py
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 55
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 56
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 58
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 59
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 65
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 78
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 80
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 87
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 90
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 91
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 93
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 94
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 96
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 97
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 109
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 125
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/safety/tool/environment_diff.py
**Line:** 129
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/torch/include/c10/util/env.h
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 55
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 56
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 58
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 65
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 66
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 73
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 75
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 79
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 83
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 84
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 85
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 86
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 87
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 92
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 93
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 94
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 96
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 97
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 100
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 104
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 111
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 116
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 122
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 129
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 133
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 134
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self._start_executable
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 135
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self.path
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 136
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self.version_info
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 137
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self._env_vars
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 144
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 145
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 146
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 149
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 151
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 170
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 173
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 176
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 178
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 179
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 180
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 181
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 185
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 186
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 187
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 189
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 202
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 207
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 226
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 228
**Type:** environment_config_issue
**Description:** Duplicate environment variable: checks
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 229
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 230
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 231
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 232
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 233
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 235
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 237
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 239
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 242
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 245
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 246
**Type:** environment_config_issue
**Description:** Duplicate environment variable: var
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 254
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 255
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 256
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 260
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 261
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 262
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 263
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 268
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 272
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 273
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 274
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 275
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 276
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 277
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 278
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 279
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 280
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 281
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 282
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 283
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 284
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 286
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 287
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 288
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 293
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 296
**Type:** environment_config_issue
**Description:** Duplicate environment variable: virtual_env
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 297
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 298
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 299
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 301
**Type:** environment_config_issue
**Description:** Duplicate environment variable: conda_env
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 302
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 303
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 304
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 306
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 307
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 308
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 311
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 313
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 315
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 316
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 318
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 320
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 321
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 322
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 326
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 327
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 328
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 329
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 331
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 333
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 334
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 335
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 336
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 338
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 339
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 345
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 346
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 347
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 349
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 350
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 351
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 353
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 355
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 356
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 358
**Type:** environment_config_issue
**Description:** Duplicate environment variable: if os.name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 359
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 360
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 362
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 363
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 364
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 368
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 369
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 370
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 372
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 373
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 374
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 375
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 376
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 382
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 383
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 384
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 386
**Type:** environment_config_issue
**Description:** Duplicate environment variable: if os.name
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 388
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 389
**Type:** environment_config_issue
**Description:** Duplicate environment variable: pythons
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 390
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 391
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 392
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 393
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 394
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 396
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 397
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 400
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 401
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 405
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 406
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 407
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 408
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 409
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 410
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 411
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 413
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 414
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 416
**Type:** environment_config_issue
**Description:** Duplicate environment variable: exe
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 417
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 418
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 419
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 420
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 423
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 424
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 425
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 426
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 429
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 434
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 435
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 440
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 442
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 453
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 454
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 457
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 458
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 461
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 476
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 477
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 479
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/api/environment.py
**Line:** 480
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 45
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 73
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 75
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 78
**Type:** environment_config_issue
**Description:** Duplicate environment variable: block_start_string: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 79
**Type:** environment_config_issue
**Description:** Duplicate environment variable: block_end_string: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 80
**Type:** environment_config_issue
**Description:** Duplicate environment variable: variable_start_string: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 81
**Type:** environment_config_issue
**Description:** Duplicate environment variable: variable_end_string: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 82
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_start_string: Any
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 83
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_end_string: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 84
**Type:** environment_config_issue
**Description:** Duplicate environment variable: line_statement_prefix: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 85
**Type:** environment_config_issue
**Description:** Duplicate environment variable: line_comment_prefix: Text
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 86
**Type:** environment_config_issue
**Description:** Duplicate environment variable: trim_blocks: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 87
**Type:** environment_config_issue
**Description:** Duplicate environment variable: lstrip_blocks: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 88
**Type:** environment_config_issue
**Description:** Duplicate environment variable: extensions: List[Any]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 89
**Type:** environment_config_issue
**Description:** Duplicate environment variable: optimized: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 90
**Type:** environment_config_issue
**Description:** Duplicate environment variable: undefined: Type[Undefined]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 93
**Type:** environment_config_issue
**Description:** Duplicate environment variable: loader: Optional[BaseLoader]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 94
**Type:** environment_config_issue
**Description:** Duplicate environment variable: cache_size: int
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 95
**Type:** environment_config_issue
**Description:** Duplicate environment variable: auto_reload: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 96
**Type:** environment_config_issue
**Description:** Duplicate environment variable: bytecode_cache: Optional[BytecodeCache]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 97
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 100
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 104
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 134
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 135
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 137
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 143
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 144
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 146
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 154
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 161
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 163
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 164
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 169
**Type:** environment_config_issue
**Description:** Duplicate environment variable: comment_start_string: Any
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 178
**Type:** environment_config_issue
**Description:** Duplicate environment variable: optimized: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 181
**Type:** environment_config_issue
**Description:** Duplicate environment variable: autoescape: bool
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 182
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 186
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 187
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 189
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 195
**Type:** environment_config_issue
**Description:** Duplicate environment variable: self, vars: Optional[Dict[str, Any]]
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 197
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 198
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 202
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 204
**Type:** environment_config_issue
**Description:** Duplicate environment variable: if sys.version_info >
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 208
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 209
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 210
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 211
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 214
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 215
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 217
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 218
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 220
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 221
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 223
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/jedi/third_party/typeshed/third_party/2and3/jinja2/environment.pyi
**Line:** 224
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 51
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 66
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 67
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 70
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 72
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/google/auth/environment_vars.py
**Line:** 73
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/huggingface_hub/commands/env.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 14
**Type:** environment_config_issue
**Description:** Duplicate environment variable: x
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 46
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 58
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 59
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 65
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 70
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 72
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 73
**Type:** environment_config_issue
**Description:** Duplicate environment variable: add_args_to_env(builder, local
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 79
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 80
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 84
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 85
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 86
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 87
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 88
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 90
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 91
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 92
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 104
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 106
**Type:** environment_config_issue
**Description:** Duplicate environment variable: add_args_to_env(builder, local
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 111
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 124
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 125
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 127
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 133
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 135
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 143
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 151
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 153
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 154
**Type:** environment_config_issue
**Description:** Duplicate environment variable: base.prev_env_reg
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 161
**Type:** environment_config_issue
**Description:** Duplicate environment variable: outer_env
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 162
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_reg
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 163
**Type:** environment_config_issue
**Description:** Duplicate environment variable: index -
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 170
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 175
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 176
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 180
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 181
**Type:** environment_config_issue
**Description:** Duplicate environment variable: fn_info
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 185
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 193
**Type:** environment_config_issue
**Description:** Duplicate environment variable: rtype
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 198
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 202
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 204
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 208
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 210
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 211
**Type:** environment_config_issue
**Description:** Duplicate environment variable: env_for_func
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 216
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 217
**Type:** environment_config_issue
**Description:** Duplicate environment variable: rtype
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 220
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 221
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 222
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 228
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 230
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 233
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 234
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 236
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 237
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 238
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 239
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 240
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 245
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 250
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 251
**Type:** environment_config_issue
**Description:** Duplicate environment variable: prev_env_reg
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 257
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 260
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 261
**Type:** environment_config_issue
**Description:** Duplicate environment variable: fitem
**Recommendation:** Remove duplicate variable definitions
**Rule ID:** ENV_DUPLICATE_VAR

### backend/venv/lib/python3.13/site-packages/mypyc/irbuild/env_class.py
**Line:** 262
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/.mypy_cache/3.9/pydantic/v1/env_settings.meta.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/.mypy_cache/3.9/pydantic/v1/env_settings.data.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/.mypy_cache/3.9/pydantic_settings/sources/providers/env.meta.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/.mypy_cache/3.9/pydantic_settings/sources/providers/env.data.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/.mypy_cache/3.9/google/auth/environment_vars.meta.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### backend/.mypy_cache/3.9/google/auth/environment_vars.data.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/environments.d.ts
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/environment.d.ts
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment-cMiGIVXz.d.ts
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment-cMiGIVXz.d.ts
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment-cMiGIVXz.d.ts
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment-cMiGIVXz.d.ts
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment-cMiGIVXz.d.ts
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment-cMiGIVXz.d.ts
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.d.ts
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 34
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 39
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@vitest/snapshot/dist/environment.js
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@babel/core/lib/config/helpers/environment.js
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vite/dist/client/env.mjs
**Line:** 24
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 23
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 27
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 30
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 33
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.d.ts
**Line:** 35
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.js
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/environments.js
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 5
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 9
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 11
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 15
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/chunks/environments-node.vcoXCoKs.js
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/vendor/env.AtSIuHFg.js
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/vendor/env.AtSIuHFg.js
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/vitest/dist/vendor/env.AtSIuHFg.js
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 2
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 3
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 4
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 6
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 7
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 8
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 10
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 12
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 13
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 14
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 16
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 17
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 18
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 19
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 20
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 21
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 22
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 25
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 26
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 28
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 29
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 31
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 32
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 36
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 37
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 38
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 40
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 41
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 42
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 43
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 44
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 47
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 48
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 49
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 50
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 52
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 53
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 54
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 56
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 57
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 59
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 60
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 61
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 62
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 63
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 64
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 65
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 66
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 67
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 68
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 69
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 70
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 71
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 72
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 73
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 74
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 75
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 76
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 77
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 78
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 79
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 80
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 81
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 82
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 83
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 84
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 85
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 86
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 87
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 88
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 89
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 90
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 91
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 92
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 93
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 94
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 95
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 96
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 97
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 98
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 99
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 100
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 101
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 102
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 103
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 104
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 105
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 106
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 107
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 108
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 109
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 110
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 111
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 112
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 113
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 114
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 115
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 116
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 117
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 118
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 119
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 120
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 121
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 122
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 123
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 124
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 125
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 126
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 127
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 128
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 130
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 131
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 132
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 133
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 134
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 135
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 136
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 137
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 138
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 139
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 140
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 141
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 142
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 143
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 144
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 145
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 146
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 147
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 148
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 149
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 150
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 152
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 153
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 154
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 155
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 156
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 157
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 158
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 159
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 160
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 161
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 162
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 163
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 164
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 165
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 166
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 167
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 168
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 169
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 170
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 171
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 172
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 173
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 174
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 175
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 176
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 177
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 178
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 179
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 180
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 181
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 182
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 183
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 184
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 185
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 186
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 187
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 188
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 189
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 190
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 191
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 192
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 193
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 194
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 195
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 196
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 197
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 198
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 199
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 200
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 201
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 202
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 203
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 204
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 205
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 206
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 207
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 208
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 209
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 210
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 211
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 212
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 213
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 214
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/@eslint/eslintrc/conf/environments.js
**Line:** 215
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

### node_modules/node-releases/data/processed/envs.json
**Line:** 1
**Type:** environment_config_issue
**Description:** Invalid environment variable format
**Recommendation:** Use KEY=value format
**Rule ID:** ENV_INVALID_FORMAT

## Low Issues (171)

### Dockerfile.backend
**Line:** 12
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.backend
**Line:** 43
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.nginx
**Line:** 5
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.frontend
**Line:** 8
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.backup
**Line:** 10
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### backend/Dockerfile
**Line:** 6
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### monitoring/exporters/zotero/Dockerfile
**Line:** 7
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### config/dockerfiles/Dockerfile.streamlit
**Line:** 7
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### config/dockerfiles/Dockerfile.backend
**Line:** 11
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### config/dockerfiles/Dockerfile.backend
**Line:** 35
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.backend
**Line:** 12
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.backend
**Line:** 43
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.nginx
**Line:** 5
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.frontend
**Line:** 8
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### Dockerfile.backup
**Line:** 10
**Type:** dockerfile_issue
**Description:** Missing apt cache cleanup
**Recommendation:** Add '&& rm -rf /var/lib/apt/lists/*' to reduce image size
**Ubuntu Specific:** Yes
**Rule ID:** DOCKERFILE_APT_CLEANUP

### docker-compose.prod.yml
**Type:** docker_compose_issue
**Description:** Service 'certbot' missing restart policy
**Recommendation:** Add restart policy (e.g., 'unless-stopped')
**Rule ID:** COMPOSE_NO_RESTART_POLICY

### simple-deploy.sh
**Line:** 64
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### simple-deploy.sh
**Line:** 65
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### deploy-with-ai-services.sh
**Line:** 44
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### deploy-local.sh
**Line:** 57
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### deploy-local.sh
**Line:** 58
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 181
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 201
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 239
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 240
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 244
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 253
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 295
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 298
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 324
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 325
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 364
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 365
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 380
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 406
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 410
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 424
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 427
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 538
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 590
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 604
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 605
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 606
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 607
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 611
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 614
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 636
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 655
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### production-deploy.sh
**Line:** 656
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-integration.sh
**Line:** 58
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 74
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 113
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 204
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-integration.sh
**Line:** 248
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 292
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-with-monitoring.sh
**Line:** 34
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 67
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 68
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 72
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 73
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 91
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 92
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 119
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 67
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 138
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 207
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 252
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 253
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 302
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/validate-deployment-config.sh
**Line:** 78
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/validate-deployment-config.sh
**Line:** 83
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/validate-deployment-config.sh
**Line:** 316
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/validate-deployment-config.sh
**Line:** 317
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 33
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 65
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 66
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 70
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 71
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 89
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 90
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 114
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/validate-deployment.sh
**Line:** 32
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/validate-deployment.sh
**Line:** 266
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/validate-deployment.sh
**Line:** 267
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/deploy.sh
**Line:** 32
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/production-deploy.sh
**Line:** 311
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/production-deploy.sh
**Line:** 333
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/production-deploy.sh
**Line:** 343
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/production-deploy.sh
**Line:** 344
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/blue-green-deployment.sh
**Line:** 32
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/blue-green-deployment.sh
**Line:** 33
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/blue-green-deployment.sh
**Line:** 41
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deployment/blue-green-deployment.sh
**Line:** 219
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/blue-green-deployment.sh
**Line:** 220
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/blue-green-deployment.sh
**Line:** 283
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### deploy-with-ai-services.sh
**Line:** 44
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### deploy-local.sh
**Line:** 57
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### deploy-local.sh
**Line:** 58
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-integration.sh
**Line:** 58
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 74
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 113
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 204
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-integration.sh
**Line:** 248
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-zotero-integration.sh
**Line:** 292
**Type:** deployment_script_issue
**Description:** Shell compatibility issue: source 
**Recommendation:** Use . instead of source for POSIX compatibility
**Rule ID:** SCRIPT_SHELL_COMPATIBILITY

### scripts/deploy-with-monitoring.sh
**Line:** 34
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 67
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 68
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 72
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 73
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 91
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 92
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-with-monitoring.sh
**Line:** 119
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 67
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 138
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 207
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 252
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 253
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy-zotero-production.sh
**Line:** 302
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 33
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 65
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 66
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 70
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 71
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 89
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 90
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deploy.sh
**Line:** 114
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/deployment/deploy.sh
**Line:** 32
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 35
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 80
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 166
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 167
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 173
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 185
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 186
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 200
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 204
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 310
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-ssl-setup.sh
**Line:** 311
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /usr/local/bin
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 42
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 48
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 52
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 56
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 134
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 144
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 238
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### setup-nginx-proxy.sh
**Line:** 239
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### quick-nginx-setup.sh
**Line:** 197
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### quick-nginx-setup.sh
**Line:** 216
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 32
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 34
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 39
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 41
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 168
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 180
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### nginx-monitoring-setup.sh
**Line:** 481
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/setup-ssl.sh
**Line:** 79
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/setup-ssl.sh
**Line:** 80
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/setup-ssl.sh
**Line:** 107
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/setup-ssl.sh
**Line:** 108
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /etc
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### scripts/setup-ssl.sh
**Line:** 241
**Type:** ubuntu_compatibility
**Description:** Hardcoded path may not exist: /opt
**Recommendation:** Check path existence before using
**Ubuntu Specific:** Yes
**Rule ID:** SCRIPT_HARDCODED_PATH

### config/deployment/development.env
**Line:** 24
**Type:** environment_config_issue
**Description:** Empty environment variable: REDIS_PASSWORD
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 66
**Type:** environment_config_issue
**Description:** Empty environment variable: SENTRY_DSN
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 79
**Type:** environment_config_issue
**Description:** Empty environment variable: SMTP_USER
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 80
**Type:** environment_config_issue
**Description:** Empty environment variable: SMTP_PASSWORD
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 85
**Type:** environment_config_issue
**Description:** Empty environment variable: SLACK_WEBHOOK_URL
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 86
**Type:** environment_config_issue
**Description:** Empty environment variable: PAGERDUTY_INTEGRATION_KEY
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 120
**Type:** environment_config_issue
**Description:** Empty environment variable: SSL_CERT_PATH
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 121
**Type:** environment_config_issue
**Description:** Empty environment variable: SSL_KEY_PATH
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 129
**Type:** environment_config_issue
**Description:** Empty environment variable: BACKUP_S3_BUCKET
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 130
**Type:** environment_config_issue
**Description:** Empty environment variable: BACKUP_S3_ACCESS_KEY
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

### config/deployment/development.env
**Line:** 131
**Type:** environment_config_issue
**Description:** Empty environment variable: BACKUP_S3_SECRET_KEY
**Recommendation:** Provide default value or remove unused variable
**Rule ID:** ENV_EMPTY_VALUE

## Ubuntu Compatibility Issues (188)

The following issues are specific to Ubuntu compatibility:

- **Dockerfile.backend**: Missing apt cache cleanup
- **Dockerfile.backend**: Missing apt cache cleanup
- **Dockerfile.nginx**: Missing apt cache cleanup
- **Dockerfile.frontend**: Missing apt cache cleanup
- **Dockerfile.backup**: Missing apt cache cleanup
- **backend/Dockerfile**: Missing apt cache cleanup
- **monitoring/exporters/zotero/Dockerfile**: Missing apt cache cleanup
- **config/dockerfiles/Dockerfile.streamlit**: Missing apt cache cleanup
- **config/dockerfiles/Dockerfile.backend**: Missing apt cache cleanup
- **config/dockerfiles/Dockerfile.backend**: Missing apt cache cleanup
- **Dockerfile.backend**: Missing apt cache cleanup
- **Dockerfile.backend**: Missing apt cache cleanup
- **Dockerfile.nginx**: Missing apt cache cleanup
- **Dockerfile.frontend**: Missing apt cache cleanup
- **Dockerfile.backup**: Missing apt cache cleanup
- **simple-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **simple-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **deploy-local.sh**: Hardcoded path may not exist: /usr/local/bin
- **deploy-local.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /etc
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Ubuntu incompatible command: systemctl
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Hardcoded path may not exist: /opt
- **production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy-zotero-integration.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy-with-monitoring.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-with-monitoring.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /opt
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-zotero-production.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Ubuntu incompatible command: systemctl
- **scripts/validate-deployment-config.sh**: Hardcoded path may not exist: /etc
- **scripts/validate-deployment-config.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy.sh**: Hardcoded path may not exist: /opt
- **scripts/deployment/validate-deployment.sh**: Hardcoded path may not exist: /opt
- **scripts/deployment/validate-deployment.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/validate-deployment.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/validate-deployment.sh**: Ubuntu incompatible command: yum
- **scripts/deployment/validate-deployment.sh**: Ubuntu incompatible command: yum
- **scripts/deployment/deploy.sh**: Hardcoded path may not exist: /opt
- **scripts/deployment/production-deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/production-deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deployment/production-deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deployment/production-deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deployment/production-deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deployment/production-deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deployment/production-deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deployment/blue-green-deployment.sh**: Hardcoded path may not exist: /opt
- **scripts/deployment/blue-green-deployment.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/blue-green-deployment.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/blue-green-deployment.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/blue-green-deployment.sh**: Hardcoded path may not exist: /etc
- **scripts/deployment/blue-green-deployment.sh**: Ubuntu incompatible command: systemctl
- **deploy-local.sh**: Hardcoded path may not exist: /usr/local/bin
- **deploy-local.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy-zotero-integration.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy-with-monitoring.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-with-monitoring.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-with-monitoring.sh**: Hardcoded path may not exist: /opt
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-zotero-production.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy-zotero-production.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy-zotero-production.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /etc
- **scripts/deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy.sh**: Hardcoded path may not exist: /usr/local/bin
- **scripts/deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy.sh**: Ubuntu incompatible command: systemctl
- **scripts/deploy.sh**: Hardcoded path may not exist: /opt
- **scripts/deployment/deploy.sh**: Hardcoded path may not exist: /opt
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Ubuntu incompatible command: yum
- **nginx-ssl-setup.sh**: Ubuntu incompatible command: dnf
- **nginx-ssl-setup.sh**: Ubuntu incompatible command: systemctl
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /usr/local/bin
- **nginx-ssl-setup.sh**: Ubuntu incompatible command: systemctl
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Ubuntu incompatible command: systemctl
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /usr/local/bin
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /usr/local/bin
- **nginx-ssl-setup.sh**: Ubuntu incompatible command: systemctl
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-ssl-setup.sh**: Hardcoded path may not exist: /usr/local/bin
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Ubuntu incompatible command: yum
- **setup-nginx-proxy.sh**: Ubuntu incompatible command: dnf
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Hardcoded path may not exist: /etc
- **setup-nginx-proxy.sh**: Ubuntu incompatible command: systemctl
- **setup-nginx-proxy.sh**: Ubuntu incompatible command: systemctl
- **quick-nginx-setup.sh**: Hardcoded path may not exist: /opt
- **quick-nginx-setup.sh**: Hardcoded path may not exist: /opt
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /opt
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /opt
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-monitoring-setup.sh**: Hardcoded path may not exist: /etc
- **nginx-monitoring-setup.sh**: Ubuntu incompatible command: systemctl
- **nginx-monitoring-setup.sh**: Ubuntu incompatible command: systemctl
- **nginx-monitoring-setup.sh**: Ubuntu incompatible command: systemctl
- **scripts/setup-ssl.sh**: Hardcoded path may not exist: /etc
- **scripts/setup-ssl.sh**: Hardcoded path may not exist: /etc
- **scripts/setup-ssl.sh**: Hardcoded path may not exist: /etc
- **scripts/setup-ssl.sh**: Hardcoded path may not exist: /etc
- **scripts/setup-ssl.sh**: Hardcoded path may not exist: /opt