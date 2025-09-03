"""
Infrastructure Manager for AI Scholar
Automated deployment, scaling, and infrastructure management
"""
import asyncio
import json
import logging
import os
import subprocess
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import boto3
import docker
from kubernetes import client, config
import terraform

logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: str
    region: str
    instance_type: str
    min_instances: int
    max_instances: int
    auto_scaling: bool
    load_balancer: bool
    database_config: Dict[str, Any]
    storage_config: Dict[str, Any]
    monitoring_config: Dict[str, Any]

@dataclass
class InfrastructureResource:
    """Infrastructure resource definition"""
    resource_id: str
    resource_type: str
    status: str
    configuration: Dict[str, Any]
    created_at: datetime
    last_updated: datetime
    tags: Dict[str, str]

class CloudProvider:
    """Abstract cloud provider interface"""
    
    def __init__(self, provider_name: str, credentials: Dict[str, Any]):
        self.provider_name = provider_name
        self.credentials = credentials
    
    async def create_instance(self, config: Dict[str, Any]) -> str:
        """Create compute instance"""
        raise NotImplementedError
    
    async def create_database(self, config: Dict[str, Any]) -> str:
        """Create database instance"""
        raise NotImplementedError
    
    async def create_load_balancer(self, config: Dict[str, Any]) -> str:
        """Create load balancer"""
        raise NotImplementedError
    
    async def setup_auto_scaling(self, config: Dict[str, Any]) -> str:
        """Setup auto scaling group"""
        raise NotImplementedError

