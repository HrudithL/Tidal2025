"""
Simple script to help edit .env file with AWS credentials
"""
import os
import shutil

def edit_env_file():
    """Help user edit .env file with actual AWS credentials"""
    
    print("SonicMuse AWS Credentials Setup")
    print("=" * 40)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("Created .env file from .env.example")
        else:
            print("ERROR: .env.example not found")
            return
    
    print("\nCurrent .env file contents:")
    print("-" * 30)
    with open('.env', 'r', encoding='utf-8') as f:
        print(f.read())
    
    print("\nTo edit with your actual AWS credentials:")
    print("1. Open .env file in a text editor")
    print("2. Replace the placeholder values:")
    print("   - AWS_ACCESS_KEY_ID=your_actual_access_key")
    print("   - AWS_SECRET_ACCESS_KEY=your_actual_secret_key")
    print("   - SAGEMAKER_BUCKET_NAME=your_unique_bucket_name")
    print("3. Save the file")
    print("4. Run: python scripts/deploy_sagemaker_env.py")
    
    print("\nExample .env file:")
    print("-" * 20)
    print("AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF")
    print("AWS_SECRET_ACCESS_KEY=abcdef1234567890abcdef1234567890abcdef12")
    print("AWS_DEFAULT_REGION=us-east-1")
    print("SAGEMAKER_BUCKET_NAME=my-sonicmuse-bucket-12345")
    print("SAGEMAKER_ENDPOINT_NAME=sonicmuse-endpoint")
    print("SAGEMAKER_INSTANCE_TYPE=ml.g4dn.xlarge")
    print("MODEL_SIZE=small")
    print("GEMINI_API_KEY=your_gemini_key_here")

if __name__ == "__main__":
    edit_env_file()
