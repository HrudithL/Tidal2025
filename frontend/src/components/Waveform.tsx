import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';

interface WaveformProps {
    audioUrl: string;
    onReady?: () => void;
    onPlay?: () => void;
    onPause?: () => void;
    onSeek?: (time: number) => void;
    height?: number;
    color?: string;
    progressColor?: string;
}

const Waveform: React.FC<WaveformProps> = ({
    audioUrl,
    onReady,
    onPlay,
    onPause,
    onSeek,
    height = 100,
    color = '#0ea5e9',
    progressColor = '#0284c7'
}) => {
    const waveformRef = useRef<HTMLDivElement>(null);
    const wavesurferRef = useRef<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [duration, setDuration] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);

    useEffect(() => {
        if (!waveformRef.current) return;

        // Initialize WaveSurfer
        const wavesurfer = WaveSurfer.create({
            container: waveformRef.current,
            waveColor: color,
            progressColor: progressColor,
            height: height,
            normalize: true,
            responsive: true,
            backend: 'WebAudio',
            mediaControls: false,
        });

        wavesurferRef.current = wavesurfer;

        // Event listeners
        wavesurfer.on('ready', () => {
            setDuration(wavesurfer.getDuration());
            onReady?.();
        });

        wavesurfer.on('play', () => {
            setIsPlaying(true);
            onPlay?.();
        });

        wavesurfer.on('pause', () => {
            setIsPlaying(false);
            onPause?.();
        });

        wavesurfer.on('seek', (progress) => {
            const time = wavesurfer.getDuration() * progress;
            setCurrentTime(time);
            onSeek?.(time);
        });

        wavesurfer.on('audioprocess', () => {
            setCurrentTime(wavesurfer.getCurrentTime());
        });

        // Load audio
        wavesurfer.load(audioUrl);

        return () => {
            wavesurfer.destroy();
        };
    }, [audioUrl, height, color, progressColor, onReady, onPlay, onPause, onSeek]);

    const togglePlayPause = () => {
        if (wavesurferRef.current) {
            wavesurferRef.current.playPause();
        }
    };

    const formatTime = (time: number) => {
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    return (
        <div className="space-y-4">
            <div ref={waveformRef} className="w-full" />

            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <button
                        onClick={togglePlayPause}
                        className="flex items-center justify-center w-10 h-10 bg-primary-600 hover:bg-primary-700 text-white rounded-full transition-colors"
                    >
                        {isPlaying ? (
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                            </svg>
                        ) : (
                            <svg className="w-5 h-5 ml-1" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z" />
                            </svg>
                        )}
                    </button>

                    <div className="text-sm text-gray-400">
                        {formatTime(currentTime)} / {formatTime(duration)}
                    </div>
                </div>

                <div className="text-sm text-gray-400">
                    {duration > 0 && `${Math.round(duration)}s`}
                </div>
            </div>
        </div>
    );
};

export default Waveform;
