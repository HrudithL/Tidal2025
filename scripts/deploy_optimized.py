"""
Deploy optimized SageMaker model
"""
import os
import boto3
import json
import time
from dotenv import load_dotenv

def deploy_optimized_model():
    """Deploy the optimized SageMaker model"""
    
    load_dotenv()
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    bucket_name = os.getenv('SAGEMAKER_BUCKET_NAME', 'sonicmuse-models-0ubdu3d6')
    endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
    instance_type = os.getenv('SAGEMAKER_INSTANCE_TYPE', 'ml.g4dn.xlarge')
    
    print("Deploying Optimized SageMaker Model")
    print("=" * 40)
    
    # Initialize AWS clients
    s3_client = boto3.client(
        's3',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    sagemaker_client = boto3.client(
        'sagemaker',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    # Step 1: Upload optimized model package
    model_file = "sonicmuse-model-optimized.tar.gz"
    if not os.path.exists(model_file):
        print(f"ERROR: {model_file} not found. Run create_optimized_package.py first.")
        return False
    
    print("Step 1: Uploading optimized model package...")
    s3_key = f"models/{model_file}"
    s3_model_uri = f"s3://{bucket_name}/{s3_key}"
    
    try:
        s3_client.upload_file(model_file, bucket_name, s3_key)
        print(f"[OK] Model uploaded to {s3_model_uri}")
    except Exception as e:
        print(f"ERROR: Failed to upload model: {e}")
        return False
    
    # Step 2: Create SageMaker model
    print("Step 2: Creating SageMaker model...")
    
    # Get account ID for role ARN
    sts_client = boto3.client(
        'sts',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    account_id = sts_client.get_caller_identity()['Account']
    role_arn = f"arn:aws:iam::{account_id}:role/SonicMuseSageMakerRole"
    
    model_name = f"sonicmuse-optimized-{int(time.time())}"
    
    try:
        sagemaker_client.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': '763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-inference:2.0.0-gpu-py310',
                'ModelDataUrl': s3_model_uri,
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': '/opt/ml/code',
                    'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
                    'SAGEMAKER_REGION': region,
                    'MODEL_SIZE': os.getenv('MODEL_SIZE', 'small')
                }
            },
            ExecutionRoleArn=role_arn
        )
        print(f"[OK] SageMaker model created: {model_name}")
    except Exception as e:
        print(f"ERROR: Failed to create model: {e}")
        return False
    
    # Step 3: Create endpoint configuration
    print("Step 3: Creating endpoint configuration...")
    
    config_name = f"sonicmuse-optimized-config-{int(time.time())}"
    
    try:
        sagemaker_client.create_endpoint_config(
            EndpointConfigName=config_name,
            ProductionVariants=[
                {
                    'VariantName': 'primary',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': instance_type,
                    'InitialVariantWeight': 1.0
                }
            ]
        )
        print(f"[OK] Endpoint configuration created: {config_name}")
    except Exception as e:
        print(f"ERROR: Failed to create endpoint config: {e}")
        return False
    
    # Step 4: Update endpoint
    print("Step 4: Updating endpoint...")
    
    try:
        sagemaker_client.update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=config_name
        )
        print(f"[OK] Endpoint update initiated: {endpoint_name}")
        
        # Wait for endpoint to be ready
        print("Waiting for endpoint to be ready...")
        waiter = sagemaker_client.get_waiter('endpoint_in_service')
        waiter.wait(EndpointName=endpoint_name)
        
        print("[OK] Endpoint is ready!")
        
    except Exception as e:
        print(f"ERROR: Failed to update endpoint: {e}")
        return False
    
    # Step 5: Test endpoint
    print("Step 5: Testing optimized endpoint...")
    
    runtime_client = boto3.client(
        'sagemaker-runtime',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    try:
        # Test health endpoint
        test_payload = {"operation": "health"}
        
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read())
        print(f"[OK] Health check successful: {result}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_optimized_model()
    if success:
        print("\n🎉 Optimized model deployment successful!")
        print("\nNext steps:")
        print("1. Test the endpoint with audio data")
        print("2. Update frontend to use the endpoint")
        print("3. Deploy frontend to Vercel")
    else:
        print("\n[ERROR] Deployment failed. Check the logs.")
