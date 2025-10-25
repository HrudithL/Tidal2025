// API client for SonicMuse backend
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
    AnalyzeResponse,
    ComposeRequest,
    ScriptToBgRequest,
    HealthResponse,
    MusicControls
} from './types';

class SonicMuseAPI {
    private client: AxiosInstance;

    constructor(baseURL: string = 'http://localhost:8000') {
        this.client = axios.create({
            baseURL,
            timeout: 120000, // 2 minutes for music generation
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Add request interceptor for logging
        this.client.interceptors.request.use(
            (config) => {
                console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
                return config;
            },
            (error) => {
                console.error('API Request Error:', error);
                return Promise.reject(error);
            }
        );

        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => {
                console.log(`API Response: ${response.status} ${response.config.url}`);
                return response;
            },
            (error) => {
                console.error('API Response Error:', error.response?.data || error.message);
                return Promise.reject(error);
            }
        );
    }

    async healthCheck(): Promise<HealthResponse> {
        const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
        return response.data;
    }

    async analyzeAudio(file: File): Promise<AnalyzeResponse> {
        const formData = new FormData();
        formData.append('file', file);

        const response: AxiosResponse<AnalyzeResponse> = await this.client.post(
            '/analyze',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    }

    async generateMusic(
        prompt: string,
        duration: number = 30,
        seed: number = 42,
        tempo_bpm: number = 120,
        key: string = 'Cmaj'
    ): Promise<Blob> {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('duration', duration.toString());
        formData.append('seed', seed.toString());
        formData.append('tempo_bpm', tempo_bpm.toString());
        formData.append('key', key);

        const response = await this.client.post('/generate', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
        });

        return response.data;
    }

    async mixAudio(
        dialogueFile: File,
        bgFile: File,
        bgDb: number = -18,
        ducking: number = 0.3
    ): Promise<Blob> {
        const formData = new FormData();
        formData.append('file_dialogue', dialogueFile);
        formData.append('file_bg', bgFile);
        formData.append('bg_db', bgDb.toString());
        formData.append('ducking', ducking.toString());

        const response = await this.client.post('/mix', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
        });

        return response.data;
    }

    async composeMusic(
        file: File,
        request: ComposeRequest
    ): Promise<{ blob: Blob; prompt: string; processingTime: number }> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('duration', request.duration.toString());
        formData.append('seed', request.seed.toString());
        formData.append('intensity', request.intensity.toString());

        const response = await this.client.post('/compose', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
        });

        const prompt = response.headers['x-prompt'] || 'Unknown';
        const processingTime = parseFloat(response.headers['x-processing-time'] || '0');

        return {
            blob: response.data,
            prompt,
            processingTime,
        };
    }

    async scriptToBackground(request: ScriptToBgRequest): Promise<Blob> {
        const formData = new FormData();
        formData.append('script', request.script);
        formData.append('duration', request.duration.toString());
        formData.append('style', request.style);
        formData.append('intensity', request.intensity.toString());

        const response = await this.client.post('/script-to-bg', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            responseType: 'blob',
        });

        return response.data;
    }
}

// Create singleton instance
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
export const api = new SonicMuseAPI(API_BASE_URL);

export default api;
