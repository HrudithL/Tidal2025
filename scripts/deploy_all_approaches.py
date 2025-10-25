"""
Deploy all 4 SageMaker optimization approaches and test which works
"""
import os
import json
import boto3
import time
from dotenv import load_dotenv

def deploy_all_approaches():
    """Deploy all 4 approaches and determine which works"""
    
    load_dotenv()
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    bucket_name = os.getenv('SAGEMAKER_BUCKET_NAME', 'sonicmuse-models-0ubdu3d6')
    
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
    
    approaches = {
        "cpu_minimal": {
            "package": "sonicmuse-cpu_minimal.tar.gz",
            "instance": "ml.m5.large",
            "description": "CPU-only minimal (no AI models)",
            "priority": 1
        },
        "cpu_large": {
            "package": "sonicmuse-cpu_large.tar.gz", 
            "instance": "ml.m5.2xlarge",
            "description": "CPU-only for large instances",
            "priority": 2
        },
        "lazy_loading": {
            "package": "sonicmuse-lazy_loading.tar.gz",
            "instance": "ml.m5.xlarge", 
            "description": "Lazy loading (models load on demand)",
            "priority": 3
        },
        "small_models": {
            "package": "sonicmuse-small_models.tar.gz",
            "instance": "ml.m5.xlarge",
            "description": "Smallest AI models (tiny Whisper)",
            "priority": 4
        }
    }
    
    results = {}
    
    print("=" * 70)
    print("Deploying All SageMaker Optimization Approaches")
    print("=" * 70)
    
    # Sort by priority (most likely to succeed first)
    sorted_approaches = sorted(approaches.items(), key=lambda x: x[1]['priority'])
    
    for approach_name, config in sorted_approaches:
        print(f"\n{'='*20} {approach_name.upper()} {'='*20}")
        print(f"Description: {config['description']}")
        print(f"Instance: {config['instance']}")
        print(f"Package: {config['package']}")
        print("-" * 50)
        
        try:
            result = deploy_single_approach(
                approach_name, config, s3_client, sagemaker_client, 
                bucket_name, role_arn, region
            )
            results[approach_name] = result
            
            if result.get("status") == "success":
                print(f"[SUCCESS] {approach_name} deployed successfully!")
                print(f"Endpoint: {result.get('endpoint_name')}")
                
                # Test the endpoint
                test_result = test_endpoint(result.get('endpoint_name'), region)
                results[approach_name]["test_result"] = test_result
                
                if test_result.get("status") == "healthy":
                    print(f"[SUCCESS] {approach_name} is working!")
                    print(f"[RECOMMENDED] Use {approach_name} as your production approach")
                    break  # Stop after first successful deployment
                else:
                    print(f"[WARNING] {approach_name} deployed but not healthy")
            else:
                print(f"[FAILED] {approach_name}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[ERROR] {approach_name} failed: {e}")
            results[approach_name] = {"status": "error", "error": str(e)}
    
    # Final summary
    print("\n" + "=" * 70)
    print("DEPLOYMENT SUMMARY")
    print("=" * 70)
    
    successful = []
    for name, result in results.items():
        status = result.get("status", "unknown")
        desc = approaches[name]["description"]
        print(f"\n{name}: {desc}")
        print(f"  Status: {status}")
        
        if status == "success":
            successful.append(name)
            if "test_result" in result:
                test_status = result["test_result"].get("status", "unknown")
                print(f"  Test: {test_status}")
    
    if successful:
        print(f"\n[SUCCESS] Working approaches: {', '.join(successful)}")
        print(f"[RECOMMENDED] Production approach: {successful[0]}")
        
        # Save the working configuration
        config = {
            "working_approach": successful[0],
            "endpoint_name": results[successful[0]].get("endpoint_name"),
            "region": region,
            "endpoint_url": f"https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{results[successful[0]].get('endpoint_name')}/invocations"
        }
        
        with open("sagemaker_working_config.json", "w") as f:
            json.dump(config, f, indent=2)
        print(f"[OK] Working configuration saved to sagemaker_working_config.json")
        
    else:
        print("\n[ERROR] No approaches successfully deployed")
        print("Consider:")
        print("1. Check AWS permissions")
        print("2. Verify model packages exist")
        print("3. Try different instance types")
    
    return results

def deploy_single_approach(approach_name, config, s3_client, sagemaker_client, 
                          bucket_name, role_arn, region):
    """Deploy a single approach"""
    
    package_file = config["package"]
    instance_type = config["instance"]
    
    # Check if package exists
    if not os.path.exists(package_file):
        return {"status": "error", "error": f"Package {package_file} not found"}
    
    try:
        # Step 1: Upload to S3
        print(f"Step 1: Uploading {package_file} to S3...")
        s3_key = f"models/{package_file}"
        s3_model_uri = f"s3://{bucket_name}/{s3_key}"
        
        s3_client.upload_file(package_file, bucket_name, s3_key)
        print(f"[OK] Uploaded to {s3_model_uri}")
        
        # Step 2: Create SageMaker model
        # Fix naming: SageMaker doesn't allow underscores, only hyphens
        safe_approach_name = approach_name.replace('_', '-')
        print(f"Step 2: Creating SageMaker model...")
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
        print(f"Step 3: Creating endpoint configuration...")
        config_name = f"sonicmuse-{safe_approach_name}-config-{int(time.time())}"
        
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
        print(f"[OK] Endpoint config created: {config_name}")
        
        # Step 4: Create endpoint
        print(f"Step 4: Creating endpoint...")
        endpoint_name = f"sonicmuse-{safe_approach_name}-{int(time.time())}"
        
        sagemaker_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=config_name
        )
        print(f"[OK] Endpoint creation initiated: {endpoint_name}")
        
        # Step 5: Wait for endpoint to be ready
        print(f"Step 5: Waiting for endpoint to be ready...")
        waiter = sagemaker_client.get_waiter('endpoint_in_service')
        waiter.wait(EndpointName=endpoint_name)
        print(f"[OK] Endpoint is ready: {endpoint_name}")
        
        return {
            "status": "success",
            "endpoint_name": endpoint_name,
            "model_name": model_name,
            "config_name": config_name,
            "instance_type": instance_type
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_endpoint(endpoint_name, region):
    """Test an endpoint"""
    
    runtime_client = boto3.client(
        'sagemaker-runtime',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    try:
        # Test health check
        test_payload = {"operation": "health"}
        
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read())
        return {"status": "healthy", "response": result}
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    results = deploy_all_approaches()
    
    # Save detailed results
    with open("sagemaker_deployment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[OK] Detailed results saved to sagemaker_deployment_results.json")
