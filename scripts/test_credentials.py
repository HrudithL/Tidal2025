"""
Test AWS Credentials Before Deployment
"""
import os
import boto3
from dotenv import load_dotenv

def test_credentials():
    """Test AWS credentials before deployment"""
    
    print("Testing AWS Credentials")
    print("=" * 25)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from .env
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    print(f"Access Key ID: {access_key[:10]}..." if access_key else "Not set")
    print(f"Secret Key: {'*' * 10}..." if secret_key else "Not set")
    print(f"Region: {region}")
    
    # Check if credentials are still placeholders
    if access_key == 'your_access_key_here' or secret_key == 'your_secret_key_here':
        print("\nERROR: You still have placeholder values in .env file!")
        print("Please edit .env with your actual AWS credentials.")
        return False
    
    # Test credentials
    try:
        print("\nTesting AWS credentials...")
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
        )
        
        # Test S3 access
        response = s3_client.list_buckets()
        print("[OK] AWS credentials work!")
        print(f"[OK] Found {len(response['Buckets'])} existing buckets")
        
        # Test SageMaker access
        sagemaker_client = boto3.client(
            'sagemaker',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
        )
        
        # Test SageMaker access
        sagemaker_client.list_models()
        print("[OK] SageMaker access confirmed!")
        
        print("\nReady to deploy! Run:")
        print("python scripts/deploy_sagemaker_env.py")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nPlease check your AWS credentials and try again.")
        return False

if __name__ == "__main__":
    test_credentials()
