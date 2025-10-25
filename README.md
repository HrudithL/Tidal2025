# SonicMuse: AI Background Music Generator

<div align="center">

![SonicMuse Logo](https://via.placeholder.com/200x80/0ea5e9/ffffff?text=SonicMuse)

**Generate intelligent background music that adapts to your speech audio**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)

</div>

## 🎵 Overview

SonicMuse is a full-stack AI application that analyzes speech audio and generates perfectly synchronized background music. Using advanced AI models including Whisper, MusicGen, and Gemini, it creates professional-quality audio compositions with intelligent ducking and mood-aware generation.

### ✨ Key Features

- **🎤 Audio Analysis**: Upload speech audio for automatic mood and tempo analysis
- **🤖 AI Music Generation**: Generate background music using Meta's MusicGen model
- **🎛️ Professional Mixing**: Intelligent sidechain ducking and loudness normalization
- **📝 Script Mode**: Generate music from text scripts using Gemini AI
- **🎨 Visual Feedback**: Real-time waveform display and emotion arc visualization
- **⚡ Fast Processing**: Optimized for quick feedback with GPU acceleration
- **🌐 Web Interface**: Modern React frontend with dark theme

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   AI Models     │
│                 │    │                 │    │                 │
│ • Audio Upload  │◄──►│ • Whisper ASR   │◄──►│ • Whisper       │
│ • Waveform      │    │ • Feature Ext.  │    │ • MusicGen      │
│ • Controls      │    │ • Music Gen.    │    │ • CREPE         │
│ • Player        │    │ • Audio Mixing  │    │ • Gemini        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.10+, CUDA-capable GPU (recommended), Docker
- **Frontend**: Node.js 18+, npm
- **Cloud**: AWS EC2 account, Vercel account (for deployment)

### Local Development

#### 1. Clone Repository
```bash
git clone https://github.com/your-username/sonicmuse.git
cd sonicmuse
```

#### 2. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run locally (CPU mode)
python app.py
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 4. Test the Application
1. Open http://localhost:5173
2. Upload an audio file
3. Generate background music
4. Download the mixed result

## 📁 Project Structure

```
sonicmuse/
├── backend/                 # FastAPI backend
│   ├── app.py              # Main application
│   ├── core/               # Core modules
│   │   ├── asr.py          # Speech recognition
│   │   ├── features.py     # Audio feature extraction
│   │   ├── prompt.py       # Prompt generation
│   │   ├── music.py        # Music generation
│   │   ├── mix.py          # Audio mixing
│   │   └── gemini.py       # Script analysis
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Container configuration
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api.ts         # API client
│   │   └── types.ts       # TypeScript types
│   ├── package.json       # Node dependencies
│   └── tailwind.config.js # Styling configuration
├── scripts/               # Utility scripts
│   ├── smoke_test.py      # Backend testing
│   └── download_data.py   # Dataset downloader
├── deploy/                # Deployment configurations
│   ├── aws_setup.md       # AWS deployment guide
│   ├── vercel_setup.md    # Vercel deployment guide
│   ├── docker-compose.yml # Container orchestration
│   └── nginx.conf         # Reverse proxy config
└── data/                  # Datasets (gitignored)
    ├── inputs/           # Test audio files
    ├── eval/             # Validation data
    ├── music_ref/        # Reference tracks
    └── scripts/          # Text scripts
```

## 🔧 API Documentation

### Endpoints

#### Health Check
```http
GET /health
```
Returns system status and loaded models.

#### Audio Analysis
```http
POST /analyze
Content-Type: multipart/form-data
Body: file (audio file)
```
Analyzes uploaded audio and returns features, mood, and generated prompt.

#### Music Generation
```http
POST /generate
Content-Type: multipart/form-data
Body: prompt, duration, seed, tempo_bpm, key
```
Generates background music from text prompt.

#### Audio Mixing
```http
POST /mix
Content-Type: multipart/form-data
Body: file_dialogue, file_bg, bg_db, ducking
```
Mixes dialogue with background music using sidechain ducking.

#### One-Shot Composition
```http
POST /compose
Content-Type: multipart/form-data
Body: file, duration, seed, intensity
```
Complete pipeline: analyze → generate → mix.

#### Script to Background
```http
POST /script-to-bg
Content-Type: multipart/form-data
Body: script, duration, style, intensity
```
Generates background music from text script using Gemini.

## 🚀 Deployment

### Backend (AWS EC2)

1. **Launch EC2 Instance**
   - Instance type: g4dn.xlarge (GPU-enabled)
   - OS: Ubuntu 22.04 LTS
   - Storage: 30GB root + 100GB for models

