"""
Audio feature extraction for mood analysis
"""
import io
import logging
from typing import Dict, List, Any
import numpy as np
import librosa
import crepe
from scipy import signal
from scipy.stats import stats

logger = logging.getLogger(__name__)

def extract_features(audio_data: bytes, segments: List[Dict]) -> Dict[str, Any]:
    """
    Extract audio features for mood analysis
    
    Args:
        audio_data: Raw audio bytes
        segments: ASR segments with timestamps
        
    Returns:
        Dictionary of extracted features
    """
    try:
        # Load audio
        audio_array, sr = librosa.load(io.BytesIO(audio_data), sr=16000, mono=True)
        duration = len(audio_array) / sr
        
        # Extract energy curve (RMS)
        hop_length = 512
        frame_length = 2048
        energy_curve = librosa.feature.rms(
            y=audio_array,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # Extract pitch curve using CREPE
        f0_curve, confidence = crepe.predict(
            audio_array,
            sr,
            model_capacity="full",
            viterbi=True,
            step_size=10  # 10ms steps
        )
        
        # Calculate speech rate (words per minute)
        total_words = sum(len(seg["text"].split()) for seg in segments)
        speech_rate_wpm = (total_words / duration) * 60 if duration > 0 else 0
        
        # Detect pauses (gaps between segments)
        pause_timestamps = []
        for i in range(len(segments) - 1):
            gap = segments[i + 1]["t0"] - segments[i]["t1"]
            if gap > 0.5:  # Pauses longer than 500ms
                pause_timestamps.append(segments[i]["t1"])
        
        # Calculate additional features
        energy_mean = np.mean(energy_curve)
        energy_std = np.std(energy_curve)
        f0_mean = np.mean(f0_curve[f0_curve > 0])  # Exclude unvoiced frames
        f0_std = np.std(f0_curve[f0_curve > 0])
        
        # Create time vectors for curves
        time_frames = librosa.frames_to_time(
            np.arange(len(energy_curve)),
            sr=sr,
            hop_length=hop_length
        )
        
        f0_time = np.arange(len(f0_curve)) * 0.01  # 10ms steps
        
        return {
            "energy_curve": {
                "time": time_frames.tolist(),
                "values": energy_curve.tolist(),
                "mean": float(energy_mean),
                "std": float(energy_std)
            },
            "f0_curve": {
                "time": f0_time.tolist(),
                "values": f0_curve.tolist(),
                "confidence": confidence.tolist(),
                "mean": float(f0_mean) if not np.isnan(f0_mean) else 0.0,
                "std": float(f0_std) if not np.isnan(f0_std) else 0.0
            },
            "speech_rate_wpm": float(speech_rate_wpm),
            "pause_timestamps": pause_timestamps,
            "duration": float(duration),
            "total_words": total_words
        }
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise
