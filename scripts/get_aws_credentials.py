"""
Script to help get AWS credentials for SageMaker deployment
"""
import boto3
import json
import os

def get_aws_credentials():
    """Try to get AWS credentials from various sources"""
    
    print("AWS Credentials Helper")
    print("=" * 30)
    
    # Try to get credentials from AWS CLI
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials:
            print("Found AWS credentials from AWS CLI:")
            print(f"Access Key ID: {credentials.access_key}")
            print(f"Secret Access Key: {credentials.secret_key[:10]}...")
            print(f"Region: {session.region_name}")
            
            # Update .env file
            update_env_file(credentials.access_key, credentials.secret_key, session.region_name)
            return True
        else:
            print("No credentials found in AWS CLI")
    except Exception as e:
        print(f"Error getting credentials from AWS CLI: {e}")
    
    # Try to get from environment variables
    try:
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        if access_key and secret_key:
            print("Found AWS credentials from environment variables:")
            print(f"Access Key ID: {access_key}")
            print(f"Secret Access Key: {secret_key[:10]}...")
            print(f"Region: {region}")
            
            update_env_file(access_key, secret_key, region)
            return True
        else:
            print("No credentials found in environment variables")
    except Exception as e:
        print(f"Error getting credentials from environment: {e}")
    
    print("\nNo AWS credentials found automatically.")
    print("Please get your credentials from:")
    print("1. AWS Console → IAM → Users → Your User → Security credentials")
    print("2. Or use AWS CLI: aws configure")
    print("3. Then edit .env file with your actual credentials")
    
    return False

def update_env_file(access_key, secret_key, region):
    """Update .env file with actual credentials"""
    try:
        # Read current .env file
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the lines
        new_lines = []
        for line in lines:
            if line.startswith('AWS_ACCESS_KEY_ID='):
                new_lines.append(f'AWS_ACCESS_KEY_ID={access_key}\n')
            elif line.startswith('AWS_SECRET_ACCESS_KEY='):
                new_lines.append(f'AWS_SECRET_ACCESS_KEY={secret_key}\n')
            elif line.startswith('AWS_DEFAULT_REGION='):
                new_lines.append(f'AWS_DEFAULT_REGION={region}\n')
            else:
                new_lines.append(line)
        
        # Write updated .env file
        with open('.env', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"\n✓ Updated .env file with your AWS credentials")
        print("You can now run: python scripts/deploy_sagemaker_env.py")
        
    except Exception as e:
        print(f"Error updating .env file: {e}")

if __name__ == "__main__":
    get_aws_credentials()
