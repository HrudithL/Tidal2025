"""
Optimized SageMaker inference script with lightweight model loading
"""
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
    """
    Load the SageMaker model with optimized loading strategy.
    This function is called once when the endpoint starts.
    """
    global _models_loaded, _model_config

    if not _models_loaded:
        logger.info(f"Loading models from {model_dir}")
        
        # Load environment variables from environment.json
        env_path = os.path.join(model_dir, "environment.json")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_vars = json.load(f)
                for key, value in env_vars.items():
                    os.environ[key] = str(value)
            logger.info("Loaded environment variables from environment.json")

        model_size = os.getenv("MODEL_SIZE", "small")
        
        try:
            # Optimized model loading - start with minimal models
            logger.info("Starting optimized model loading...")
            
            # Check GPU availability
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            # Load only essential models for basic functionality
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
            
            # Load CREPE for pitch detection (optional)
            try:
                import crepe
                models['crepe'] = True
                logger.info("CREPE model available")
            except Exception as e:
                logger.warning(f"CREPE not available: {e}")
                models['crepe'] = False
            
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
            # Return minimal config even if models fail
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
    """
    Deserialize and pre-process the input request.
    """
    logger.info(f"Received request with content type: {request_content_type}")
    
    if request_content_type == "application/json":
        try:
            return json.loads(request_body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {"error": "Invalid JSON"}
    
    elif request_content_type == "application/octet-stream":
        # Handle raw audio bytes
        return {"audio_bytes": request_body}
    
    else:
        logger.error(f"Unsupported content type: {request_content_type}")
        return {"error": f"Unsupported content type: {request_content_type}"}

def predict_fn(input_data, model_config):
    """
    Make a prediction using the loaded model.
    """
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
            
            # Basic audio processing
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
                        from faster_whisper import WhisperModel
                        whisper_model = model_config["models"]["whisper"]
                        
                        # Simple transcription
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
        
        # Handle script analysis
        if "script" in input_data:
            script = input_data["script"]
            return {
                "script_length": len(script),
                "word_count": len(script.split()),
                "status": "script_received",
                "message": "Script analysis not yet implemented"
            }
        
        return {"error": "No valid input data provided"}
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return {"error": f"Prediction failed: {e}"}

def output_fn(prediction, accept_type):
    """
    Serialize and post-process the prediction output.
    """
    logger.info(f"Formatting output for accept type: {accept_type}")
    
    if accept_type == "application/json":
        return json.dumps(prediction), accept_type
    else:
        return json.dumps(prediction), "application/json"
