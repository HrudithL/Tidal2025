"""
Prompt generation and mood mapping system
"""
import json
import logging
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

# Preset configurations
PRESET_TABLE = [
    {
        "id": "ambient_calm",
        "when": {"mood": "calm"},
        "style": "Ambient cinematic",
        "instruments": "pads, soft piano, light shaker",
        "texture": "wide, airy, minimal movement",
        "mix_hint": "sidechained lightly to speech"
    },
    {
        "id": "lofi_bright",
        "when": {"mood": "bright"},
        "style": "Lo-fi hip hop",
        "instruments": "soft drums, Rhodes, gentle bass",
        "texture": "warm, cozy",
        "mix_hint": "mono-friendly center"
    },
    {
        "id": "orchestral_tense",
        "when": {"mood": "tense"},
        "style": "Hybrid orchestral",
        "instruments": "low strings, pulses, light percussion",
        "texture": "driving, evolving",
        "mix_hint": "less midrange to avoid masking voice"
    },
    {
        "id": "dark_ambient",
        "when": {"mood": "dark"},
        "style": "Dark ambient",
        "instruments": "deep pads, subtle drones, minimal percussion",
        "texture": "atmospheric, mysterious",
        "mix_hint": "low-end focused, sparse"
    },
    {
        "id": "upbeat_busy",
        "when": {"mood": "busy"},
        "style": "Upbeat electronic",
        "instruments": "synth arps, electronic drums, bass",
        "texture": "energetic, layered",
        "mix_hint": "bright, punchy"
    }
]

def decide_controls(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map audio features to musical controls
    
    Args:
        features: Extracted audio features
        
    Returns:
        Dictionary of musical controls
    """
    try:
        # Extract key metrics
        energy_mean = features["energy_curve"]["mean"]
        energy_std = features["energy_curve"]["std"]
        f0_mean = features["f0_curve"]["mean"]
        f0_std = features["f0_curve"]["std"]
        speech_rate = features["speech_rate_wpm"]
        pause_count = len(features["pause_timestamps"])
        duration = features["duration"]
        
        # Determine mood based on heuristics
        mood = "calm"  # Default
        
        # High energy + high pitch variance -> tense or busy
        if energy_mean > 0.1 and f0_std > 50:
            if speech_rate > 150:
                mood = "busy"
            else:
                mood = "tense"
        
        # High speech rate -> bright or busy
        elif speech_rate > 160:
            mood = "bright"
        
        # Many pauses + low energy -> calm or dark
        elif pause_count > duration / 10 and energy_mean < 0.05:
            if f0_mean < 150:
                mood = "dark"
            else:
                mood = "calm"
        
        # Estimate tempo from speech rate
        tempo_bpm = max(60, min(160, int(speech_rate * 0.6 + 80)))
        
        # Choose key (simplified - could be more sophisticated)
        key = "Cmaj" if mood in ["bright", "busy"] else "Amin"
        
        # Find matching preset
        style_id = None
        for preset in PRESET_TABLE:
            if preset["when"]["mood"] == mood:
                style_id = preset["id"]
                break
        
        if not style_id:
            style_id = "ambient_calm"  # Fallback
        
        return {
            "mood": mood,
            "tempo_bpm": tempo_bpm,
            "key": key,
            "style_id": style_id
        }
        
    except Exception as e:
        logger.error(f"Control decision failed: {e}")
        # Return safe defaults
        return {
            "mood": "calm",
            "tempo_bpm": 120,
            "key": "Cmaj",
            "style_id": "ambient_calm"
        }

def build_prompt(controls: Dict[str, Any]) -> str:
    """
    Build music generation prompt from controls
    
    Args:
        controls: Musical controls
        
    Returns:
        Formatted prompt string
    """
    try:
        # Find preset configuration
        preset = None
        for p in PRESET_TABLE:
            if p["id"] == controls["style_id"]:
                preset = p
                break
        
        if not preset:
            preset = PRESET_TABLE[0]  # Fallback
        
        # Build prompt using template
        prompt = (
            f"{preset['style']}, {controls['mood']}, "
            f"{controls['tempo_bpm']} BPM, key {controls['key']}, "
            f"instrumentation: {preset['instruments']}, "
            f"texture: {preset['texture']}, "
            f"mix: {preset['mix_hint']}"
        )
        
        logger.info(f"Generated prompt: {prompt}")
        return prompt
        
    except Exception as e:
        logger.error(f"Prompt building failed: {e}")
        return "Ambient cinematic, calm, 120 BPM, key C major, pads, soft piano, wide, airy"
