"""
Deploy a single SageMaker approach
"""
import os
import json
import boto3
import time
import sys
from dotenv import load_dotenv

def deploy_single_approach(approach_name):
    """Deploy a single approach"""
    
    load_dotenv()
    
    approaches = {
        "cpu_minimal": {
            "package": "sonicmuse-cpu_minimal.tar.gz",
            "instance": "ml.m5.large",
            "description": "CPU-only minimal (no AI models)"
        },
        "cpu_large": {
            "package": "sonicmuse-cpu_large.tar.gz", 
            "instance": "ml.m5.2xlarge",
            "description": "CPU-only for large instances"
        },
        "lazy_loading": {
            "package": "sonicmuse-lazy_loading.tar.gz",
            "instance": "ml.m5.xlarge", 
            "description": "Lazy loading (models load on demand)"
        },
        "small_models": {
            "package": "sonicmuse-small_models.tar.gz",
            "instance": "ml.m5.xlarge",
            "description": "Smallest AI models (tiny Whisper)"
        }
    }
    
    if approach_name not in approaches:
        print(f"ERROR: Unknown approach '{approach_name}'")
        print(f"Available approaches: {', '.join(approaches.keys())}")
        return False
    
    config = approaches[approach_name]
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    bucket_name = os.getenv('SAGEMAKER_BUCKET_NAME', 'sonicmuse-models-0ubdu3d6')
    
    print(f"Deploying {approach_name}")
    print(f"Description: {config['description']}")
    print(f"Instance: {config['instance']}")
    print(f"Package: {config['package']}")
    print("=" * 50)
    
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
    
    try:
        # Step 1: Upload to S3
        print("Step 1: Uploading model package to S3...")
        package_file = config["package"]
        
        if not os.path.exists(package_file):
            print(f"ERROR: Package {package_file} not found")
            print("Run: python scripts/test_all_approaches.py first")
            return False
        
        s3_key = f"models/{package_file}"
        s3_model_uri = f"s3://{bucket_name}/{s3_key}"
        
        s3_client.upload_file(package_file, bucket_name, s3_key)
        print(f"[OK] Uploaded to {s3_model_uri}")
        
        # Step 2: Create SageMaker model
        # Fix naming: SageMaker doesn't allow underscores, only hyphens
        safe_approach_name = approach_name.replace('_', '-')
        print("Step 2: Creating SageMaker model...")
        model_name = f"sonicmuse-{safe_approach_name}-{int(time.time())}"
        
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
                    'MODEL_SIZE': 'small'
                }
            },
            ExecutionRoleArn=role_arn
        )
        print(f"[OK] Model created: {model_name}")
        
        # Step 3: Create endpoint configuration
        print("Step 3: Creating endpoint configuration...")
        config_name = f"sonicmuse-{safe_approach_name}-config-{int(time.time())}"
        
        sagemaker_client.create_endpoint_config(
            EndpointConfigName=config_name,
            ProductionVariants=[
                {
                    'VariantName': 'primary',
                    'ModelName': model_name,
                    'InitialInstanceCount': 1,
                    'InstanceType': config["instance"],
                    'InitialVariantWeight': 1.0
                }
            ]
        )
        print(f"[OK] Endpoint config created: {config_name}")
        
        # Step 4: Create endpoint
        print("Step 4: Creating endpoint...")
        endpoint_name = f"sonicmuse-{safe_approach_name}-{int(time.time())}"
        
        sagemaker_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=config_name
        )
        print(f"[OK] Endpoint creation initiated: {endpoint_name}")
        
        # Step 5: Wait for endpoint to be ready
        print("Step 5: Waiting for endpoint to be ready...")
        print("This may take 5-10 minutes...")
        
        waiter = sagemaker_client.get_waiter('endpoint_in_service')
        waiter.wait(EndpointName=endpoint_name)
        print(f"[OK] Endpoint is ready: {endpoint_name}")
        
        # Step 6: Test endpoint
        print("Step 6: Testing endpoint...")
        
        runtime_client = boto3.client(
            'sagemaker-runtime',
            region_name=region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
        )
        
        try:
            test_payload = {"operation": "health"}
            
            response = runtime_client.invoke_endpoint(
                EndpointName=endpoint_name,
                ContentType='application/json',
                Body=json.dumps(test_payload)
            )
            
            result = json.loads(response['Body'].read())
            print(f"[OK] Health check successful: {result}")
            
            # Save configuration
            config_data = {
                "approach": approach_name,
                "endpoint_name": endpoint_name,
                "model_name": model_name,
                "config_name": config_name,
                "instance_type": config["instance"],
                "region": region,
                "endpoint_url": f"https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint_name}/invocations",
                "status": "success"
            }
            
            with open(f"sagemaker_{approach_name}_config.json", "w") as f:
                json.dump(config_data, f, indent=2)
            
            print(f"[OK] Configuration saved to sagemaker_{approach_name}_config.json")
            print(f"\n[SUCCESS] {approach_name} deployed and working!")
            print(f"Endpoint URL: {config_data['endpoint_url']}")
            
            return True
            
        except Exception as e:
            print(f"[WARNING] Endpoint deployed but test failed: {e}")
            print("Check CloudWatch logs for details")
            return False
        
    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/deploy_single.py <approach_name>")
        print("Available approaches: cpu_minimal, cpu_large, lazy_loading, small_models")
        sys.exit(1)
    
    approach_name = sys.argv[1]
    success = deploy_single_approach(approach_name)
    
    if success:
        print("\n[SUCCESS] Deployment completed!")
        print("Next steps:")
        print("1. Update frontend to use this endpoint")
        print("2. Deploy frontend to Vercel")
        print("3. Test complete application")
    else:
        print("\n[ERROR] Deployment failed")
        print("Try a different approach or check AWS permissions")
