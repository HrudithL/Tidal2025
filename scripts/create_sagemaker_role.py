"""
Script to create SageMaker execution role with proper permissions
"""
import boto3
import json
import os
from dotenv import load_dotenv

def create_sagemaker_role():
    """Create SageMaker execution role with S3 permissions"""
    
    load_dotenv()
    
    # Initialize IAM client
    iam_client = boto3.client(
        'iam',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    role_name = "SonicMuseSageMakerRole"
    
    try:
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
        print(f"Creating SageMaker role: {role_name}")
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="SageMaker execution role for SonicMuse"
        )
        
        # Attach SageMaker execution policy
        print("Attaching SageMaker execution policy...")
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
        )
        
        # Create custom S3 policy for our bucket
        bucket_name = os.getenv('SAGEMAKER_BUCKET_NAME', 'sonicmuse-models-0ubdu3d6')
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket"
                    ],
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                }
            ]
        }
        
        # Create and attach S3 policy
        print("Creating custom S3 policy...")
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="SonicMuseS3Access",
            PolicyDocument=json.dumps(s3_policy)
        )
        
        # Get account ID
        sts_client = boto3.client(
            'sts',
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-west-2'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
        )
        account_id = sts_client.get_caller_identity()['Account']
        
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        print(f"Successfully created role: {role_arn}")
        
        return role_arn
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Role {role_name} already exists")
        account_id = sts_client.get_caller_identity()['Account']
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        return role_arn
        
    except Exception as e:
        print(f"Error creating role: {e}")
        return None

if __name__ == "__main__":
    role_arn = create_sagemaker_role()
    if role_arn:
        print(f"\nRole created successfully: {role_arn}")
        print("Update your deployment script to use this role.")
    else:
        print("Failed to create role. You may need to contact AWS support.")
