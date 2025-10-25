"""
Model loading and initialization for SonicMuse
"""
import os
import torch
import logging
from typing import Dict, Any
from faster_whisper import WhisperModel
from audiocraft.models import MusicGen
import crepe

logger = logging.getLogger(__name__)

def load_models() -> Dict[str, Any]:
    """Load all required models"""
    models = {}
    
    # Set device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    try:
        # Load Whisper model
        logger.info("Loading Whisper model...")
        model_size = os.getenv("MODEL_SIZE", "small")
        whisper_model = WhisperModel(
            f"faster-whisper-{model_size}",
            device=device,
            compute_type="float16" if device == "cuda" else "int8"
        )
        models["whisper"] = whisper_model
        logger.info("Whisper model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load Whisper: {e}")
        raise
    
    try:
        # Load MusicGen model
        logger.info("Loading MusicGen model...")
        musicgen_model = MusicGen.get_model("small")
        musicgen_model.set_generation_params(
            duration=30,  # Default duration
            temperature=1.0,
            top_k=250,
            top_p=0.0,
            cfg_coef=3.0
        )
        models["musicgen"] = musicgen_model
        logger.info("MusicGen model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load MusicGen: {e}")
        raise
    
    try:
        # Initialize CREPE (no explicit loading needed)
        logger.info("CREPE initialized")
        models["crepe"] = True
        
    except Exception as e:
        logger.error(f"Failed to initialize CREPE: {e}")
        raise
    
    return models
