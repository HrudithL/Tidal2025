import React from 'react';
import { MusicControls } from '../types';

interface AnalysisChipsProps {
    controls: MusicControls;
    features?: {
        speech_rate_wpm: number;
        duration: number;
        total_words: number;
    };
}

const AnalysisChips: React.FC<AnalysisChipsProps> = ({ controls, features }) => {
    const getMoodColor = (mood: string) => {
        const colors = {
            bright: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
            calm: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
            tense: 'bg-red-500/20 text-red-300 border-red-500/30',
            dark: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
            busy: 'bg-green-500/20 text-green-300 border-green-500/30',
        };
        return colors[mood as keyof typeof colors] || colors.calm;
    };

    const getMoodIcon = (mood: string) => {
        const icons = {
            bright: '☀️',
            calm: '🌊',
            tense: '⚡',
            dark: '🌙',
            busy: '🔥',
        };
        return icons[mood as keyof typeof icons] || '🎵';
    };

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-100">Analysis Results</h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Mood */}
                <div className={`px-3 py-2 rounded-lg border ${getMoodColor(controls.mood)}`}>
                    <div className="flex items-center space-x-2">
                        <span className="text-lg">{getMoodIcon(controls.mood)}</span>
                        <div>
                            <div className="text-xs opacity-75">Mood</div>
                            <div className="font-medium capitalize">{controls.mood}</div>
                        </div>
                    </div>
                </div>

                {/* Tempo */}
                <div className="px-3 py-2 rounded-lg border bg-gray-700/50 text-gray-300 border-gray-600">
                    <div className="flex items-center space-x-2">
                        <span className="text-lg">🎵</span>
                        <div>
                            <div className="text-xs opacity-75">Tempo</div>
                            <div className="font-medium">{controls.tempo_bpm} BPM</div>
                        </div>
                    </div>
                </div>

                {/* Key */}
                <div className="px-3 py-2 rounded-lg border bg-gray-700/50 text-gray-300 border-gray-600">
                    <div className="flex items-center space-x-2">
                        <span className="text-lg">🎹</span>
                        <div>
                            <div className="text-xs opacity-75">Key</div>
                            <div className="font-medium">{controls.key}</div>
                        </div>
                    </div>
                </div>

                {/* Style */}
                <div className="px-3 py-2 rounded-lg border bg-gray-700/50 text-gray-300 border-gray-600">
                    <div className="flex items-center space-x-2">
                        <span className="text-lg">🎨</span>
                        <div>
                            <div className="text-xs opacity-75">Style</div>
                            <div className="font-medium text-xs">{controls.style_id.replace('_', ' ')}</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Additional Features */}
            {features && (
                <div className="grid grid-cols-3 gap-3 mt-4">
                    <div className="px-3 py-2 rounded-lg border bg-gray-700/50 text-gray-300 border-gray-600">
                        <div className="text-xs opacity-75">Speech Rate</div>
                        <div className="font-medium">{Math.round(features.speech_rate_wpm)} WPM</div>
                    </div>

                    <div className="px-3 py-2 rounded-lg border bg-gray-700/50 text-gray-300 border-gray-600">
                        <div className="text-xs opacity-75">Duration</div>
                        <div className="font-medium">{Math.round(features.duration)}s</div>
                    </div>

                    <div className="px-3 py-2 rounded-lg border bg-gray-700/50 text-gray-300 border-gray-600">
                        <div className="text-xs opacity-75">Words</div>
                        <div className="font-medium">{features.total_words}</div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AnalysisChips;
