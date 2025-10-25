"""
Check endpoint status and complete deployment
"""
import boto3
import json
import time
from dotenv import load_dotenv

def check_and_complete_deployment():
    """Check endpoint status and complete deployment if needed"""
    
    load_dotenv()
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
    
    print("Checking SageMaker Endpoint Status")
    print("=" * 40)
    
    # Initialize SageMaker client
    sagemaker_client = boto3.client(
        'sagemaker',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    try:
        # Get endpoint status
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        status = response['EndpointStatus']
        
        print(f"Endpoint: {endpoint_name}")
        print(f"Status: {status}")
        print(f"Creation Time: {response.get('CreationTime', 'Unknown')}")
        print(f"Last Modified: {response.get('LastModifiedTime', 'Unknown')}")
        
        if status == 'InService':
            print("\n[OK] Endpoint is ready!")
            return test_endpoint()
            
        elif status == 'Updating':
            print("\n[INFO] Endpoint is updating...")
            print("Waiting for update to complete...")
            
            # Wait for endpoint to be ready
            waiter = sagemaker_client.get_waiter('endpoint_in_service')
            waiter.wait(EndpointName=endpoint_name)
            
            print("[OK] Endpoint update completed!")
            return test_endpoint()
            
        elif status == 'Creating':
            print("\n[INFO] Endpoint is being created...")
            print("Waiting for creation to complete...")
            
            waiter = sagemaker_client.get_waiter('endpoint_in_service')
            waiter.wait(EndpointName=endpoint_name)
            
            print("[OK] Endpoint creation completed!")
            return test_endpoint()
            
        else:
            print(f"\n[WARNING] Endpoint status: {status}")
            print("This might indicate an issue. Check CloudWatch logs.")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to check endpoint: {e}")
        return False

def test_endpoint():
    """Test the endpoint with a health check"""
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
    
    print("\nTesting Endpoint")
    print("=" * 20)
    
    # Create SageMaker Runtime client
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
        
        print("Sending health check request...")
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read())
        print(f"[OK] Health check successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Test with simple audio data
        print("\nTesting with audio data...")
        import numpy as np
        import soundfile as sf
        import base64
        
        # Create a simple test audio (1 second of silence)
        sample_rate = 16000
        duration = 1.0
        audio_data = np.zeros(int(sample_rate * duration))
        
        # Convert to bytes
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, sample_rate, format='WAV')
        audio_bytes = audio_buffer.getvalue()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Test audio processing
        audio_payload = {"audio_bytes": audio_base64}
        
        response = runtime_client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(audio_payload)
        )
        
        result = json.loads(response['Body'].read())
        print(f"[OK] Audio processing successful!")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    import os
    import io
    
    success = check_and_complete_deployment()
    if success:
        print("\n[SUCCESS] SageMaker endpoint is working!")
        print("\nNext steps:")
        print("1. Update frontend to use SageMaker endpoint")
        print("2. Deploy frontend to Vercel")
        print("3. Test complete application")
        
        # Save endpoint configuration
        config = {
            "endpoint_name": os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint'),
            "region": os.getenv('AWS_DEFAULT_REGION', 'us-west-2'),
            "endpoint_url": f"https://runtime.sagemaker.{os.getenv('AWS_DEFAULT_REGION', 'us-west-2')}.amazonaws.com/endpoints/{os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')}/invocations"
        }
        
        with open("sagemaker_config.json", "w") as f:
            json.dump(config, f, indent=2)
        print(f"\nEndpoint configuration saved to sagemaker_config.json")
        
    else:
        print("\n[ERROR] Endpoint is not working properly.")
        print("Check CloudWatch logs for more details.")
