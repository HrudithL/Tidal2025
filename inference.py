"""
SageMaker inference script for SonicMuse
"""
import json
import base64
import logging
import os
from typing import Dict, Any
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model storage
models = {}

def model_fn(model_dir: str) -> Dict[str, Any]:
    """
    Load models when SageMaker endpoint starts
    
    Args:
        model_dir: Directory containing model files
        
    Returns:
        Dictionary containing loaded models
    """
    try:
        logger.info(f"Loading models from {model_dir}")
        
        # Import after setting up environment
        from core.models import load_models
        
        global models
        models = load_models()
        
        logger.info("Models loaded successfully")
        return models
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

def input_fn(request_body: bytes, request_content_type: str) -> Dict[str, Any]:
    """
    Parse input data from SageMaker request
    
    Args:
        request_body: Raw request body
        request_content_type: Content type of request
        
    Returns:
        Parsed input data
    """
    try:
        if request_content_type == 'application/json':
            return json.loads(request_body.decode('utf-8'))
        elif request_content_type == 'application/octet-stream':
            # For audio files
            return {"audio_data": request_body}
        else:
            raise ValueError(f"Unsupported content type: {request_content_type}")
            
    except Exception as e:
        logger.error(f"Input parsing failed: {e}")
        raise

def predict_fn(input_data: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run prediction using loaded models
    
    Args:
        input_data: Parsed input data
        model: Loaded models
        
    Returns:
        Prediction results
    """
    try:
        # Import analysis functions
        from core.asr import transcribe
        from core.features import extract_features
        from core.prompt import decide_controls, build_prompt
        from core.music import generate_music
        from core.mix import mix_with_dialogue
        
        # Determine operation type
        operation = input_data.get("operation", "compose")
        
        if operation == "analyze":
            # Audio analysis
            audio_data = input_data["audio_data"]
            transcript, segments = transcribe(audio_data, model["whisper"])
            features = extract_features(audio_data, segments)
            controls = decide_controls(features)
            prompt = build_prompt(controls)
            
            return {
                "transcript": transcript,
                "segments": segments,
                "features": features,
                "controls": controls,
                "prompt": prompt
            }
            
        elif operation == "generate":
            # Music generation
            prompt = input_data["prompt"]
            duration = input_data.get("duration", 30)
            seed = input_data.get("seed", 42)
            tempo_bpm = input_data.get("tempo_bpm", 120)
            key = input_data.get("key", "Cmaj")
            
            wav_bytes = generate_music(
                model["musicgen"],
                prompt=prompt,
                duration=duration,
                seed=seed,
                tempo_bpm=tempo_bpm,
                key=key
            )
            
            return {
                "audio_data": base64.b64encode(wav_bytes).decode('utf-8'),
                "content_type": "audio/wav"
            }
            
        elif operation == "compose":
            # Full composition pipeline
            audio_data = input_data["audio_data"]
            duration = input_data.get("duration", 30)
            seed = input_data.get("seed", 42)
            intensity = input_data.get("intensity", 0.5)
            
            # Analyze
            transcript, segments = transcribe(audio_data, model["whisper"])
            features = extract_features(audio_data, segments)
            controls = decide_controls(features)
            prompt = build_prompt(controls)
            
            # Generate
            wav_bytes = generate_music(
                model["musicgen"],
                prompt=prompt,
                duration=duration,
                seed=seed,
                tempo_bpm=controls.get("tempo_bpm", 120),
                key=controls.get("key", "Cmaj")
            )
            
            # Mix
            mixed_wav = mix_with_dialogue(
                audio_data,
                wav_bytes,
                bg_db=-18,
                ducking=0.3
            )
            
            return {
                "audio_data": base64.b64encode(mixed_wav).decode('utf-8'),
                "prompt": prompt,
                "controls": controls,
                "content_type": "audio/wav"
            }
            
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise

def output_fn(prediction: Dict[str, Any], content_type: str) -> str:
    """
    Format output for SageMaker response
    
    Args:
        prediction: Prediction results
        content_type: Desired output content type
        
    Returns:
        Formatted output string
    """
    try:
        if content_type == 'application/json':
            return json.dumps(prediction)
        else:
            return prediction
            
    except Exception as e:
        logger.error(f"Output formatting failed: {e}")
        raise
