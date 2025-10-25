"""
Approach 3: Smaller Model Sizes - Use smallest possible models
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

# Global variables
_models_loaded = False
_model_config = {}

def model_fn(model_dir):
    """Load smallest possible models"""
    global _models_loaded, _model_config

    if not _models_loaded:
        logger.info(f"Loading smallest models from {model_dir}")
        
        try:
            # Force CPU for smaller memory footprint
            device = "cpu"  # Use CPU for smaller models
            logger.info("Using CPU for smaller model size")
            
            # Use tiny Whisper model
            whisper_model = None
            try:
                from faster_whisper import WhisperModel
                # Use tiny model (smallest possible)
                whisper_model = WhisperModel("tiny", device=device, compute_type="int8")
                logger.info("Loaded Whisper tiny model")
            except Exception as e:
                logger.warning(f"Could not load Whisper: {e}")
            
            _models_loaded = True
            _model_config = {
                "device": device,
                "gpu_available": False,
                "models": {
                    "whisper": "tiny" if whisper_model else None,
                    "musicgen": None  # Skip MusicGen for now
                },
                "mode": "smallest_models",
                "model_sizes": {
                    "whisper": "tiny",
                    "memory_efficient": True
                }
            }
            logger.info("Smallest models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading smallest models: {e}", exc_info=True)
            _model_config = {"error": str(e), "mode": "failed"}
            _models_loaded = True
    
    return _model_config

def input_fn(request_body, request_content_type):
    """Deserialize input request"""
    logger.info(f"Received request with content type: {request_content_type}")
    
    if request_content_type == "application/json":
        try:
            return json.loads(request_body)
        except json.JSONDecodeError as e:
            return {"error": "Invalid JSON"}
    elif request_content_type == "application/octet-stream":
        return {"audio_bytes": request_body}
    else:
        return {"error": f"Unsupported content type: {request_content_type}"}

def predict_fn(input_data, model_config):
    """Handle predictions with smallest models"""
    logger.info(f"Processing with smallest models")
    
    try:
        # Health check
        if "operation" in input_data and input_data["operation"] == "health":
            return {
                "status": "healthy",
                "mode": "smallest_models",
                "whisper_size": config.get("model_sizes", {}).get("whisper", "none"),
                "message": "Using smallest possible models"
            }
        
        # Audio analysis
        if "audio_bytes" in input_data:
            audio_bytes = input_data["audio_bytes"]
            
            try:
                audio_io = io.BytesIO(audio_bytes)
                audio_data, sample_rate = sf.read(audio_io)
                
                # Basic analysis
                duration = len(audio_data) / sample_rate
                rms = np.sqrt(np.mean(audio_data**2))
                
                result = {
                    "duration": float(duration),
                    "sample_rate": int(sample_rate),
                    "rms_energy": float(rms),
                    "status": "processed",
                    "mode": "smallest_models",
                    "whisper_model": model_config.get("models", {}).get("whisper", "none")
                }
                
                # Try ASR with tiny model
                if "tiny" in str(model_config.get("models", {}).get("whisper", "")):
                    try:
                        from faster_whisper import WhisperModel
                        whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
                        
                        audio_io.seek(0)
                        segments, info = whisper.transcribe(audio_io)
                        transcript = " ".join([segment.text for segment in segments])
                        
                        result["transcript"] = transcript
                        result["asr_model"] = "tiny"
                        result["asr_loaded"] = True
                    except Exception as e:
                        logger.warning(f"ASR failed: {e}")
                        result["asr_loaded"] = False
                        result["asr_error"] = str(e)
                
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
