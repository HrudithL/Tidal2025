import React, { useState, useRef, useCallback } from 'react';

interface UploaderProps {
    onFileSelect: (file: File) => void;
    isLoading: boolean;
    acceptedFormats?: string;
}

const Uploader: React.FC<UploaderProps> = ({
    onFileSelect,
    isLoading,
    acceptedFormats = 'audio/*'
}) => {
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);

        const files = Array.from(e.dataTransfer.files);
        const audioFile = files.find(file => file.type.startsWith('audio/'));

        if (audioFile) {
            onFileSelect(audioFile);
        }
    }, [onFileSelect]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            onFileSelect(file);
        }
    }, [onFileSelect]);

    const handleClick = useCallback(() => {
        fileInputRef.current?.click();
    }, []);

    return (
        <div
            className={`
        relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragOver
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-gray-600 hover:border-gray-500'
                }
        ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleClick}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept={acceptedFormats}
                onChange={handleFileInput}
                className="hidden"
                disabled={isLoading}
            />

            <div className="space-y-4">
                <div className="mx-auto w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center">
                    <svg
                        className="w-8 h-8 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                    </svg>
                </div>

                <div>
                    <h3 className="text-lg font-medium text-gray-100 mb-2">
                        {isLoading ? 'Processing...' : 'Upload Audio File'}
                    </h3>
                    <p className="text-gray-400">
                        Drag and drop an audio file here, or click to browse
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                        Supports MP3, WAV, M4A, and other audio formats
                    </p>
                </div>

                {isLoading && (
                    <div className="flex justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Uploader;
