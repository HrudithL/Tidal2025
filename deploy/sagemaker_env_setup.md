# SageMaker Deployment with Environment Variables

## Quick Setup Guide

### Step 1: Install Dependencies

```bash
pip install -r requirements-sagemaker.txt
```

### Step 2: Set Up Environment Variables

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file** with your AWS credentials:
   ```env
   # AWS Credentials
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_DEFAULT_REGION=us-east-1
   
   # SageMaker Configuration
   SAGEMAKER_BUCKET_NAME=your-unique-bucket-name
   SAGEMAKER_ENDPOINT_NAME=sonicmuse-endpoint
   SAGEMAKER_INSTANCE_TYPE=ml.g4dn.xlarge
   
   # Optional
   MODEL_SIZE=small
   GEMINI_API_KEY=your_gemini_key_here
   ```

### Step 3: Create Model Package

```bash
python scripts/create_sagemaker_package.py
```

### Step 4: Deploy to SageMaker

```bash
python scripts/deploy_sagemaker_env.py
```

## Detailed Instructions

### Getting AWS Credentials

#### Option 1: AWS Event Account (Your Case)
If you have an event account with temporary credentials:

1. **Get credentials from AWS Console**:
   - Go to AWS Console → IAM → Users → Your User
   - Security credentials tab
   - Create access key

2. **Or use temporary credentials**:
   ```env
   AWS_ACCESS_KEY_ID=ASIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_SESSION_TOKEN=...  # Add this for temporary credentials
   ```

#### Option 2: Personal AWS Account
1. Create IAM user with SageMaker permissions
2. Generate access keys
3. Add to .env file

### Required AWS Permissions

Your AWS credentials need these permissions:
- `AmazonSageMakerFullAccess`
- `AmazonS3FullAccess`
- `IAMFullAccess` (for creating SageMaker role)

### Environment Variables Explained

```env
# Required
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# Optional (with defaults)
SAGEMAKER_BUCKET_NAME=sonicmuse-models-bucket  # Will be created if doesn't exist
SAGEMAKER_ENDPOINT_NAME=sonicmuse-endpoint
SAGEMAKER_INSTANCE_TYPE=ml.g4dn.xlarge
MODEL_SIZE=small
GEMINI_API_KEY=your_key_here  # Optional for script mode
```

### Deployment Process

The deployment script will:

1. **Verify credentials** - Test AWS access
2. **Create S3 bucket** - For model storage
3. **Upload model** - Your sonicmuse-model.tar.gz
4. **Create SageMaker role** - IAM role for SageMaker
5. **Create model** - SageMaker model from S3
6. **Deploy endpoint** - GPU instance with your model
7. **Test endpoint** - Verify it's working
8. **Save config** - Configuration for frontend

### Expected Output

```
🚀 SonicMuse SageMaker Setup
========================================
✓ AWS credentials verified successfully
Step 1: Creating S3 bucket...
Created bucket sonicmuse-models-bucket
Step 2: Uploading model package...
Model uploaded to s3://sonicmuse-models-bucket/models/sonicmuse-model.tar.gz
Step 3: Creating SageMaker model...
SageMaker model created successfully
Step 4: Deploying endpoint...
Endpoint deployed successfully: sonicmuse-endpoint
Step 5: Testing endpoint...
Endpoint test successful
🎉 Deployment completed successfully!
Endpoint URL: https://sonicmuse-endpoint.us-east-1.sagemaker.amazonaws.com
```

### Troubleshooting

#### Common Issues

1. **"AWS credentials verification failed"**
   ```bash
   # Check your .env file
   cat .env
   
   # Verify credentials manually
   aws sts get-caller-identity
   ```

2. **"Bucket already exists"**
   ```bash
   # Change bucket name in .env
   SAGEMAKER_BUCKET_NAME=your-unique-bucket-name-12345
   ```

3. **"Permission denied"**
   - Ensure your AWS user has SageMaker permissions
   - Check if you're using temporary credentials (add AWS_SESSION_TOKEN)

4. **"Model package not found"**
   ```bash
   # Create model package first
   python scripts/create_sagemaker_package.py
   ```

#### Debug Mode

Run with debug logging:
```bash
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
exec(open('scripts/deploy_sagemaker_env.py').read())
"
```

### Cost Monitoring

Monitor your SageMaker costs:
1. **AWS Console** → Billing → Cost Explorer
2. **Filter by service**: SageMaker
3. **Set up billing alerts** for $10, $50, $100 thresholds

### Cleanup

To avoid ongoing costs:
```python
# Delete endpoint when done
import boto3
sagemaker = boto3.client('sagemaker')
sagemaker.delete_endpoint(EndpointName='sonicmuse-endpoint')
```

### Next Steps

After successful deployment:

1. **Update frontend**:
   ```typescript
   // frontend/src/api.ts
   const API_BASE_URL = 'https://sonicmuse-endpoint.us-east-1.sagemaker.amazonaws.com';
   ```

2. **Deploy frontend to Vercel**:
   ```bash
   cd frontend
   vercel --prod
   ```

3. **Test complete application**:
   - Upload audio file
   - Generate background music
   - Download mixed result
