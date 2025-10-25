"""
Create optimized SageMaker model package with lightweight inference
"""
import os
import shutil
import tarfile
import json
from pathlib import Path

def create_optimized_package():
    """Create an optimized SageMaker model package"""
    
    sagemaker_dir = Path("sagemaker")
    model_dir = sagemaker_dir / "model"

    # Clean up previous build
    if sagemaker_dir.exists():
        shutil.rmtree(sagemaker_dir)
    os.makedirs(model_dir, exist_ok=True)

    print("Creating optimized SageMaker model package...")
    
    # Copy essential backend files only
    essential_files = [
        Path("backend/core"),
        Path("backend/requirements.txt"),
        Path("backend/.env.example")
    ]

    for src in essential_files:
        if src.is_file():
            shutil.copy2(src, model_dir / src.name)
        elif src.is_dir():
            shutil.copytree(src, model_dir / src.name, dirs_exist_ok=True)
    
    print("[OK] Essential files copied")
    
    # Create optimized inference.py
    create_optimized_inference(model_dir)
    
    # Create lightweight requirements.txt
    create_lightweight_requirements(model_dir)
    
    # Create environment.json
    create_environment_config(model_dir)
    
    # Create model package
    create_model_tarball(sagemaker_dir)
    
    print("[OK] Optimized SageMaker model package created!")

def create_optimized_inference(model_dir):
    """Create optimized inference.py"""
    
    inference_code = '''
import os
import json
import logging
import torch
import base64
import io
import soundfile as sf
import numpy as np
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('SM_LOG_LEVEL', 'INFO').upper())

# Global variables for models
_models_loaded = False
_model_config = {}

def model_fn(model_dir):
    """Load models with optimized loading strategy"""
    global _models_loaded, _model_config

    if not _models_loaded:
        logger.info(f"Loading models from {model_dir}")
        
        # Load environment variables
        env_path = os.path.join(model_dir, "environment.json")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_vars = json.load(f)
                for key, value in env_vars.items():
                    os.environ[key] = str(value)

        model_size = os.getenv("MODEL_SIZE", "small")
        
        try:
            logger.info("Starting optimized model loading...")
            
            # Check GPU availability
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            models = {}
            
            # Load Whisper model (lightweight)
            try:
                from faster_whisper import WhisperModel
                logger.info("Loading Whisper model...")
                whisper_model = WhisperModel(
                    model_size, 
                    device=device, 
                    compute_type="float16" if device == "cuda" else "int8"
                )
                models['whisper'] = whisper_model
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
                models['whisper'] = None
            
            # Load MusicGen model (more resource intensive)
            try:
                from audiocraft.models import MusicGen
                logger.info("Loading MusicGen model...")
                musicgen_model = MusicGen.get_pretrained(f"facebook/musicgen-{model_size}")
                musicgen_model.set_generation_params(duration=30)
                models['musicgen'] = musicgen_model
                logger.info("MusicGen model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load MusicGen: {e}")
                models['musicgen'] = None
            
            _models_loaded = True
            _model_config = {
                "model_size": model_size, 
                "gpu_available": torch.cuda.is_available(),
                "device": device,
                "models": models
            }
            logger.info(f"Model loading completed. Config: {_model_config}")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            _model_config = {
                "model_size": model_size,
                "gpu_available": torch.cuda.is_available(),
                "device": "cpu",
                "models": {},
                "error": str(e)
            }
            _models_loaded = True
    
    return _model_config

def input_fn(request_body, request_content_type):
    """Deserialize input request"""
    logger.info(f"Received request with content type: {request_content_type}")
    
    if request_content_type == "application/json":
        try:
            return json.loads(request_body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {"error": "Invalid JSON"}
    
    elif request_content_type == "application/octet-stream":
        return {"audio_bytes": request_body}
    
    else:
        logger.error(f"Unsupported content type: {request_content_type}")
        return {"error": f"Unsupported content type: {request_content_type}"}

def predict_fn(input_data, model_config):
    """Make prediction using loaded model"""
    logger.info(f"Starting prediction with input data keys: {list(input_data.keys())}")
    
    try:
        # Handle health check
        if "operation" in input_data and input_data["operation"] == "health":
            return {
                "status": "healthy",
                "models_loaded": len(model_config.get("models", {})),
                "gpu_available": model_config.get("gpu_available", False),
                "device": model_config.get("device", "cpu")
            }
        
        # Handle basic audio analysis
        if "audio_bytes" in input_data:
            audio_bytes = input_data["audio_bytes"]
            
            try:
                # Convert audio bytes to numpy array
                audio_io = io.BytesIO(audio_bytes)
                audio_data, sample_rate = sf.read(audio_io)
                
                # Simple analysis
                duration = len(audio_data) / sample_rate
                rms = np.sqrt(np.mean(audio_data**2))
                
                result = {
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "rms_energy": float(rms),
                    "audio_length": len(audio_data),
                    "status": "processed"
                }
                
                # Try ASR if Whisper is available
                if model_config.get("models", {}).get("whisper"):
                    try:
                        whisper_model = model_config["models"]["whisper"]
                        audio_io.seek(0)  # Reset stream position
                        
                        segments, info = whisper_model.transcribe(audio_io)
                        transcript = " ".join([segment.text for segment in segments])
                        
                        result["transcript"] = transcript
                        result["language"] = info.language
                        result["asr_available"] = True
                        
                    except Exception as e:
                        logger.warning(f"ASR failed: {e}")
                        result["asr_available"] = False
                        result["asr_error"] = str(e)
                else:
                    result["asr_available"] = False
                
                return result
                
            except Exception as e:
                logger.error(f"Audio processing failed: {e}")
                return {"error": f"Audio processing failed: {e}"}
        
        return {"error": "No valid input data provided"}
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return {"error": f"Prediction failed: {e}"}

def output_fn(prediction, accept_type):
    """Serialize prediction output"""
    logger.info(f"Formatting output for accept type: {accept_type}")
    
    if accept_type == "application/json":
        return json.dumps(prediction), accept_type
    else:
        return json.dumps(prediction), "application/json"
'''
    
    with open(model_dir / "inference.py", "w") as f:
        f.write(inference_code)
    print("[OK] Optimized inference.py created")

def create_lightweight_requirements(model_dir):
    """Create lightweight requirements.txt"""
    
    requirements = """# Core dependencies
torch>=2.0.0
torchaudio>=2.0.0
soundfile>=0.12.0
numpy>=1.21.0

# Audio processing
librosa>=0.10.0
faster-whisper>=1.0.0

# Optional: MusicGen (can be loaded on demand)
# audiocraft>=1.3.0

# Utilities
python-dotenv>=1.0.0
"""
    
    with open(model_dir / "requirements.txt", "w") as f:
        f.write(requirements)
    print("[OK] Lightweight requirements.txt created")

def create_environment_config(model_dir):
    """Create environment.json"""
    
    env_config = {
        "MODEL_SIZE": os.getenv("MODEL_SIZE", "small"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "HF_HOME": "/opt/ml/model/huggingface_cache",
        "TORCH_HOME": "/opt/ml/model/torch_cache",
        "SM_LOG_LEVEL": "INFO"
    }
    
    with open(model_dir / "environment.json", "w") as f:
        json.dump(env_config, f, indent=2)
    print("[OK] environment.json created")

def create_model_tarball(sagemaker_dir):
    """Create compressed model package"""
    
    # Create tar.gz file
    with tarfile.open("sonicmuse-model-optimized.tar.gz", "w:gz") as tar:
        tar.add(sagemaker_dir / "model", arcname=".")
    
    print("[OK] Optimized model package created: sonicmuse-model-optimized.tar.gz")
    print(f"Package size: {os.path.getsize('sonicmuse-model-optimized.tar.gz') / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    create_optimized_package()
