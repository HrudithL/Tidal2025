"""
Approach 4: CPU-Only Instance Type
Target: ml.m5.xlarge (4 vCPU, 16 GB RAM) or ml.m5.2xlarge (8 vCPU, 32 GB RAM)
"""
import os
import json
import logging
import soundfile as sf
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('SM_LOG_LEVEL', 'INFO').upper())

def model_fn(model_dir):
    """CPU-only model for larger CPU instances"""
    logger.info("Loading CPU-only models for large instance")
    
    return {
        "device": "cpu",
        "gpu_available": False,
        "instance_type": "cpu_large",
        "mode": "cpu_only_large",
        "models": {}
    }

def input_fn(request_body, request_content_type):
    """Deserialize input request"""
    if request_content_type == "application/json":
        return json.loads(request_body)
    elif request_content_type == "application/octet-stream":
        return {"audio_bytes": request_body}
    else:
        return {"error": "Unsupported content type"}

def predict_fn(input_data, model_config):
    """Handle predictions with CPU-only processing"""
    try:
        if "operation" in input_data and input_data["operation"] == "health":
            return {
                "status": "healthy",
                "mode": "cpu_only_large",
                "message": "CPU-only instance running",
                "memory_available": "High (large CPU instance)"
            }
        
        if "audio_bytes" in input_data:
            audio_bytes = input_data["audio_bytes"]
            import io
            
            audio_io = io.BytesIO(audio_bytes)
            audio_data, sample_rate = sf.read(audio_io)
            
            # Comprehensive audio analysis
            duration = len(audio_data) / sample_rate
            rms = np.sqrt(np.mean(audio_data**2))
            peak = np.max(np.abs(audio_data))
            
            # Spectral analysis
            if len(audio_data) > 1024:
                fft = np.fft.fft(audio_data)
                magnitude = np.abs(fft)
                dominant_freq = np.argmax(magnitude[:len(magnitude)//2]) * sample_rate / len(fft)
            else:
                dominant_freq = 0
            
            return {
                "duration": float(duration),
                "sample_rate": int(sample_rate),
                "rms_energy": float(rms),
                "peak_level": float(peak),
                "dominant_frequency": float(dominant_freq),
                "status": "processed",
                "mode": "cpu_only_large",
                "analysis_level": "comprehensive"
            }
        
        return {"error": "No valid input data provided"}
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return {"error": str(e)}

def output_fn(prediction, accept_type):
    """Serialize prediction output"""
    if accept_type == "application/json":
        return json.dumps(prediction), accept_type
    else:
        return json.dumps(prediction), "application/json"
