import React, { useState, useCallback } from 'react';
import Uploader from './components/Uploader';
import AnalysisChips from './components/AnalysisChips';
import EmotionArc from './components/EmotionArc';
import Controls from './components/Controls';
import Player from './components/Player';
import api from './api';
import { AnalyzeResponse, ComposeRequest, ScriptToBgRequest } from './types';

type TabType = 'audio' | 'script';

const App: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<TabType>('audio');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Audio mode state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);
  const [composedAudio, setComposedAudio] = useState<Blob | null>(null);
  const [composePrompt, setComposePrompt] = useState<string>('');
  const [processingTime, setProcessingTime] = useState<number>(0);

  // Controls state
  const [duration, setDuration] = useState(30);
  const [seed, setSeed] = useState(42);
  const [intensity, setIntensity] = useState(0.5);
  const [style, setStyle] = useState('ambient');

  // Script mode state
  const [script, setScript] = useState('');
  const [scriptAudio, setScriptAudio] = useState<Blob | null>(null);

  // Error handling
  const showError = useCallback((message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  }, []);

  // Audio mode handlers
  const handleFileSelect = useCallback(async (file: File) => {
    try {
      setUploadedFile(file);
      setIsLoading(true);
      setError(null);

      const result = await api.analyzeAudio(file);
      setAnalysisResult(result);
    } catch (err) {
      showError('Failed to analyze audio file. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [showError]);

  const handleCompose = useCallback(async () => {
    if (!uploadedFile) return;

    try {
      setIsLoading(true);
      setError(null);

      const request: ComposeRequest = {
        duration,
        seed,
        intensity
      };

      const result = await api.composeMusic(uploadedFile, request);
      setComposedAudio(result.blob);
      setComposePrompt(result.prompt);
      setProcessingTime(result.processingTime);
    } catch (err) {
      showError('Failed to generate composition. Please try again.');
      console.error('Composition error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [uploadedFile, duration, seed, intensity, showError]);

  // Script mode handlers
  const handleScriptGenerate = useCallback(async () => {
    if (!script.trim()) return;

    try {
      setIsLoading(true);
      setError(null);

      const request: ScriptToBgRequest = {
        script: script.trim(),
        duration: 60,
        style,
        intensity
      };

      const result = await api.scriptToBackground(request);
      setScriptAudio(result);
    } catch (err) {
      showError('Failed to generate background music from script. Please try again.');
      console.error('Script generation error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [script, style, intensity, showError]);

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-white">SonicMuse</h1>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-400">
                AI Background Music Generator
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Toast */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-300">{error}</span>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg w-fit">
            <button
              onClick={() => setActiveTab('audio')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'audio' ? 'tab-active' : 'tab-inactive'
                }`}
            >
              Audio Mode
            </button>
            <button
              onClick={() => setActiveTab('script')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'script' ? 'tab-active' : 'tab-inactive'
                }`}
            >
              Script Mode
            </button>
          </div>
        </div>

        {/* Audio Mode */}
        {activeTab === 'audio' && (
          <div className="space-y-8">
            {/* Upload Section */}
            <div className="card">
              <Uploader
                onFileSelect={handleFileSelect}
                isLoading={isLoading}
              />
            </div>

            {/* Analysis Results */}
            {analysisResult && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="card">
                  <AnalysisChips
                    controls={analysisResult.controls}
                    features={{
                      speech_rate_wpm: analysisResult.features.speech_rate_wpm,
                      duration: analysisResult.features.duration,
                      total_words: analysisResult.features.total_words
                    }}
                  />
                </div>

                <div className="card">
                  <EmotionArc features={analysisResult.features} />
                </div>
              </div>
            )}

            {/* Controls */}
            {analysisResult && (
              <div className="card">
                <Controls
                  duration={duration}
                  seed={seed}
                  intensity={intensity}
                  style={style}
                  onDurationChange={setDuration}
                  onSeedChange={setSeed}
                  onIntensityChange={setIntensity}
                  onStyleChange={setStyle}
                  disabled={isLoading}
                />

                <div className="mt-6 pt-6 border-t border-gray-700">
                  <button
                    onClick={handleCompose}
                    disabled={isLoading}
                    className="btn-primary w-full py-3 text-lg"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-2">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Generating...</span>
                      </div>
                    ) : (
                      'Generate Background Music'
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Player */}
            {composedAudio && (
              <Player
                audioBlob={composedAudio}
                prompt={composePrompt}
                processingTime={processingTime}
              />
            )}
      </div>
        )}

        {/* Script Mode */}
        {activeTab === 'script' && (
          <div className="space-y-8">
            {/* Script Input */}
      <div className="card">
              <h3 className="text-lg font-semibold text-gray-100 mb-4">Script Input</h3>
              <textarea
                value={script}
                onChange={(e) => setScript(e.target.value)}
                placeholder="Enter your script here... The AI will analyze the text and generate appropriate background music for different sections."
                className="w-full h-48 input-field resize-none"
                disabled={isLoading}
              />
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  {script.length} characters
                </div>
                <button
                  onClick={handleScriptGenerate}
                  disabled={!script.trim() || isLoading}
                  className="btn-primary"
                >
                  {isLoading ? 'Generating...' : 'Generate Background Music'}
        </button>
              </div>
            </div>

            {/* Script Controls */}
            <div className="card">
              <Controls
                duration={60}
                seed={seed}
                intensity={intensity}
                style={style}
                onDurationChange={() => { }} // Fixed for script mode
                onSeedChange={setSeed}
                onIntensityChange={setIntensity}
                onStyleChange={setStyle}
                disabled={isLoading}
              />
            </div>

            {/* Script Player */}
            {scriptAudio && (
              <Player
                audioBlob={scriptAudio}
                prompt="Generated from script analysis"
              />
            )}
      </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-400">
            <p>SonicMuse - AI Background Music Generator</p>
            <p className="text-sm mt-2">Powered by Whisper, MusicGen, and Gemini AI</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;