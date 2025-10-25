# AWS EC2 Setup Guide for SonicMuse Backend

## Prerequisites

- AWS Account with EC2 access
- AWS CLI configured (optional but recommended)
- Basic knowledge of Linux command line

## Step 1: Launch EC2 Instance

### 1.1 Instance Configuration
1. Go to AWS EC2 Console
2. Click "Launch Instance"
3. Choose "Ubuntu Server 22.04 LTS" (Free tier eligible)
4. Select **g4dn.xlarge** instance type (GPU-enabled)
   - **Important**: This instance type provides NVIDIA T4 GPU
   - Cost: ~$0.526/hour (~$380/month if running 24/7)
   - For testing, consider using Spot Instances for ~70% cost savings

### 1.2 Security Group Configuration
Create a new security group with these inbound rules:
- **SSH (22)**: Your IP only
- **HTTP (80)**: 0.0.0.0/0 (for Let's Encrypt)
- **HTTPS (443)**: 0.0.0.0/0
- **Custom TCP (8000)**: 0.0.0.0/0 (for API, restrict later)

### 1.3 Storage Configuration
- **Root Volume**: 30 GB gp3 (minimum)
- **Additional Volume**: 100 GB gp3 for model caching
  - Mount point: `/models`
  - This stores downloaded AI models

## Step 2: Connect to Instance

```bash
# Replace with your instance's public IP
ssh -i your-key.pem ubuntu@your-instance-ip
```

## Step 3: Install System Dependencies

### 3.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 3.2 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install NVIDIA Docker (for GPU support)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 3.3 Install NVIDIA Drivers
```bash
# Install NVIDIA drivers
sudo apt install nvidia-driver-535 -y
sudo reboot

# After reboot, verify GPU is accessible
nvidia-smi
```

### 3.4 Install Additional Dependencies
```bash
# Install Python, Git, and other tools
sudo apt install python3 python3-pip git curl wget unzip -y

# Install FFmpeg (required for audio processing)
sudo apt install ffmpeg -y
```

## Step 4: Clone and Setup Project

### 4.1 Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/your-username/sonicmuse.git
cd sonicmuse
```

### 4.2 Create Environment File
```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Update the environment variables:
```env
TORCH_HOME=/models
HF_HOME=/models
CORS_ALLOW_ORIGINS=https://your-frontend.vercel.app
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_SIZE=small
HOST=0.0.0.0
PORT=8000
```

### 4.3 Mount Additional Volume
```bash
# Format and mount the additional volume
sudo mkfs.ext4 /dev/nvme1n1
sudo mkdir -p /models
sudo mount /dev/nvme1n1 /models
sudo chown ubuntu:ubuntu /models

# Make mount persistent
echo '/dev/nvme1n1 /models ext4 defaults 0 0' | sudo tee -a /etc/fstab
```

## Step 5: Build and Run Backend

### 5.1 Build Docker Image
```bash
cd backend
sudo docker build -t sonicmuse-api .
```

### 5.2 Run Container
```bash
sudo docker run -d \
  --name sonicmuse-backend \
  --gpus all \
  -p 8000:8000 \
  -v /models:/models \
  --env-file .env \
  --restart unless-stopped \
  sonicmuse-api
```

### 5.3 Verify Backend is Running
```bash
# Check container status
sudo docker ps

# Check logs
sudo docker logs sonicmuse-backend

# Test health endpoint
curl http://localhost:8000/health
```

## Step 6: Setup Nginx Reverse Proxy

### 6.1 Install Nginx
```bash
sudo apt install nginx -y
```

### 6.2 Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/sonicmuse
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
        
        # File upload limits
        client_max_body_size 30M;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6.3 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/sonicmuse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Setup SSL with Let's Encrypt

### 7.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 7.2 Get SSL Certificate
```bash
# Replace with your domain
sudo certbot --nginx -d your-domain.com
```

### 7.3 Test SSL
```bash
# Test certificate renewal
sudo certbot renew --dry-run
```

## Step 8: Verify Deployment

### 8.1 Test API Endpoints
```bash
# Health check
curl https://your-domain.com/health

# Test with a sample audio file
curl -X POST -F "file=@sample.wav" https://your-domain.com/api/analyze
```

### 8.2 Monitor Resources
```bash
# Check GPU usage
nvidia-smi

# Check Docker container
sudo docker stats sonicmuse-backend

# Check disk usage
df -h
```

## Step 9: Production Optimizations

### 9.1 Setup Log Rotation
```bash
sudo nano /etc/logrotate.d/sonicmuse
```

Add:
```
/var/log/sonicmuse/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
```

### 9.2 Setup Monitoring
```bash
# Install htop for system monitoring
sudo apt install htop -y

# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Disk Usage:"
df -h
echo "Memory Usage:"
free -h
echo "GPU Status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
echo "Docker Status:"
sudo docker ps
EOF

chmod +x monitor.sh
```

## Troubleshooting

### Common Issues

1. **GPU not detected in Docker**:
   ```bash
   # Verify nvidia-docker2 is installed
   sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. **Out of disk space**:
   ```bash
   # Clean up Docker images
   sudo docker system prune -a
   
   # Check model cache size
   du -sh /models/*
   ```

3. **API not responding**:
   ```bash
   # Check container logs
   sudo docker logs sonicmuse-backend
   
   # Restart container
   sudo docker restart sonicmuse-backend
   ```

4. **SSL certificate issues**:
   ```bash
   # Renew certificate manually
   sudo certbot renew
   
   # Check certificate status
   sudo certbot certificates
   ```

### Performance Tuning

1. **Enable GPU memory optimization**:
   ```bash
   # Add to Docker run command
   --gpus '"device=0"'
   ```

2. **Optimize Nginx for large files**:
   ```nginx
   # Add to nginx config
   proxy_buffering off;
   proxy_request_buffering off;
   ```

3. **Setup swap file** (if needed):
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

## Cost Optimization

1. **Use Spot Instances** for development/testing
2. **Stop instance** when not in use
3. **Use smaller instance** for development (g4dn.large)
4. **Monitor usage** with AWS Cost Explorer

## Security Considerations

1. **Restrict API access** to frontend domain only
2. **Use AWS WAF** for additional protection
3. **Regular security updates**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
4. **Backup important data** regularly
5. **Use IAM roles** instead of access keys when possible
