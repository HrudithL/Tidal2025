"""
Quick Setup Script for SageMaker Deployment
"""
import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up environment files for SageMaker deployment"""
    
    print("SonicMuse SageMaker Setup")
    print("=" * 40)
    
    # Check if .env exists
    if os.path.exists('.env'):
        print("[OK] .env file already exists")
    else:
        # Copy .env.example to .env
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("[OK] Created .env file from .env.example")
            print("WARNING: Please edit .env with your actual AWS credentials")
        else:
            print("ERROR: .env.example not found")
            return False
    
    # Check if model package exists
    if os.path.exists('sonicmuse-model.tar.gz'):
        print("[OK] Model package exists")
    else:
        print("ERROR: Model package not found")
        print("Run: python scripts/create_sagemaker_package.py")
        return False
    
    # Check required packages
    try:
        import boto3
        import sagemaker
        from dotenv import load_dotenv
        print("[OK] Required packages installed")
    except ImportError as e:
        print("ERROR: Missing package:", e)
        print("Install with: pip install boto3 sagemaker python-dotenv")
        return False
    
    print("\nSetup Complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your AWS credentials")
    print("2. Run: python scripts/deploy_sagemaker_env.py")
    
    return True

if __name__ == "__main__":
    setup_environment()
