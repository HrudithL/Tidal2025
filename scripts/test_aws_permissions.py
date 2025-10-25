"""
Test AWS credentials and permissions for SageMaker endpoint invocation
"""
import os
import boto3
import json
from dotenv import load_dotenv

def test_aws_credentials():
    """Test AWS credentials and permissions"""
    
    print("Testing AWS Credentials and Permissions")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    session_token = os.getenv('AWS_SESSION_TOKEN')
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    
    print(f"Access Key ID: {access_key[:10]}..." if access_key else "Not set")
    print(f"Secret Key: {'*' * 10}..." if secret_key else "Not set")
    print(f"Session Token: {'Set' if session_token else 'Not set'}")
    print(f"Region: {region}")
    
    # Check if credentials are still placeholders
    if access_key == 'your_access_kfey_here' or secret_key == 'your_secret_key_here':
        print("\n❌ ERROR: You still have placeholder values in .env file!")
        print("Please edit .env with your actual AWS credentials.")
        return False
    
    if not access_key or not secret_key:
        print("\n❌ ERROR: Missing AWS credentials!")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
        return False
    
    # Test credentials with STS
    try:
        sts_client = boto3.client(
            'sts',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token if session_token else None
        )
        
        identity = sts_client.get_caller_identity()
        print(f"\n✅ AWS Credentials Valid!")
        print(f"Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}")
        
    except Exception as e:
        print(f"\n❌ AWS Credentials Invalid: {e}")
        return False
    
    # Test SageMaker permissions
    try:
        sagemaker_client = boto3.client(
            'sagemaker',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token if session_token else None
        )
        
        # List endpoints to test permissions
        endpoints = sagemaker_client.list_endpoints()
        print(f"\n✅ SageMaker Access Valid!")
        print(f"Found {len(endpoints['Endpoints'])} endpoints")
        
        # List existing endpoints
        for endpoint in endpoints['Endpoints']:
            print(f"  - {endpoint['EndpointName']}: {endpoint['EndpointStatus']}")
        
    except Exception as e:
        print(f"\n❌ SageMaker Access Failed: {e}")
        return False
    
    # Test SageMaker Runtime permissions
    try:
        runtime_client = boto3.client(
            'sagemaker-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token if session_token else None
        )
        
        print(f"\n✅ SageMaker Runtime Access Valid!")
        
    except Exception as e:
        print(f"\n❌ SageMaker Runtime Access Failed: {e}")
        return False
    
    print(f"\n🎉 All AWS permissions are working correctly!")
    return True

def test_endpoint_invocation():
    """Test endpoint invocation with proper error handling"""
    
    print("\nTesting Endpoint Invocation")
    print("=" * 30)
    
    load_dotenv()
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
    
    # Create runtime client
    runtime_client = boto3.client(
        'sagemaker-runtime',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    # Test health check
    test_payload = {"operation": "health"}
    
    try:
        print(f"Sending health check to endpoint: {endpoint_name}")
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read())
        print(f"✅ Health check successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        return True
        
    except Exception as e:
        print(f"❌ Endpoint invocation failed: {e}")
        
        # Check if endpoint exists
        try:
            sagemaker_client = boto3.client(
                'sagemaker',
                region_name=region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
            )
            
            endpoint_info = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
            print(f"Endpoint Status: {endpoint_info['EndpointStatus']}")
            
            if endpoint_info['EndpointStatus'] != 'InService':
                print(f"❌ Endpoint is not in service. Status: {endpoint_info['EndpointStatus']}")
                return False
            
        except Exception as describe_error:
            print(f"❌ Endpoint does not exist or cannot be accessed: {describe_error}")
            return False
        
        return False

if __name__ == "__main__":
    # Test credentials first
    if test_aws_credentials():
        # Test endpoint invocation
        test_endpoint_invocation()
    else:
        print("\n❌ Cannot test endpoint - AWS credentials are invalid")
        print("\nTo fix this:")
        print("1. Edit .env file with your actual AWS credentials")
        print("2. Make sure you have SageMaker permissions")
        print("3. Run this script again")