2. **Install Dependencies**
   ```bash
   # Install Docker and NVIDIA support
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt install nvidia-docker2 -y
   
   # Install NVIDIA drivers
   sudo apt install nvidia-driver-535 -y
   ```

3. **Deploy Application**
   ```bash
   # Clone repository
   git clone https://github.com/your-username/sonicmuse.git
   cd sonicmuse/backend
   
   # Build and run
   sudo docker build -t sonicmuse-api .
   sudo docker run -d --gpus all -p 8000:8000 sonicmuse-api
   ```

4. **Setup Nginx & SSL**
   - Follow detailed guide in `deploy/aws_setup.md`

### Frontend (Vercel)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd frontend
   vercel
   ```

3. **Configure Environment**
   ```bash
   vercel env add VITE_API_BASE
   # Enter: https://your-api-domain.com/api
   ```

4. **Production Deploy**
   ```bash
   vercel --prod
   ```

For detailed deployment instructions, see:
- [AWS EC2 Setup Guide](deploy/aws_setup.md)
- [Vercel Deployment Guide](deploy/vercel_setup.md)

## 🧪 Testing

### Backend Testing
```bash
cd scripts
python smoke_test.py
```

### Frontend Testing
```bash
cd frontend
npm run test
```

### End-to-End Testing
1. Deploy both backend and frontend
2. Test audio upload and generation
3. Test script mode functionality
4. Verify download functionality

## 📊 Performance

### Benchmarks (g4dn.xlarge)
- **Audio Analysis**: ~2-5 seconds
- **Music Generation**: ~10-15 seconds (30s audio)
- **Audio Mixing**: ~1-2 seconds
- **Total Pipeline**: ~15-25 seconds

### Optimization Tips
- Use GPU acceleration for faster inference
- Enable model caching for repeated requests
- Implement request queuing for high traffic
- Use CDN for static assets

## 🔒 Security

### Backend Security
- Rate limiting (10 requests/minute per IP)
- File size limits (30MB max)
- Input validation and sanitization
- CORS configuration
- SSL/TLS encryption

### Frontend Security
- Environment variable protection
- Content Security Policy
- HTTPS enforcement
- Input validation

## 🛠️ Configuration

### Environment Variables

#### Backend (.env)
```env
TORCH_HOME=/models              # Model cache directory
HF_HOME=/models                 # Hugging Face cache
CORS_ALLOW_ORIGINS=https://...  # Allowed origins
GEMINI_API_KEY=your_key         # Gemini API key
MODEL_SIZE=small                # Model size (small/medium)
HOST=0.0.0.0                   # Server host
PORT=8000                       # Server port
```

#### Frontend (.env)
```env
VITE_API_BASE=https://your-api-domain.com/api
```

### Model Configuration
- **Whisper**: small/medium models for ASR
- **MusicGen**: small model for music generation
- **CREPE**: full model for pitch detection
- **Gemini**: Pro model for script analysis

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues
1. **GPU not detected**
   ```bash
   nvidia-smi  # Check GPU status
   sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

2. **Out of memory**
   ```bash
   # Reduce model size or increase instance memory
   export MODEL_SIZE=small
   ```

3. **API not responding**
   ```bash
   sudo docker logs sonicmuse-backend
   sudo docker restart sonicmuse-backend
   ```

#### Frontend Issues
1. **API connection failed**
   - Check CORS settings
   - Verify API URL in environment variables
   - Test API endpoint directly

2. **Build failures**
   ```bash
   npm run build  # Check for errors
   npm audit      # Check for vulnerabilities
   ```

### Performance Issues
1. **Slow generation**
   - Ensure GPU is being used
   - Check model cache is populated
   - Monitor system resources

2. **High memory usage**
   - Use smaller models
   - Implement model unloading
   - Increase instance memory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Add tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Meta AI** for MusicGen model
- **OpenAI** for Whisper model
- **Google** for Gemini API
- **Hugging Face** for model hosting
- **FastAPI** for the excellent web framework
- **React** and **Vite** for the frontend stack

## 📞 Support

- **Documentation**: Check this README and deployment guides
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

## 🔮 Roadmap

### Short Term
- [ ] Add more music styles and presets
- [ ] Implement real-time audio processing
- [ ] Add batch processing capabilities
- [ ] Improve mobile responsiveness

### Long Term
- [ ] Support for video input
- [ ] Multi-language script analysis
- [ ] Custom model training
- [ ] API rate limiting and monetization
- [ ] Integration with popular DAWs

---

<div align="center">

**Made with ❤️ by the SonicMuse Team**

[Website](https://sonicmuse.ai) • [Documentation](https://docs.sonicmuse.ai) • [Support](https://github.com/your-username/sonicmuse/issues)

</div>