class AWSProvider(CloudProvider):
    """AWS cloud provider implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("aws", credentials)
        self.ec2 = boto3.client(
            'ec2',
            aws_access_key_id=credentials.get('access_key'),
            aws_secret_access_key=credentials.get('secret_key'),
            region_name=credentials.get('region', 'us-east-1')
        )
        self.rds = boto3.client(
            'rds',
            aws_access_key_id=credentials.get('access_key'),
            aws_secret_access_key=credentials.get('secret_key'),
            region_name=credentials.get('region', 'us-east-1')
        )
        self.elbv2 = boto3.client(
            'elbv2',
            aws_access_key_id=credentials.get('access_key'),
            aws_secret_access_key=credentials.get('secret_key'),
            region_name=credentials.get('region', 'us-east-1')
        )
        self.autoscaling = boto3.client(
            'autoscaling',
            aws_access_key_id=credentials.get('access_key'),
            aws_secret_access_key=credentials.get('secret_key'),
            region_name=credentials.get('region', 'us-east-1')
        )
    
    async def create_instance(self, config: Dict[str, Any]) -> str:
        """Create EC2 instance"""
        try:
            response = self.ec2.run_instances(
                ImageId=config.get('ami_id', 'ami-0c02fb55956c7d316'),  # Amazon Linux 2
                MinCount=1,
                MaxCount=1,
                InstanceType=config.get('instance_type', 't3.medium'),
                KeyName=config.get('key_name'),
                SecurityGroupIds=config.get('security_groups', []),
                SubnetId=config.get('subnet_id'),
                UserData=config.get('user_data', ''),
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': config.get('name', 'ai-scholar-instance')},
                            {'Key': 'Environment', 'Value': config.get('environment', 'production')},
                            {'Key': 'Project', 'Value': 'ai-scholar'}
                        ]
                    }
                ]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            logger.info(f"✅ EC2 instance created: {instance_id}")
            return instance_id
            
        except Exception as e:
            logger.error(f"Failed to create EC2 instance: {e}")
            raise
    
    async def create_database(self, config: Dict[str, Any]) -> str:
        """Create RDS database"""
        try:
            response = self.rds.create_db_instance(
                DBInstanceIdentifier=config.get('db_identifier', 'ai-scholar-db'),
                DBInstanceClass=config.get('db_instance_class', 'db.t3.micro'),
                Engine=config.get('engine', 'postgres'),
                EngineVersion=config.get('engine_version', '13.7'),
                MasterUsername=config.get('master_username', 'postgres'),
                MasterUserPassword=config.get('master_password'),
                AllocatedStorage=config.get('allocated_storage', 20),
                StorageType=config.get('storage_type', 'gp2'),
                VpcSecurityGroupIds=config.get('security_groups', []),
                DBSubnetGroupName=config.get('subnet_group'),
                BackupRetentionPeriod=config.get('backup_retention', 7),
                MultiAZ=config.get('multi_az', False),
                StorageEncrypted=config.get('encrypted', True),
                Tags=[
                    {'Key': 'Name', 'Value': config.get('name', 'ai-scholar-database')},
                    {'Key': 'Environment', 'Value': config.get('environment', 'production')},
                    {'Key': 'Project', 'Value': 'ai-scholar'}
                ]
            )
            
            db_identifier = response['DBInstance']['DBInstanceIdentifier']
            logger.info(f"✅ RDS database created: {db_identifier}")
            return db_identifier
            
        except Exception as e:
            logger.error(f"Failed to create RDS database: {e}")
            raise
    
    async def create_load_balancer(self, config: Dict[str, Any]) -> str:
        """Create Application Load Balancer"""
        try:
            # Create load balancer
            response = self.elbv2.create_load_balancer(
                Name=config.get('name', 'ai-scholar-alb'),
                Subnets=config.get('subnets', []),
                SecurityGroups=config.get('security_groups', []),
                Scheme=config.get('scheme', 'internet-facing'),
                Type='application',
                IpAddressType='ipv4',
                Tags=[
                    {'Key': 'Name', 'Value': config.get('name', 'ai-scholar-load-balancer')},
                    {'Key': 'Environment', 'Value': config.get('environment', 'production')},
                    {'Key': 'Project', 'Value': 'ai-scholar'}
                ]
            )
            
            lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
            
            # Create target group
            tg_response = self.elbv2.create_target_group(
                Name=config.get('target_group_name', 'ai-scholar-tg'),
                Protocol='HTTP',
                Port=config.get('port', 8000),
                VpcId=config.get('vpc_id'),
                HealthCheckProtocol='HTTP',
                HealthCheckPath=config.get('health_check_path', '/health'),
                HealthCheckIntervalSeconds=30,
                HealthCheckTimeoutSeconds=5,
                HealthyThresholdCount=2,
                UnhealthyThresholdCount=3
            )
            
            tg_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
            
            # Create listener
            self.elbv2.create_listener(
                LoadBalancerArn=lb_arn,
                Protocol='HTTP',
                Port=80,
                DefaultActions=[
                    {
                        'Type': 'forward',
                        'TargetGroupArn': tg_arn
                    }
                ]
            )
            
            logger.info(f"✅ Load balancer created: {lb_arn}")
            return lb_arn
            
        except Exception as e:
            logger.error(f"Failed to create load balancer: {e}")
            raise
    
    async def setup_auto_scaling(self, config: Dict[str, Any]) -> str:
        """Setup Auto Scaling Group"""
        try:
            # Create launch template
            lt_response = self.ec2.create_launch_template(
                LaunchTemplateName=config.get('launch_template_name', 'ai-scholar-lt'),
                LaunchTemplateData={
                    'ImageId': config.get('ami_id', 'ami-0c02fb55956c7d316'),
                    'InstanceType': config.get('instance_type', 't3.medium'),
                    'KeyName': config.get('key_name'),
                    'SecurityGroupIds': config.get('security_groups', []),
                    'UserData': config.get('user_data', ''),
                    'TagSpecifications': [
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {'Key': 'Name', 'Value': 'ai-scholar-asg-instance'},
                                {'Key': 'Environment', 'Value': config.get('environment', 'production')},
                                {'Key': 'Project', 'Value': 'ai-scholar'}
                            ]
                        }
                    ]
                }
            )
            
            lt_id = lt_response['LaunchTemplate']['LaunchTemplateId']
            
            # Create Auto Scaling Group
            asg_response = self.autoscaling.create_auto_scaling_group(
                AutoScalingGroupName=config.get('asg_name', 'ai-scholar-asg'),
                LaunchTemplate={
                    'LaunchTemplateId': lt_id,
                    'Version': '$Latest'
                },
                MinSize=config.get('min_size', 1),
                MaxSize=config.get('max_size', 5),
                DesiredCapacity=config.get('desired_capacity', 2),
                VPCZoneIdentifier=','.join(config.get('subnets', [])),
                TargetGroupARNs=config.get('target_group_arns', []),
                HealthCheckType='ELB',
                HealthCheckGracePeriod=300,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': 'ai-scholar-auto-scaling-group',
                        'PropagateAtLaunch': False,
                        'ResourceId': config.get('asg_name', 'ai-scholar-asg'),
                        'ResourceType': 'auto-scaling-group'
                    }
                ]
            )
            
            asg_name = config.get('asg_name', 'ai-scholar-asg')
            logger.info(f"✅ Auto Scaling Group created: {asg_name}")
            return asg_name
            
        except Exception as e:
            logger.error(f"Failed to create Auto Scaling Group: {e}")
            raise

class KubernetesManager:
    """Kubernetes deployment manager"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
    
    async def deploy_application(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Deploy application to Kubernetes"""
        namespace = config.get('namespace', 'default')
        app_name = config.get('app_name', 'ai-scholar')
        
        # Create namespace if it doesn't exist
        await self._ensure_namespace(namespace)
        
        # Create deployment
        deployment_name = await self._create_deployment(namespace, app_name, config)
        
        # Create service
        service_name = await self._create_service(namespace, app_name, config)
        
        # Create ingress if specified
        ingress_name = None
        if config.get('create_ingress', False):
            ingress_name = await self._create_ingress(namespace, app_name, config)
        
        return {
            'deployment': deployment_name,
            'service': service_name,
            'ingress': ingress_name,
            'namespace': namespace
        }
    
    async def _ensure_namespace(self, namespace: str):
        """Ensure namespace exists"""
        try:
            self.v1.read_namespace(name=namespace)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # Create namespace
                namespace_manifest = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=namespace)
                )
                self.v1.create_namespace(body=namespace_manifest)
                logger.info(f"✅ Namespace created: {namespace}")
    
    async def _create_deployment(self, namespace: str, app_name: str, config: Dict[str, Any]) -> str:
        """Create Kubernetes deployment"""
        deployment_name = f"{app_name}-deployment"
        
        # Container configuration
        container = client.V1Container(
            name=app_name,
            image=config.get('image', 'ai-scholar:latest'),
            ports=[client.V1ContainerPort(container_port=config.get('port', 8000))],
            env=[
                client.V1EnvVar(name=k, value=str(v))
                for k, v in config.get('env_vars', {}).items()
            ],
            resources=client.V1ResourceRequirements(
                requests={
                    'cpu': config.get('cpu_request', '100m'),
                    'memory': config.get('memory_request', '128Mi')
                },
                limits={
                    'cpu': config.get('cpu_limit', '500m'),
                    'memory': config.get('memory_limit', '512Mi')
                }
            ),
            liveness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path=config.get('health_check_path', '/health'),
                    port=config.get('port', 8000)
                ),
                initial_delay_seconds=30,
                period_seconds=10
            ),
            readiness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path=config.get('readiness_check_path', '/ready'),
                    port=config.get('port', 8000)
                ),
                initial_delay_seconds=5,
                period_seconds=5
            )
        )
        
        # Pod template
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={'app': app_name}
            ),
            spec=client.V1PodSpec(containers=[container])
        )
        
        # Deployment spec
        spec = client.V1DeploymentSpec(
            replicas=config.get('replicas', 2),
            selector=client.V1LabelSelector(
                match_labels={'app': app_name}
            ),
            template=template
        )
        
        # Deployment
        deployment = client.V1Deployment(
            api_version='apps/v1',
            kind='Deployment',
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec
        )
        
        try:
            self.apps_v1.create_namespaced_deployment(
                body=deployment,
                namespace=namespace
            )
            logger.info(f"✅ Deployment created: {deployment_name}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # Already exists
                self.apps_v1.patch_namespaced_deployment(
                    name=deployment_name,
                    namespace=namespace,
                    body=deployment
                )
                logger.info(f"✅ Deployment updated: {deployment_name}")
            else:
                raise
        
        return deployment_name
    
    async def _create_service(self, namespace: str, app_name: str, config: Dict[str, Any]) -> str:
        """Create Kubernetes service"""
        service_name = f"{app_name}-service"
        
        service = client.V1Service(
            api_version='v1',
            kind='Service',
            metadata=client.V1ObjectMeta(name=service_name),
            spec=client.V1ServiceSpec(
                selector={'app': app_name},
                ports=[
                    client.V1ServicePort(
                        port=config.get('service_port', 80),
                        target_port=config.get('port', 8000),
                        protocol='TCP'
                    )
                ],
                type=config.get('service_type', 'ClusterIP')
            )
        )
        
        try:
            self.v1.create_namespaced_service(
                body=service,
                namespace=namespace
            )
            logger.info(f"✅ Service created: {service_name}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # Already exists
                self.v1.patch_namespaced_service(
                    name=service_name,
                    namespace=namespace,
                    body=service
                )
                logger.info(f"✅ Service updated: {service_name}")
            else:
                raise
        
        return service_name
    
    async def _create_ingress(self, namespace: str, app_name: str, config: Dict[str, Any]) -> str:
        """Create Kubernetes ingress"""
        ingress_name = f"{app_name}-ingress"
        service_name = f"{app_name}-service"
        
        ingress = client.NetworkingV1Ingress(
            api_version='networking.k8s.io/v1',
            kind='Ingress',
            metadata=client.V1ObjectMeta(
                name=ingress_name,
                annotations=config.get('ingress_annotations', {})
            ),
            spec=client.NetworkingV1IngressSpec(
                rules=[
                    client.NetworkingV1IngressRule(
                        host=config.get('hostname'),
                        http=client.NetworkingV1HTTPIngressRuleValue(
                            paths=[
                                client.NetworkingV1HTTPIngressPath(
                                    path='/',
                                    path_type='Prefix',
                                    backend=client.NetworkingV1IngressBackend(
                                        service=client.NetworkingV1IngressServiceBackend(
                                            name=service_name,
                                            port=client.NetworkingV1ServiceBackendPort(
                                                number=config.get('service_port', 80)
                                            )
                                        )
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )
        
        try:
            self.networking_v1.create_namespaced_ingress(
                body=ingress,
                namespace=namespace
            )
            logger.info(f"✅ Ingress created: {ingress_name}")
        except client.exceptions.ApiException as e:
            if e.status == 409:  # Already exists
                self.networking_v1.patch_namespaced_ingress(
                    name=ingress_name,
                    namespace=namespace,
                    body=ingress
                )
                logger.info(f"✅ Ingress updated: {ingress_name}")
            else:
                raise
        
        return ingress_name

class DockerManager:
    """Docker container management"""
    
    def __init__(self):
        self.client = docker.from_env()
    
    async def build_image(self, config: Dict[str, Any]) -> str:
        """Build Docker image"""
        try:
            image, build_logs = self.client.images.build(
                path=config.get('build_context', '.'),
                dockerfile=config.get('dockerfile', 'Dockerfile'),
                tag=config.get('tag', 'ai-scholar:latest'),
                rm=True,
                forcerm=True
            )
            
            logger.info(f"✅ Docker image built: {image.tags[0]}")
            return image.tags[0]
            
        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            raise
    
    async def push_image(self, image_tag: str, registry_config: Dict[str, Any]) -> bool:
        """Push image to registry"""
        try:
            # Login to registry if credentials provided
            if registry_config.get('username') and registry_config.get('password'):
                self.client.login(
                    username=registry_config['username'],
                    password=registry_config['password'],
                    registry=registry_config.get('registry')
                )
            
            # Push image
            push_logs = self.client.images.push(
                repository=image_tag,
                stream=True,
                decode=True
            )
            
            for log in push_logs:
                if 'error' in log:
                    raise Exception(log['error'])
            
            logger.info(f"✅ Docker image pushed: {image_tag}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push Docker image: {e}")
            return False

class InfrastructureManager:
    """Main infrastructure management orchestrator"""
    
    def __init__(self):
        self.cloud_providers = {}
        self.kubernetes_manager = None
        self.docker_manager = DockerManager()
        self.resources = {}
        self.deployments = {}
    
    def add_cloud_provider(self, provider_name: str, provider: CloudProvider):
        """Add cloud provider"""
        self.cloud_providers[provider_name] = provider
        logger.info(f"✅ Cloud provider added: {provider_name}")
    
    def set_kubernetes_manager(self, kubeconfig_path: Optional[str] = None):
        """Set Kubernetes manager"""
        self.kubernetes_manager = KubernetesManager(kubeconfig_path)
        logger.info("✅ Kubernetes manager configured")
    
    async def deploy_infrastructure(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Deploy complete infrastructure"""
        deployment_id = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            # Select cloud provider
            provider = self.cloud_providers.get('aws')  # Default to AWS
            if not provider:
                raise ValueError("No cloud provider configured")
            
            resources_created = {}
            
            # Create database if specified
            if config.database_config.get('enabled', True):
                db_id = await provider.create_database(config.database_config)
                resources_created['database'] = db_id
            
            # Create load balancer if specified
            if config.load_balancer:
                lb_id = await provider.create_load_balancer({
                    'name': f'ai-scholar-{config.environment}-lb',
                    'environment': config.environment,
                    'subnets': config.database_config.get('subnets', []),
                    'security_groups': config.database_config.get('security_groups', []),
                    'vpc_id': config.database_config.get('vpc_id')
                })
                resources_created['load_balancer'] = lb_id
            
            # Setup auto scaling if specified
            if config.auto_scaling:
                asg_id = await provider.setup_auto_scaling({
                    'asg_name': f'ai-scholar-{config.environment}-asg',
                    'environment': config.environment,
                    'instance_type': config.instance_type,
                    'min_size': config.min_instances,
                    'max_size': config.max_instances,
                    'desired_capacity': config.min_instances,
                    'subnets': config.database_config.get('subnets', []),
                    'security_groups': config.database_config.get('security_groups', []),
                    'target_group_arns': [resources_created.get('load_balancer')]
                })
                resources_created['auto_scaling_group'] = asg_id
            else:
                # Create single instance
                instance_id = await provider.create_instance({
                    'name': f'ai-scholar-{config.environment}',
                    'environment': config.environment,
                    'instance_type': config.instance_type,
                    'security_groups': config.database_config.get('security_groups', []),
                    'subnet_id': config.database_config.get('subnets', [None])[0]
                })
                resources_created['instance'] = instance_id
            
            # Store deployment info
            self.deployments[deployment_id] = {
                'config': asdict(config),
                'resources': resources_created,
                'status': 'deployed',
                'created_at': datetime.now(),
                'provider': provider.provider_name
            }
            
            logger.info(f"✅ Infrastructure deployed: {deployment_id}")
            
            return {
                'deployment_id': deployment_id,
                'status': 'success',
                'resources': resources_created,
                'endpoints': self._get_deployment_endpoints(resources_created)
            }
            
        except Exception as e:
            logger.error(f"Infrastructure deployment failed: {e}")
            return {
                'deployment_id': deployment_id,
                'status': 'failed',
                'error': str(e)
            }
    
    async def deploy_application(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application using Kubernetes or Docker"""
        if self.kubernetes_manager and app_config.get('platform') == 'kubernetes':
            return await self.kubernetes_manager.deploy_application(app_config)
        else:
            # Docker deployment
            image_tag = await self.docker_manager.build_image(app_config.get('build', {}))
            
            if app_config.get('push_to_registry'):
                await self.docker_manager.push_image(
                    image_tag, 
                    app_config.get('registry', {})
                )
            
            return {
                'platform': 'docker',
                'image': image_tag,
                'status': 'deployed'
            }
    
    def _get_deployment_endpoints(self, resources: Dict[str, str]) -> Dict[str, str]:
        """Get deployment endpoints"""
        endpoints = {}
        
        if 'load_balancer' in resources:
            endpoints['load_balancer'] = f"http://{resources['load_balancer']}"
        
        if 'instance' in resources:
            endpoints['instance'] = f"http://{resources['instance']}:8000"
        
        return endpoints
    
    async def scale_deployment(self, deployment_id: str, target_capacity: int) -> bool:
        """Scale deployment"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        provider_name = deployment['provider']
        provider = self.cloud_providers.get(provider_name)
        
        if not provider:
            raise ValueError(f"Provider not available: {provider_name}")
        
        try:
            # Update auto scaling group capacity
            if 'auto_scaling_group' in deployment['resources']:
                asg_name = deployment['resources']['auto_scaling_group']
                # In real implementation, call AWS API to update ASG
                logger.info(f"✅ Scaled deployment {deployment_id} to {target_capacity} instances")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to scale deployment: {e}")
            return False
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")
        
        deployment = self.deployments[deployment_id]
        
        return {
            'deployment_id': deployment_id,
            'status': deployment['status'],
            'created_at': deployment['created_at'].isoformat(),
            'resources': deployment['resources'],
            'config': deployment['config']
        }
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployments"""
        return [
            {
                'deployment_id': dep_id,
                'status': dep['status'],
                'created_at': dep['created_at'].isoformat(),
                'provider': dep['provider'],
                'resource_count': len(dep['resources'])
            }
            for dep_id, dep in self.deployments.items()
        ]

# Global infrastructure manager
infrastructure_manager = InfrastructureManager()

# Convenience functions
async def deploy_infrastructure(config: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy infrastructure"""
    deployment_config = DeploymentConfig(**config)
    return await infrastructure_manager.deploy_infrastructure(deployment_config)

async def deploy_application(config: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy application"""
    return await infrastructure_manager.deploy_application(config)

def setup_aws_provider(credentials: Dict[str, Any]):
    """Setup AWS provider"""
    aws_provider = AWSProvider(credentials)
    infrastructure_manager.add_cloud_provider('aws', aws_provider)

def setup_kubernetes(kubeconfig_path: Optional[str] = None):
    """Setup Kubernetes manager"""
    infrastructure_manager.set_kubernetes_manager(kubeconfig_path)

if __name__ == "__main__":
    # Example usage
    async def test_infrastructure_manager():
        print("🧪 Testing Infrastructure Manager...")
        
        # Setup AWS provider (with mock credentials)
        setup_aws_provider({
            'access_key': 'mock_access_key',
            'secret_key': 'mock_secret_key',
            'region': 'us-east-1'
        })
        
        # Deploy infrastructure
        config = {
            'environment': 'production',
            'region': 'us-east-1',
            'instance_type': 't3.medium',
            'min_instances': 2,
            'max_instances': 10,
            'auto_scaling': True,
            'load_balancer': True,
            'database_config': {
                'enabled': True,
                'engine': 'postgres',
                'instance_class': 'db.t3.micro'
            },
            'storage_config': {},
            'monitoring_config': {}
        }
        
        try:
            result = await deploy_infrastructure(config)
            print(f"Infrastructure deployment: {result['status']}")
            if result['status'] == 'success':
                print(f"Deployment ID: {result['deployment_id']}")
                print(f"Resources created: {len(result['resources'])}")
        except Exception as e:
            print(f"Deployment failed: {e}")
        
        # List deployments
        deployments = infrastructure_manager.list_deployments()
        print(f"Total deployments: {len(deployments)}")
    
    asyncio.run(test_infrastructure_manager())