from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
import io

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SonicMuse API",
    description="AI Background Music Generator",
    version="1.0.0"
)

# CORS middleware
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model storage
models = {}

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    try:
        from core.models import load_models
        global models
        models = load_models()
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        
        return {
            "ok": True,
            "gpu": gpu_available,
            "models": {
                "whisper": "small" if models.get("whisper") else None,
                "musicgen": "small" if models.get("musicgen") else None,
                "crepe": "loaded" if models.get("crepe") else None
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    """Analyze uploaded audio file"""
    try:
        # Validate file type
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=422, detail="File must be audio")
        
        # Read audio data
        audio_data = await file.read()
        
        # Import analysis functions
        from core.asr import transcribe
        from core.features import extract_features
        from core.prompt import decide_controls, build_prompt
        
        # Transcribe audio
        transcript, segments = transcribe(audio_data, models["whisper"])
        
        # Extract features
        features = extract_features(audio_data, segments)
        
        # Decide controls
        controls = decide_controls(features)
        
        # Build prompt
        prompt = build_prompt(controls)
        
        return {
            "transcript": transcript,
            "segments": segments,
            "features": features,
            "controls": controls,
            "prompt": prompt
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_music(
    prompt: str = Form(...),
    duration: int = Form(30),
    seed: int = Form(42),
    melody_ref: Optional[str] = Form(None),
    tempo_bpm: int = Form(120),
    key: str = Form("Cmaj")
):
    """Generate background music"""
    try:
        from core.music import generate_music
        
        # Convert melody_ref if provided
        melody_array = None
        if melody_ref:
            import json
            melody_array = json.loads(melody_ref)
        
        # Generate music
        wav_bytes = generate_music(
            models["musicgen"],
            prompt=prompt,
            duration=duration,
            seed=seed,
            melody_ref=melody_array,
            tempo_bpm=tempo_bpm,
            key=key
        )
        
        return StreamingResponse(
            io.BytesIO(wav_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=background_music.wav"}
        )
        
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mix")
async def mix_audio(
    file_dialogue: UploadFile = File(...),
    file_bg: UploadFile = File(...),
    bg_db: int = Form(-18),
    ducking: float = Form(0.3)
):
    """Mix dialogue with background music"""
    try:
        from core.mix import mix_with_dialogue
        
        # Read audio files
        dialogue_data = await file_dialogue.read()
        bg_data = await file_bg.read()
        
        # Mix audio
        mixed_wav = mix_with_dialogue(
            dialogue_data,
            bg_data,
            bg_db=bg_db,
            ducking=ducking
        )
        
        return StreamingResponse(
            io.BytesIO(mixed_wav),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=mixed_audio.wav"}
        )
        
    except Exception as e:
        logger.error(f"Mixing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compose")
async def compose_music(
    file: UploadFile = File(...),
    duration: int = Form(30),
    seed: int = Form(42),
    intensity: float = Form(0.5)
):
    """One-shot endpoint: analyze -> generate -> mix"""
    try:
        import time
        start_time = time.time()
        
        # Step 1: Analyze
        analyze_start = time.time()
        audio_data = await file.read()
        
        from core.asr import transcribe
        from core.features import extract_features
        from core.prompt import decide_controls, build_prompt
        
        transcript, segments = transcribe(audio_data, models["whisper"])
        features = extract_features(audio_data, segments)
        controls = decide_controls(features)
        prompt = build_prompt(controls)
        
        analyze_time = time.time() - analyze_start
        logger.info(f"Analysis took {analyze_time:.2f}s")
        
        # Step 2: Generate
        generate_start = time.time()
        from core.music import generate_music
        
        wav_bytes = generate_music(
            models["musicgen"],
            prompt=prompt,
            duration=duration,
            seed=seed,
            melody_ref=None,
            tempo_bpm=controls.get("tempo_bpm", 120),
            key=controls.get("key", "Cmaj")
        )
        
        generate_time = time.time() - generate_start
        logger.info(f"Generation took {generate_time:.2f}s")
        
        # Step 3: Mix
        mix_start = time.time()
        from core.mix import mix_with_dialogue
        
        mixed_wav = mix_with_dialogue(
            audio_data,
            wav_bytes,
            bg_db=-18,
            ducking=0.3
        )
        
        mix_time = time.time() - mix_start
        logger.info(f"Mixing took {mix_time:.2f}s")
        
        total_time = time.time() - start_time
        logger.info(f"Total composition took {total_time:.2f}s")
        
        return StreamingResponse(
            io.BytesIO(mixed_wav),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=composed_audio.wav",
                "X-Prompt": prompt,
                "X-Processing-Time": str(total_time)
            }
        )
        
    except Exception as e:
        logger.error(f"Composition failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/script-to-bg")
async def script_to_background(
    script: str = Form(...),
    duration: int = Form(60),
    style: str = Form("ambient"),
    intensity: float = Form(0.5)
):
    """Generate background music from script using Gemini"""
    try:
        from core.gemini import analyze_script_with_gemini
        from core.music import generate_music
        from core.mix import crossfade_sections
        from core.prompt import build_prompt
        
        # Analyze script with Gemini
        sections = analyze_script_with_gemini(script, style, intensity)
        
        # Generate music for each section
        section_audios = []
        for section in sections:
            prompt = build_prompt({
                "mood": section["mood"],
                "tempo_bpm": section["tempo_bpm"],
                "key": section["key"],
                "style_id": f"{style}_{section['mood']}"
            })
            
            section_duration = int(duration * (section["end_ratio"] - section["start_ratio"]))
            wav_bytes = generate_music(
                models["musicgen"],
                prompt=prompt,
                duration=section_duration,
                seed=42,
                melody_ref=None,
                tempo_bpm=section["tempo_bpm"],
                key=section["key"]
            )
            
            section_audios.append(wav_bytes)
        
        # Crossfade sections
        final_wav = crossfade_sections(section_audios)
        
        return StreamingResponse(
            io.BytesIO(final_wav),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=script_background.wav"}
        )
        
    except Exception as e:
        logger.error(f"Script-to-BG failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
