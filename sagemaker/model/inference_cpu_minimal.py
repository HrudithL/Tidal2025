"""
Approach 1: CPU-Only Minimal Model (Most likely to succeed)
"""
import os
import json
import logging
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
    """Minimal model loading - CPU only, no heavy AI models"""
    global _models_loaded, _model_config

    if not _models_loaded:
        logger.info(f"Loading minimal CPU-only models from {model_dir}")
        
        try:
            # Only load basic audio processing
            device = "cpu"  # Force CPU-only
            logger.info("Using CPU for all operations")
            
            _models_loaded = True
            _model_config = {
                "device": "cpu",
                "gpu_available": False,
                "models": {
                    "whisper": None,  # Not loaded
                    "musicgen": None,  # Not loaded
                    "cpu_only": True
                },
                "mode": "minimal_cpu"
            }
            logger.info("Minimal CPU model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading minimal model: {e}", exc_info=True)
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
    """Handle predictions with minimal CPU processing"""
    logger.info(f"Processing with minimal CPU mode")
    
    try:
        # Health check
        if "operation" in input_data and input_data["operation"] == "health":
            return {
                "status": "healthy",
                "mode": "minimal_cpu",
                "models_loaded": 0,
                "message": "Minimal CPU mode active - basic audio processing only"
            }
        
        # Basic audio analysis without AI models
        if "audio_bytes" in input_data:
            audio_bytes = input_data["audio_bytes"]
            
            try:
                import io
                audio_io = io.BytesIO(audio_bytes)
                audio_data, sample_rate = sf.read(audio_io)
                
                # Basic audio stats
                duration = len(audio_data) / sample_rate
                rms = np.sqrt(np.mean(audio_data**2))
                peak = np.max(np.abs(audio_data))
                
                result = {
                    "duration": float(duration),
                    "sample_rate": int(sample_rate),
                    "rms_energy": float(rms),
                    "peak_level": float(peak),
                    "audio_length": len(audio_data),
                    "status": "processed",
                    "mode": "minimal_cpu",
                    "note": "No AI models loaded - basic audio analysis only"
                }
                
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
