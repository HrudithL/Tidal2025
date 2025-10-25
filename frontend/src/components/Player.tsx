import React, { useState, useRef } from 'react';
import Waveform from './Waveform';

interface PlayerProps {
    audioBlob: Blob | null;
    prompt?: string;
    processingTime?: number;
    onDownload?: () => void;
}

const Player: React.FC<PlayerProps> = ({
    audioBlob,
    prompt,
    processingTime,
    onDownload
}) => {
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const downloadRef = useRef<HTMLAnchorElement>(null);

    React.useEffect(() => {
        if (audioBlob) {
            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);

            return () => {
                URL.revokeObjectURL(url);
            };
        }
    }, [audioBlob]);

    const handleDownload = () => {
        if (audioBlob && downloadRef.current) {
            const url = URL.createObjectURL(audioBlob);
            downloadRef.current.href = url;
            downloadRef.current.download = `sonicmuse-composition-${Date.now()}.wav`;
            downloadRef.current.click();
            URL.revokeObjectURL(url);
            onDownload?.();
        }
    };

    if (!audioBlob || !audioUrl) {
        return (
            <div className="card">
                <div className="text-center py-8">
                    <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-300 mb-2">No Audio Generated</h3>
                    <p className="text-gray-500">Upload an audio file and generate background music to see the player here.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-100">Generated Composition</h3>
                    <button
                        onClick={handleDownload}
                        className="btn-primary flex items-center space-x-2"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Download</span>
                    </button>
                </div>

                {/* Waveform Player */}
                <div className="bg-gray-900 rounded-lg p-4">
                    <Waveform
                        audioUrl={audioUrl}
                        height={120}
                        color="#0ea5e9"
                        progressColor="#0284c7"
                    />
                </div>

                {/* Metadata */}
                <div className="space-y-3">
                    {prompt && (
                        <div>
                            <h4 className="text-sm font-medium text-gray-300 mb-2">Generated Prompt</h4>
                            <div className="bg-gray-800 rounded-lg p-3">
                                <p className="text-sm text-gray-400 italic">"{prompt}"</p>
                            </div>
                        </div>
                    )}

                    {processingTime && (
                        <div className="flex items-center justify-between text-sm text-gray-500">
                            <span>Processing Time</span>
                            <span className="font-mono">{processingTime.toFixed(2)}s</span>
                        </div>
                    )}

                    <div className="flex items-center justify-between text-sm text-gray-500">
                        <span>File Size</span>
                        <span className="font-mono">{(audioBlob.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>

                    <div className="flex items-center justify-between text-sm text-gray-500">
                        <span>Format</span>
                        <span className="font-mono">WAV (32kHz)</span>
                    </div>
                </div>

                {/* Hidden download link */}
                <a ref={downloadRef} className="hidden" />
            </div>
        </div>
    );
};

export default Player;
