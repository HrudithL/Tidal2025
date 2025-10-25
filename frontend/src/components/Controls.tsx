import React from 'react';

interface ControlsProps {
    duration: number;
    seed: number;
    intensity: number;
    style: string;
    onDurationChange: (duration: number) => void;
    onSeedChange: (seed: number) => void;
    onIntensityChange: (intensity: number) => void;
    onStyleChange: (style: string) => void;
    disabled?: boolean;
}

const Controls: React.FC<ControlsProps> = ({
    duration,
    seed,
    intensity,
    style,
    onDurationChange,
    onSeedChange,
    onIntensityChange,
    onStyleChange,
    disabled = false
}) => {
    const styles = [
        { value: 'ambient', label: 'Ambient' },
        { value: 'lofi', label: 'Lo-fi' },
        { value: 'orchestral', label: 'Orchestral' },
        { value: 'electronic', label: 'Electronic' },
        { value: 'acoustic', label: 'Acoustic' }
    ];

    return (
        <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-100">Generation Controls</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Duration */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">
                        Duration: {duration}s
                    </label>
                    <input
                        type="range"
                        min="10"
                        max="90"
                        step="5"
                        value={duration}
                        onChange={(e) => onDurationChange(parseInt(e.target.value))}
                        disabled={disabled}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                        <span>10s</span>
                        <span>90s</span>
                    </div>
                </div>

                {/* Seed */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">
                        Seed: {seed}
                    </label>
                    <div className="flex space-x-2">
                        <input
                            type="number"
                            min="1"
                            max="999999"
                            value={seed}
                            onChange={(e) => onSeedChange(parseInt(e.target.value))}
                            disabled={disabled}
                            className="flex-1 input-field"
                        />
                        <button
                            onClick={() => onSeedChange(Math.floor(Math.random() * 999999) + 1)}
                            disabled={disabled}
                            className="btn-secondary text-xs px-3"
                        >
                            Random
                        </button>
                    </div>
                </div>

                {/* Intensity */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">
                        Intensity: {Math.round(intensity * 100)}%
                    </label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={intensity}
                        onChange={(e) => onIntensityChange(parseFloat(e.target.value))}
                        disabled={disabled}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                        <span>Calm</span>
                        <span>Intense</span>
                    </div>
                </div>

                {/* Style */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-300">
                        Style
                    </label>
                    <select
                        value={style}
                        onChange={(e) => onStyleChange(e.target.value)}
                        disabled={disabled}
                        className="w-full input-field"
                    >
                        {styles.map(s => (
                            <option key={s.value} value={s.value}>
                                {s.label}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Advanced Controls */}
            <div className="border-t border-gray-700 pt-6">
                <h4 className="text-md font-medium text-gray-300 mb-4">Advanced Settings</h4>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-300">
                            Background Level
                        </label>
                        <select
                            disabled={disabled}
                            className="w-full input-field"
                        >
                            <option value="-18">Quiet (-18dB)</option>
                            <option value="-12">Medium (-12dB)</option>
                            <option value="-6">Loud (-6dB)</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-300">
                            Ducking Amount
                        </label>
                        <select
                            disabled={disabled}
                            className="w-full input-field"
                        >
                            <option value="0.1">Light</option>
                            <option value="0.3">Medium</option>
                            <option value="0.5">Heavy</option>
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-300">
                            Key Signature
                        </label>
                        <select
                            disabled={disabled}
                            className="w-full input-field"
                        >
                            <option value="Cmaj">C Major</option>
                            <option value="Amin">A Minor</option>
                            <option value="Gmaj">G Major</option>
                            <option value="Emin">E Minor</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Controls;
