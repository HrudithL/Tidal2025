"""
Automatic Speech Recognition using Faster-Whisper
"""
import io
import logging
from typing import Tuple, List, Dict
import librosa
import soundfile as sf
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

def transcribe(audio_data: bytes, whisper_model: WhisperModel) -> Tuple[str, List[Dict]]:
    """
    Transcribe audio data and return transcript with segments
    
    Args:
        audio_data: Raw audio bytes
        whisper_model: Loaded Whisper model
        
    Returns:
        Tuple of (transcript, segments)
    """
    try:
        # Convert bytes to audio array
        audio_array, sr = librosa.load(io.BytesIO(audio_data), sr=16000, mono=True)
        
        # Transcribe with timestamps
        segments, info = whisper_model.transcribe(
            audio_array,
            beam_size=5,
            language="en",  # Can be made configurable
            word_timestamps=True
        )
        
        # Extract transcript and segments
        transcript_parts = []
        segments_list = []
        
        for segment in segments:
            transcript_parts.append(segment.text.strip())
            segments_list.append({
                "t0": segment.start,
                "t1": segment.end,
                "text": segment.text.strip()
            })
        
        transcript = " ".join(transcript_parts)
        
        logger.info(f"Transcribed {len(segments_list)} segments")
        return transcript, segments_list
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise
