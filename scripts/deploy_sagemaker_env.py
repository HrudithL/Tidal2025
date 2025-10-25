"""
SageMaker Deployment Script for SonicMuse
Uses environment variables for AWS credentials
"""
import os
import json
import time
import boto3
from pathlib import Path
from sagemaker.pytorch import PyTorchModel
from sagemaker import get_execution_role
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SonicMuseSageMakerDeployer:
    def __init__(self):
        # Get configuration from environment variables
        self.bucket_name = os.getenv('SAGEMAKER_BUCKET_NAME', 'sonicmuse-models-bucket')
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
        self.instance_type = os.getenv('SAGEMAKER_INSTANCE_TYPE', 'ml.g4dn.xlarge')
        
        # Initialize AWS clients with environment credentials
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
        )
        
        self.sagemaker_client = boto3.client(
            'sagemaker',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
        )
        
        # Verify credentials
        self._verify_credentials()
        
    def _verify_credentials(self):
        """Verify AWS credentials are working"""
        try:
            # Test S3 access
            self.s3_client.list_buckets()
            logger.info("AWS credentials verified successfully")
        except Exception as e:
            logger.error(f"AWS credentials verification failed: {e}")
            logger.error("Please check your .env file and ensure credentials are correct")
            raise
    
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
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model package not found: {model_path}")
            
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
            # Create IAM role for SageMaker
            role = self._get_or_create_role()
            
            # Create model
            model = PyTorchModel(
                model_data=model_s3_uri,
                role=role,
                entry_point='inference.py',
                framework_version='2.0.0',
                py_version='py310',
                env={
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code',
                    'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
                    'SAGEMAKER_REGION': self.region,
                    'TORCH_HOME': '/opt/ml/model/models',
                    'HF_HOME': '/opt/ml/model/models',
                    'MODEL_SIZE': os.getenv('MODEL_SIZE', 'small'),
                    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', '')
                }
            )
            
            logger.info("SageMaker model created successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create model: {e}")
            raise
    
    def _get_or_create_role(self):
        """Get or create IAM role for SageMaker"""
        try:
            # Force use of our custom role
            account_id = self._get_account_id()
            role_arn = f"arn:aws:iam::{account_id}:role/SonicMuseSageMakerRole"
            logger.info(f"Using SonicMuse SageMaker role: {role_arn}")
            return role_arn
        except:
            # Create new role if it doesn't exist
            logger.info("Creating new SageMaker execution role...")
            
            iam_client = boto3.client(
                'iam',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
            )
            
            # Create trust policy
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "sagemaker.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create role
            role_name = "SonicMuseSageMakerRole"
            try:
                iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description="SageMaker execution role for SonicMuse"
                )
                
                # Attach SageMaker execution policy
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
                )
                
                # Wait for role to be available
                time.sleep(10)
                
                role_arn = f"arn:aws:iam::{self._get_account_id()}:role/{role_name}"
                logger.info(f"Created new SageMaker role: {role_arn}")
                return role_arn
                
            except iam_client.exceptions.EntityAlreadyExistsException:
                # Role already exists, get its ARN
                account_id = self._get_account_id()
                role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
                logger.info(f"Using existing role: {role_arn}")
                return role_arn
    
    def _get_account_id(self):
        """Get AWS account ID"""
        sts_client = boto3.client(
            'sts',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        return sts_client.get_caller_identity()['Account']
    
    def deploy_endpoint(self, model):
        """Deploy model as SageMaker endpoint"""
        try:
            logger.info(f"Deploying endpoint: {self.endpoint_name}")
            
            predictor = model.deploy(
                initial_instance_count=1,
                instance_type=self.instance_type,
                endpoint_name=self.endpoint_name,
                wait=True,
                update_endpoint=False
            )
            
            logger.info(f"Endpoint deployed successfully: {self.endpoint_name}")
            return predictor
            
        except Exception as e:
            logger.error(f"Failed to deploy endpoint: {e}")
            raise
    
    def test_endpoint(self):
        """Test the deployed endpoint"""
        try:
            # Create test payload
            test_payload = {
                "operation": "analyze",
                "audio_data": "dGVzdA=="  # Base64 encoded "test"
            }
            
            # Invoke endpoint using SageMaker Runtime client
            runtime_client = boto3.client(
                'sagemaker-runtime',
                region_name=self.region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
            )
            
            response = runtime_client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(test_payload)
            )
            
            result = json.loads(response['Body'].read())
            logger.info("Endpoint test successful")
            return result
            
        except Exception as e:
            logger.error(f"Endpoint test failed: {e}")
            raise
    
    def get_endpoint_url(self):
        """Get endpoint URL"""
        try:
            response = self.sagemaker_client.describe_endpoint(EndpointName=self.endpoint_name)
            endpoint_url = f"https://{self.endpoint_name}.{self.region}.sagemaker.amazonaws.com"
            return endpoint_url
        except Exception as e:
            logger.error(f"Failed to get endpoint URL: {e}")
            return None

def main():
    """Main deployment function"""
    
    try:
        # Check if .env file exists
        if not os.path.exists('.env'):
            logger.error("❌ .env file not found!")
            logger.error("Please copy .env.example to .env and fill in your AWS credentials")
            logger.error("Example:")
            logger.error("  cp .env.example .env")
            logger.error("  # Edit .env with your actual credentials")
            return
        
        # Check required environment variables
        required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            logger.error("Please check your .env file")
            return
        
        # Initialize deployer
        deployer = SonicMuseSageMakerDeployer()
        
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
        predictor = deployer.deploy_endpoint(model)
        
        # Step 5: Test endpoint
        logger.info("Step 5: Testing endpoint...")
        deployer.test_endpoint()
        
        # Step 6: Get endpoint URL
        endpoint_url = deployer.get_endpoint_url()
        
        logger.info("🎉 Deployment completed successfully!")
        logger.info(f"Endpoint URL: {endpoint_url}")
        logger.info(f"Endpoint Name: {deployer.endpoint_name}")
        
        # Save configuration
        config = {
            "endpoint_name": deployer.endpoint_name,
            "endpoint_url": endpoint_url,
            "bucket_name": deployer.bucket_name,
            "region": deployer.region,
            "model_s3_uri": model_s3_uri,
            "instance_type": deployer.instance_type
        }
        
        with open("sagemaker_config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuration saved to sagemaker_config.json")
        
        # Print next steps
        logger.info("\n📋 Next Steps:")
        logger.info("1. Update your frontend API configuration:")
        logger.info(f"   VITE_API_BASE={endpoint_url}")
        logger.info("2. Deploy frontend to Vercel")
        logger.info("3. Test the complete application")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise

if __name__ == "__main__":
    main()
