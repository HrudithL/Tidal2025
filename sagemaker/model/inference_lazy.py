"""
Approach 2: Lazy Loading - Load models only when needed
"""
import os
import json
import logging
import torch
import base64
import io
import soundfile as sf
import numpy as np
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('SM_LOG_LEVEL', 'INFO').upper())

# Global variables
_whisper_model = None
_musicgen_model = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def model_fn(model_dir):
    """Initialize lazy loading - don't load models yet"""
    global _whisper_model, _musicgen_model
    
    logger.info(f"Initializing lazy loading from {model_dir}")
    
    # Just set up the environment, don't load models
    return {
        "device": _device,
        "gpu_available": torch.cuda.is_available(),
        "models_loaded": False,
        "mode": "lazy_loading"
    }

def _load_whisper_if_needed():
    """Load Whisper model only when needed"""
    global _whisper_model
    
    if _whisper_model is None:
        logger.info("Lazy loading Whisper model...")
        try:
            from faster_whisper import WhisperModel
            _whisper_model = WhisperModel(
                "small",
                device=_device,
                compute_type="float16" if _device == "cuda" else "int8"
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            return None
    
    return _whisper_model

def _load_musicgen_if_needed():
    """Load MusicGen model only when needed"""
    global _musicgen_model
    
    if _musicgen_model is None:
        logger.info("Lazy loading MusicGen model...")
        try:
            from audiocraft.models import MusicGen
            _musicgen_model = MusicGen.get_pretrained("facebook/musicgen-small")
            _musicgen_model.set_generation_params(duration=30)
            logger.info("MusicGen model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load MusicGen: {e}")
            return None
    
    return _musicgen_model

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
    """Handle predictions with lazy loading"""
    logger.info(f"Processing prediction with lazy loading")
    
    try:
        # Health check - doesn't require models
        if "operation" in input_data and input_data["operation"] == "health":
            return {
                "status": "healthy",
                "mode": "lazy_loading",
                "device": _device,
                "message": "Lazy loading mode - models will load on demand"
            }
        
        # Audio analysis - load Whisper only if needed
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
                    "mode": "lazy_loading"
                }
                
                # Try to load and use Whisper if requested
                if input_data.get("use_asr", False):
                    whisper = _load_whisper_if_needed()
                    if whisper:
                        try:
                            audio_io.seek(0)
                            segments, info = whisper.transcribe(audio_io)
                            transcript = " ".join([segment.text for segment in segments])
                            result["transcript"] = transcript
                            result["asr_loaded"] = True
                        except Exception as e:
                            logger.warning(f"ASR failed: {e}")
                            result["asr_loaded"] = False
                            result["asr_error"] = str(e)
                    else:
                        result["asr_loaded"] = False
                        result["asr_message"] = "Whisper model not available"
                else:
                    result["asr_loaded"] = False
                    result["asr_message"] = "ASR not requested"
                
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
