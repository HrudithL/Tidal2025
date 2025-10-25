"""
Music generation using MusicGen
"""
import io
import logging
from typing import Optional, List
import torch
import numpy as np
from audiocraft.models import MusicGen
import soundfile as sf

logger = logging.getLogger(__name__)

def generate_music(
    musicgen_model: MusicGen,
    prompt: str,
    duration: int = 30,
    seed: int = 42,
    melody_ref: Optional[List[float]] = None,
    tempo_bpm: int = 120,
    key: str = "Cmaj"
) -> bytes:
    """
    Generate background music using MusicGen
    
    Args:
        musicgen_model: Loaded MusicGen model
        prompt: Text prompt for generation
        duration: Duration in seconds
        seed: Random seed for reproducibility
        melody_ref: Optional melody reference (not implemented yet)
        tempo_bpm: Tempo in BPM
        key: Musical key
        
    Returns:
        WAV audio bytes
    """
    try:
        # Set random seed for reproducibility
        torch.manual_seed(seed)
        np.random.seed(seed)
        
        # Set generation parameters
        musicgen_model.set_generation_params(
            duration=duration,
            temperature=1.0,
            top_k=250,
            top_p=0.0,
            cfg_coef=3.0
        )
        
        # Generate music
        logger.info(f"Generating music with prompt: {prompt}")
        
        # MusicGen expects a list of prompts
        wav = musicgen_model.generate([prompt], progress=True)
        
        # Convert to numpy array and ensure proper format
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        
        # Handle batch dimension
        if wav.ndim == 3:
            wav = wav[0]  # Take first (and only) sample
        
        # Ensure stereo output
        if wav.ndim == 1:
            wav = np.stack([wav, wav])  # Mono to stereo
        elif wav.shape[0] == 1:
            wav = np.repeat(wav, 2, axis=0)  # Mono to stereo
        
        # Convert to bytes
        buffer = io.BytesIO()
        sf.write(buffer, wav.T, 32000, format='WAV')  # MusicGen uses 32kHz
        wav_bytes = buffer.getvalue()
        
        logger.info(f"Generated {duration}s of music")
        return wav_bytes
        
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise
