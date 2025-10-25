"""
Interactive AWS Credentials Setup
"""
import os

def setup_credentials_interactive():
    """Interactive setup for AWS credentials"""
    
    print("AWS Credentials Setup")
    print("=" * 25)
    
    print("\nCurrent .env file has placeholder values.")
    print("You need to replace them with your actual AWS credentials.")
    
    print("\nTo get your credentials:")
    print("1. Go to AWS Console (console.aws.amazon.com)")
    print("2. Sign in with your event account")
    print("3. Go to IAM -> Users -> Your User")
    print("4. Click 'Security credentials' tab")
    print("5. Click 'Create access key'")
    print("6. Copy the Access Key ID and Secret Access Key")
    
    print("\nThen run this command to edit your .env file:")
    print("notepad .env")
    
    print("\nReplace these lines:")
    print("AWS_ACCESS_KEY_ID=your_access_key_here")
    print("AWS_SECRET_ACCESS_KEY=your_secret_key_here")
    
    print("\nWith your actual credentials (example):")
    print("AWS_ACCESS_KEY_ID=AKIA1234567890ABCDEF")
    print("AWS_SECRET_ACCESS_KEY=abcdef1234567890abcdef1234567890abcdef12")
    
    print("\nAfter editing, test your credentials:")
    print("python scripts/test_credentials.py")
    
    print("\nIf credentials work, deploy:")
    print("python scripts/deploy_sagemaker_env.py")

if __name__ == "__main__":
    setup_credentials_interactive()
