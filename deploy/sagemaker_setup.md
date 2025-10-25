# SageMaker Deployment Guide for SonicMuse

## Prerequisites

- AWS Account with SageMaker access
- AWS CLI configured (`aws configure`)
- Python 3.8+ with boto3 installed
- Your SonicMuse code ready

## Quick Start

### Step 1: Install Dependencies

```bash
pip install boto3 sagemaker
```

### Step 2: Create Model Package

```bash
# Run the package creation script
python scripts/create_sagemaker_package.py
```

This will create:
- `sagemaker/model/` directory with your code
- `sonicmuse-model.tar.gz` compressed package

### Step 3: Deploy to SageMaker

```bash
# Edit the bucket name in deploy_sagemaker.py
# Then run deployment
python scripts/deploy_sagemaker.py
```

### Step 4: Test Your Endpoint

```python
import boto3
import json

# Test the endpoint
sagemaker_client = boto3.client('sagemaker', region_name='us-east-1')

response = sagemaker_client.invoke_endpoint(
    EndpointName='sonicmuse-endpoint',
    ContentType='application/json',
    Body=json.dumps({
        "operation": "analyze",
        "audio_data": "base64_encoded_audio_data"
    })
)

result = json.loads(response['Body'].read())
print(result)
```

## Manual Deployment Steps

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-sonicmuse-bucket
```

### 2. Upload Model Package

```bash
aws s3 cp sonicmuse-model.tar.gz s3://your-sonicmuse-bucket/models/
```

### 3. Create SageMaker Model

```python
from sagemaker.pytorch import PyTorchModel
from sagemaker import get_execution_role

model = PyTorchModel(
    model_data='s3://your-sonicmuse-bucket/models/sonicmuse-model.tar.gz',
    role=get_execution_role(),
    entry_point='inference.py',
    framework_version='2.0.0',
    py_version='py310',
    instance_type='ml.g4dn.xlarge'
)
```

### 4. Deploy Endpoint

```python
predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.g4dn.xlarge',
    endpoint_name='sonicmuse-endpoint'
)
```

## Configuration

### Environment Variables

Set these in your SageMaker model:

```python
env = {
    'TORCH_HOME': '/opt/ml/model/models',
    'HF_HOME': '/opt/ml/model/models',
    'MODEL_SIZE': 'small',
    'GEMINI_API_KEY': 'your_key_here'
}
```

### Instance Types

- **ml.g4dn.xlarge**: 1 GPU, 4 vCPU, 16 GB RAM (~$0.526/hour)
- **ml.g4dn.2xlarge**: 1 GPU, 8 vCPU, 32 GB RAM (~$0.752/hour)
- **ml.g4dn.4xlarge**: 1 GPU, 16 vCPU, 64 GB RAM (~$1.204/hour)

## Cost Optimization

### Auto Scaling

```python
from sagemaker.model_monitor import DefaultModelMonitor

# Set up auto scaling
sagemaker_client.put_scaling_policy(
    PolicyName='sonicmuse-scaling',
    ServiceNamespace='sagemaker',
    ResourceId=f'endpoint/{endpoint_name}/variant/AllTraffic',
    ScalableDimension='sagemaker:variant:DesiredInstanceCount',
    PolicyType='TargetTrackingScaling',
    TargetTrackingScalingPolicyConfiguration={
        'TargetValue': 70.0,
        'PredefinedMetricSpecification': {
            'PredefinedMetricType': 'SageMakerVariantInvocationsPerInstance'
        }
    }
)
```

### Spot Instances

```python
# Use spot instances for cost savings
predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.g4dn.xlarge',
    endpoint_name='sonicmuse-endpoint',
    use_spot_instances=True,
    max_wait_time_in_seconds=3600
)
```

## Monitoring

### CloudWatch Metrics

Monitor these metrics:
- `Invocations`: Number of requests
- `ModelLatency`: Response time
- `OverheadLatency`: SageMaker overhead
- `Invocation4XXErrors`: Client errors
- `Invocation5XXErrors`: Server errors

### Custom Metrics

```python
# Add custom metrics in inference.py
import boto3

cloudwatch = boto3.client('cloudwatch')

def log_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='SonicMuse',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
        ]
    )
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
   ```bash
   # Check model files in S3
   aws s3 ls s3://your-bucket/models/ --recursive
   ```

2. **Memory Issues**
   ```python
   # Use larger instance type
   instance_type='ml.g4dn.2xlarge'
   ```

3. **Timeout Errors**
   ```python
   # Increase timeout
   predictor = model.deploy(
       initial_instance_count=1,
       instance_type='ml.g4dn.xlarge',
       endpoint_name='sonicmuse-endpoint',
       wait=True,
       update_endpoint=False,
       model_data_download_timeout=3600
   )
   ```

### Debugging

```python
# Check endpoint status
response = sagemaker_client.describe_endpoint(EndpointName='sonicmuse-endpoint')
print(response['EndpointStatus'])

# Check endpoint configuration
response = sagemaker_client.describe_endpoint_config(EndpointConfigName='sonicmuse-endpoint')
print(response)
```

## Cleanup

```python
# Delete endpoint
sagemaker_client.delete_endpoint(EndpointName='sonicmuse-endpoint')

# Delete endpoint configuration
sagemaker_client.delete_endpoint_config(EndpointConfigName='sonicmuse-endpoint')

# Delete model
sagemaker_client.delete_model(ModelName='sonicmuse-model')
```

## Integration with Frontend

Update your frontend API configuration:

```typescript
// frontend/src/api.ts
const SAGEMAKER_ENDPOINT = 'https://sonicmuse-endpoint.us-east-1.sagemaker.amazonaws.com';

class SonicMuseAPI {
  async composeMusic(file: File, request: ComposeRequest) {
    // Convert file to base64
    const audioData = await this.fileToBase64(file);
    
    const payload = {
      operation: 'compose',
      audio_data: audioData,
      duration: request.duration,
      seed: request.seed,
      intensity: request.intensity
    };
    
    const response = await fetch(SAGEMAKER_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    return response.json();
  }
  
  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result as string;
        resolve(base64.split(',')[1]); // Remove data:audio/... prefix
      };
      reader.onerror = error => reject(error);
    });
  }
}
```
