"""
Manual AWS Credentials Setup for SageMaker Deployment
"""
import os

def setup_credentials():
    """Help user set up AWS credentials manually"""
    
    print("AWS Credentials Setup for SageMaker")
    print("=" * 40)
    
    print("\nSince you have an AWS event account, you need to:")
    print("1. Go to AWS Console (console.aws.amazon.com)")
    print("2. Sign in with your event account")
    print("3. Go to IAM -> Users -> Your User")
    print("4. Click 'Security credentials' tab")
    print("5. Click 'Create access key'")
    print("6. Copy the Access Key ID and Secret Access Key")
    
    print("\nThen edit your .env file:")
    print("notepad .env")
    
    print("\nReplace these lines:")
    print("AWS_ACCESS_KEY_ID=your_access_key_here")
    print("AWS_SECRET_ACCESS_KEY=your_secret_key_here")
    
    print("\nWith your actual credentials:")
    print("AWS_ACCESS_KEY_ID=AKIA...")
    print("AWS_SECRET_ACCESS_KEY=...")
    
    print("\nAlso change the bucket name to something unique:")
    print("SAGEMAKER_BUCKET_NAME=your-unique-bucket-name-12345")
    
    print("\nAfter editing .env, run:")
    print("python scripts/deploy_sagemaker_env.py")

if __name__ == "__main__":
    setup_credentials()
