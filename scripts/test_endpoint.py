"""
Test the deployed SageMaker endpoint
"""
import boto3
import json
import os
from dotenv import load_dotenv

def test_endpoint():
    """Test the deployed SageMaker endpoint"""
    
    load_dotenv()
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
    
    print("Testing SageMaker Endpoint")
    print("=" * 30)
    print(f"Endpoint: {endpoint_name}")
    print(f"Region: {region}")
    
    # Create SageMaker Runtime client
    runtime_client = boto3.client(
        'sagemaker-runtime',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    # Test payload
    test_payload = {
        "operation": "health"
    }
    
    try:
        print("\nSending test request...")
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read())
        print("SUCCESS! Endpoint is working!")
        print(f"Response: {result}")
        
        # Get endpoint URL
        endpoint_url = f"https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint_name}/invocations"
        print(f"\nEndpoint URL: {endpoint_url}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_endpoint()
    if success:
        print("\n🎉 SageMaker deployment is complete and working!")
        print("\nNext steps:")
        print("1. Update frontend to use the SageMaker endpoint")
        print("2. Deploy frontend to Vercel")
        print("3. Test the complete application")
    else:
        print("\n❌ Endpoint test failed. Check the logs.")
