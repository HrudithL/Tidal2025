"""
SageMaker Deployment Script for SonicMuse
"""
import boto3
import json
import time
from pathlib import Path
from sagemaker.pytorch import PyTorchModel
from sagemaker import get_execution_role
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SonicMuseSageMakerDeployer:
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.sagemaker_client = boto3.client('sagemaker', region_name=region)
        
    def create_s3_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
        except:
            if self.region == "us-east-1":
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            logger.info(f"Created bucket {self.bucket_name}")
    
    def upload_model_package(self, model_path: str = "sonicmuse-model.tar.gz"):
        """Upload model package to S3"""
        try:
            s3_key = f"models/{Path(model_path).name}"
            self.s3_client.upload_file(model_path, self.bucket_name, s3_key)
            
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Model uploaded to {s3_uri}")
            return s3_uri
            
        except Exception as e:
            logger.error(f"Failed to upload model: {e}")
            raise
    
    def create_model(self, model_s3_uri: str):
        """Create SageMaker model"""
        try:
            role = get_execution_role()
            
            # Create model
            model = PyTorchModel(
                model_data=model_s3_uri,
                role=role,
                entry_point='inference.py',
                framework_version='2.0.0',
                py_version='py310',
                instance_type='ml.g4dn.xlarge',
                source_dir='.',  # Current directory
                dependencies=['requirements.txt'],
                env={
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code',
                    'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
                    'SAGEMAKER_REGION': self.region
                }
            )
            
            logger.info("SageMaker model created successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create model: {e}")
            raise
    
    def deploy_endpoint(self, model, endpoint_name: str = "sonicmuse-endpoint"):
        """Deploy model as SageMaker endpoint"""
        try:
            logger.info(f"Deploying endpoint: {endpoint_name}")
            
            predictor = model.deploy(
                initial_instance_count=1,
                instance_type='ml.g4dn.xlarge',
                endpoint_name=endpoint_name,
                wait=True,
                update_endpoint=False
            )
            
            logger.info(f"Endpoint deployed successfully: {endpoint_name}")
            return predictor
            
        except Exception as e:
            logger.error(f"Failed to deploy endpoint: {e}")
            raise
    
    def test_endpoint(self, endpoint_name: str):
        """Test the deployed endpoint"""
        try:
            # Create test payload
            test_payload = {
                "operation": "analyze",
                "audio_data": "dGVzdA=="  # Base64 encoded "test"
            }
            
            # Invoke endpoint
            response = self.sagemaker_client.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/json',
                Body=json.dumps(test_payload)
            )
            
            result = json.loads(response['Body'].read())
            logger.info("Endpoint test successful")
            return result
            
        except Exception as e:
            logger.error(f"Endpoint test failed: {e}")
            raise
    
    def get_endpoint_url(self, endpoint_name: str):
        """Get endpoint URL"""
        try:
            response = self.sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
            endpoint_url = f"https://{endpoint_name}.{self.region}.sagemaker.amazonaws.com"
            return endpoint_url
        except Exception as e:
            logger.error(f"Failed to get endpoint URL: {e}")
            return None

def main():
    """Main deployment function"""
    
    # Configuration
    BUCKET_NAME = "sonicmuse-models-bucket"  # Change this to your bucket name
    REGION = "us-east-1"
    ENDPOINT_NAME = "sonicmuse-endpoint"
    
    try:
        # Initialize deployer
        deployer = SonicMuseSageMakerDeployer(BUCKET_NAME, REGION)
        
        # Step 1: Create S3 bucket
        logger.info("Step 1: Creating S3 bucket...")
        deployer.create_s3_bucket()
        
        # Step 2: Upload model package
        logger.info("Step 2: Uploading model package...")
        model_s3_uri = deployer.upload_model_package()
        
        # Step 3: Create SageMaker model
        logger.info("Step 3: Creating SageMaker model...")
        model = deployer.create_model(model_s3_uri)
        
        # Step 4: Deploy endpoint
        logger.info("Step 4: Deploying endpoint...")
        predictor = deployer.deploy_endpoint(model, ENDPOINT_NAME)
        
        # Step 5: Test endpoint
        logger.info("Step 5: Testing endpoint...")
        deployer.test_endpoint(ENDPOINT_NAME)
        
        # Step 6: Get endpoint URL
        endpoint_url = deployer.get_endpoint_url(ENDPOINT_NAME)
        
        logger.info("🎉 Deployment completed successfully!")
        logger.info(f"Endpoint URL: {endpoint_url}")
        logger.info(f"Endpoint Name: {ENDPOINT_NAME}")
        
        # Save configuration
        config = {
            "endpoint_name": ENDPOINT_NAME,
            "endpoint_url": endpoint_url,
            "bucket_name": BUCKET_NAME,
            "region": REGION,
            "model_s3_uri": model_s3_uri
        }
        
        with open("sagemaker_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuration saved to sagemaker_config.json")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise

if __name__ == "__main__":
    main()
