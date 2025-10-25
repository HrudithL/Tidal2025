// TypeScript types for SonicMuse API

export interface AnalyzeResponse {
    transcript: string;
    segments: AudioSegment[];
    features: AudioFeatures;
    controls: MusicControls;
    prompt: string;
}

export interface AudioSegment {
    t0: number;
    t1: number;
    text: string;
}

export interface AudioFeatures {
    energy_curve: {
        time: number[];
        values: number[];
        mean: number;
        std: number;
    };
    f0_curve: {
        time: number[];
        values: number[];
        confidence: number[];
        mean: number;
        std: number;
    };
    speech_rate_wpm: number;
    pause_timestamps: number[];
    duration: number;
    total_words: number;
}

export interface MusicControls {
    mood: 'bright' | 'calm' | 'tense' | 'dark' | 'busy';
    tempo_bpm: number;
    key: string;
    style_id: string;
}

export interface ComposeRequest {
    duration: number;
    seed: number;
    intensity: number;
}

export interface ScriptToBgRequest {
    script: string;
    duration: number;
    style: string;
    intensity: number;
}

export interface HealthResponse {
    ok: boolean;
    gpu: boolean;
    models: {
        whisper: string | null;
        musicgen: string | null;
        crepe: string | null;
    };
}

export interface PresetStyle {
    id: string;
    when: { mood: string };
    style: string;
    instruments: string;
    texture: string;
    mix_hint: string;
}
