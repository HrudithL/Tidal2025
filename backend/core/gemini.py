"""
Gemini integration for script analysis
"""
import os
import json
import logging
from typing import List, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)

def analyze_script_with_gemini(
    script: str,
    style: str = "ambient",
    intensity: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Analyze script using Gemini to create mood timeline
    
    Args:
        script: Text script to analyze
        style: Musical style preference
        intensity: Intensity level (0.0 to 1.0)
        
    Returns:
        List of sections with mood, tempo, key, etc.
    """
    try:
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, using fallback analysis")
            return create_fallback_sections(script, style, intensity)
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Create prompt for Gemini
        prompt = f"""
Given this script, split it into up to 4 sections. For each section, provide:
- start_ratio (0.0 to 1.0)
- end_ratio (0.0 to 1.0) 
- mood (one of: bright, calm, tense, dark, busy)
- tempo_bpm (60 to 160)
- key (Cmaj or Amin)
- style_id (ambient_calm, lofi_bright, orchestral_tense, dark_ambient, upbeat_busy)

Script: "{script}"
Style preference: {style}
Intensity: {intensity}

Output JSON only, no other text:
[
  {{
    "start_ratio": 0.0,
    "end_ratio": 0.5,
    "mood": "calm",
    "tempo_bpm": 90,
    "key": "Cmaj",
    "style_id": "ambient_calm"
  }}
]
"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            sections = json.loads(response.text.strip())
            
            # Validate sections
            for section in sections:
                if not all(key in section for key in ["start_ratio", "end_ratio", "mood", "tempo_bpm", "key", "style_id"]):
                    raise ValueError("Invalid section format")
            
            logger.info(f"Gemini analyzed script into {len(sections)} sections")
            return sections
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return create_fallback_sections(script, style, intensity)
        
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return create_fallback_sections(script, style, intensity)

def create_fallback_sections(
    script: str,
    style: str = "ambient",
    intensity: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Create fallback sections when Gemini is unavailable
    
    Args:
        script: Text script
        style: Musical style
        intensity: Intensity level
        
    Returns:
        List of fallback sections
    """
    try:
        # Simple heuristic: split script into 2-3 sections
        words = script.split()
        total_words = len(words)
        
        if total_words < 50:
            # Short script - single section
            sections = [{
                "start_ratio": 0.0,
                "end_ratio": 1.0,
                "mood": "calm" if intensity < 0.5 else "bright",
                "tempo_bpm": int(80 + intensity * 40),
                "key": "Cmaj",
                "style_id": f"{style}_calm"
            }]
        elif total_words < 150:
            # Medium script - two sections
            sections = [
                {
                    "start_ratio": 0.0,
                    "end_ratio": 0.6,
                    "mood": "calm",
                    "tempo_bpm": int(80 + intensity * 30),
                    "key": "Cmaj",
                    "style_id": f"{style}_calm"
                },
                {
                    "start_ratio": 0.6,
                    "end_ratio": 1.0,
                    "mood": "bright" if intensity > 0.5 else "calm",
                    "tempo_bpm": int(100 + intensity * 40),
                    "key": "Cmaj",
                    "style_id": f"{style}_bright"
                }
            ]
        else:
            # Long script - three sections
            sections = [
                {
                    "start_ratio": 0.0,
                    "end_ratio": 0.4,
                    "mood": "calm",
                    "tempo_bpm": int(80 + intensity * 20),
                    "key": "Cmaj",
                    "style_id": f"{style}_calm"
                },
                {
                    "start_ratio": 0.4,
                    "end_ratio": 0.8,
                    "mood": "bright" if intensity > 0.3 else "calm",
                    "tempo_bpm": int(100 + intensity * 30),
                    "key": "Cmaj",
                    "style_id": f"{style}_bright"
                },
                {
                    "start_ratio": 0.8,
                    "end_ratio": 1.0,
                    "mood": "calm",
                    "tempo_bpm": int(90 + intensity * 20),
                    "key": "Cmaj",
                    "style_id": f"{style}_calm"
                }
            ]
        
        logger.info(f"Created {len(sections)} fallback sections")
        return sections
        
    except Exception as e:
        logger.error(f"Fallback section creation failed: {e}")
        # Ultimate fallback
        return [{
            "start_ratio": 0.0,
            "end_ratio": 1.0,
            "mood": "calm",
            "tempo_bpm": 120,
            "key": "Cmaj",
            "style_id": "ambient_calm"
        }]
