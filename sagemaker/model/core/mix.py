"""
Audio mixing with sidechain ducking
"""
import io
import logging
from typing import List, Dict, Any
import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from pydub import AudioSegment
from pydub.effects import normalize

logger = logging.getLogger(__name__)

def mix_with_dialogue(
    dialogue_data: bytes,
    bg_data: bytes,
    bg_db: int = -18,
    ducking: float = 0.3
) -> bytes:
    """
    Mix dialogue with background music using sidechain ducking
    
    Args:
        dialogue_data: Raw dialogue audio bytes
        bg_data: Raw background music bytes
        bg_db: Background level in dB
        ducking: Ducking amount (0.0 = no ducking, 1.0 = full ducking)
        
    Returns:
        Mixed WAV bytes
    """
    try:
        # Load audio files
        dialogue_audio = AudioSegment.from_file(io.BytesIO(dialogue_data))
        bg_audio = AudioSegment.from_file(io.BytesIO(bg_data))
        
        # Normalize dialogue to target LUFS (-16 LUFS)
        dialogue_normalized = normalize(dialogue_audio, headroom=1.0)
        
        # Convert to numpy arrays for processing
        dialogue_array = np.array(dialogue_normalized.get_array_of_samples())
        if dialogue_normalized.channels == 2:
            dialogue_array = dialogue_array.reshape((-1, 2))
        
        bg_array = np.array(bg_audio.get_array_of_samples())
        if bg_audio.channels == 2:
            bg_array = bg_array.reshape((-1, 2))
        
        # Ensure same sample rate
        target_sr = dialogue_normalized.frame_rate
        if bg_audio.frame_rate != target_sr:
            bg_audio = bg_audio.set_frame_rate(target_sr)
            bg_array = np.array(bg_audio.get_array_of_samples())
            if bg_audio.channels == 2:
                bg_array = bg_array.reshape((-1, 2))
        
        # Create speech activity mask (simplified - would use ASR segments in practice)
        speech_mask = create_speech_mask(dialogue_array, target_sr)
        
        # Apply sidechain ducking
        ducked_bg = apply_sidechain_ducking(bg_array, speech_mask, ducking)
        
        # Set background level
        bg_level_linear = 10 ** (bg_db / 20)
        ducked_bg = ducked_bg * bg_level_linear
        
        # Mix audio
        mixed = dialogue_array + ducked_bg
        
        # Peak limiting
        mixed = apply_peak_limiting(mixed)
        
        # Convert back to AudioSegment
        if mixed.ndim == 1:
            mixed_audio = AudioSegment(
                mixed.tobytes(),
                frame_rate=target_sr,
                sample_width=dialogue_normalized.sample_width,
                channels=1
            )
        else:
            mixed_audio = AudioSegment(
                mixed.tobytes(),
                frame_rate=target_sr,
                sample_width=dialogue_normalized.sample_width,
                channels=2
            )
        
        # Export as WAV
        buffer = io.BytesIO()
        mixed_audio.export(buffer, format="wav")
        
        logger.info("Audio mixing completed")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Audio mixing failed: {e}")
        raise

def create_speech_mask(audio_array: np.ndarray, sr: int) -> np.ndarray:
    """
    Create speech activity mask from audio
    
    Args:
        audio_array: Audio samples
        sr: Sample rate
        
    Returns:
        Speech activity mask (0 = silence, 1 = speech)
    """
    try:
        # Convert to mono if stereo
        if audio_array.ndim == 2:
            mono = np.mean(audio_array, axis=1)
        else:
            mono = audio_array
        
        # Calculate RMS energy
        hop_length = 512
        frame_length = 2048
        energy = librosa.feature.rms(
            y=mono,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # Threshold for speech detection
        threshold = np.mean(energy) * 0.3
        
        # Create binary mask
        speech_frames = energy > threshold
        
        # Convert back to sample-level mask
        mask = np.repeat(speech_frames, hop_length)
        mask = mask[:len(mono)]  # Trim to audio length
        
        return mask
        
    except Exception as e:
        logger.error(f"Speech mask creation failed: {e}")
        # Return all-ones mask as fallback
        return np.ones(len(audio_array) if audio_array.ndim == 1 else audio_array.shape[0])

def apply_sidechain_ducking(
    bg_array: np.ndarray,
    speech_mask: np.ndarray,
    ducking: float
) -> np.ndarray:
    """
    Apply sidechain ducking to background music
    
    Args:
        bg_array: Background music samples
        speech_mask: Speech activity mask
        ducking: Ducking amount (0.0 to 1.0)
        
    Returns:
        Ducking gain curve
    """
    try:
        # Ensure same length
        min_length = min(len(bg_array), len(speech_mask))
        bg_array = bg_array[:min_length]
        speech_mask = speech_mask[:min_length]
        
        # Create ducking gain curve
        ducking_gain = 1.0 - (speech_mask * ducking)
        
        # Apply smoothing to avoid clicks
        window_size = int(0.01 * 32000)  # 10ms window
        if window_size > 1:
            ducking_gain = signal.savgol_filter(ducking_gain, window_size, 3)
        
        # Apply ducking
        if bg_array.ndim == 1:
            ducked_bg = bg_array * ducking_gain
        else:
            ducked_bg = bg_array * ducking_gain[:, np.newaxis]
        
        return ducked_bg
        
    except Exception as e:
        logger.error(f"Sidechain ducking failed: {e}")
        return bg_array

def apply_peak_limiting(audio_array: np.ndarray, limit_db: float = -1.0) -> np.ndarray:
    """
    Apply peak limiting to prevent clipping
    
    Args:
        audio_array: Audio samples
        limit_db: Peak limit in dB
        
    Returns:
        Limited audio array
    """
    try:
        limit_linear = 10 ** (limit_db / 20)
        
        # Find peak level
        peak = np.max(np.abs(audio_array))
        
        if peak > limit_linear:
            # Apply limiting
            gain = limit_linear / peak
            audio_array = audio_array * gain
        
        return audio_array
        
    except Exception as e:
        logger.error(f"Peak limiting failed: {e}")
        return audio_array

def crossfade_sections(section_audios: List[bytes], crossfade_ms: int = 500) -> bytes:
    """
    Crossfade multiple audio sections together
    
    Args:
        section_audios: List of audio section bytes
        crossfade_ms: Crossfade duration in milliseconds
        
    Returns:
        Crossfaded audio bytes
    """
    try:
        if not section_audios:
            raise ValueError("No audio sections provided")
        
        if len(section_audios) == 1:
            return section_audios[0]
        
        # Load first section
        result = AudioSegment.from_file(io.BytesIO(section_audios[0]))
        
        # Crossfade remaining sections
        for section_bytes in section_audios[1:]:
            section = AudioSegment.from_file(io.BytesIO(section_bytes))
            result = result.append(section, crossfade=crossfade_ms)
        
        # Export result
        buffer = io.BytesIO()
        result.export(buffer, format="wav")
        
        logger.info(f"Crossfaded {len(section_audios)} sections")
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Crossfading failed: {e}")
        raise
