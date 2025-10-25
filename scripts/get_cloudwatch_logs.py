"""
Script to fetch CloudWatch logs for SageMaker endpoint
"""
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

def get_cloudwatch_logs():
    """Fetch recent CloudWatch logs for the SageMaker endpoint"""
    
    load_dotenv()
    
    region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
    endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'sonicmuse-endpoint')
    
    # Create CloudWatch Logs client
    logs_client = boto3.client(
        'logs',
        region_name=region,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN') if os.getenv('AWS_SESSION_TOKEN') else None
    )
    
    log_group_name = f"/aws/sagemaker/Endpoints/{endpoint_name}"
    
    print(f"Fetching logs from: {log_group_name}")
    print("=" * 50)
    
    try:
        # Get log streams
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not response['logStreams']:
            print("No log streams found. The endpoint might not have generated logs yet.")
            return
        
        # Get events from the most recent log stream
        latest_stream = response['logStreams'][0]
        stream_name = latest_stream['logStreamName']
        
        print(f"Latest log stream: {stream_name}")
        print(f"Last event time: {latest_stream.get('lastEventTime', 'Unknown')}")
        print("-" * 50)
        
        # Get log events
        events_response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=stream_name,
            startTime=int((datetime.now() - timedelta(hours=1)).timestamp() * 1000),
            limit=100
        )
        
        events = events_response['events']
        
        if not events:
            print("No recent events found.")
            return
        
        print(f"Found {len(events)} recent events:")
        print("-" * 50)
        
        for event in events[-20:]:  # Show last 20 events
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message']
            print(f"[{timestamp}] {message}")
        
    except logs_client.exceptions.ResourceNotFoundException:
        print(f"Log group '{log_group_name}' not found.")
        print("This might mean:")
        print("1. The endpoint hasn't been invoked yet")
        print("2. The endpoint name is incorrect")
        print("3. The endpoint is in a different region")
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    get_cloudwatch_logs()
