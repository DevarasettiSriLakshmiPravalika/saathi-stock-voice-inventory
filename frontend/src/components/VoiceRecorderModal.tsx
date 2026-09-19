import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Loader2, CheckCircle2, AlertCircle, X, Volume2, ArrowRight } from 'lucide-react';
import { voiceApi, VoiceProcessResult } from '../api/voice';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from './StatusBadge';

interface VoiceRecorderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const VoiceRecorderModal: React.FC<VoiceRecorderModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { currentShop } = useAuth();
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [textOverride, setTextOverride] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VoiceProcessResult | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isOpen) {
      resetState();
    }
  }, [isOpen]);

  const resetState = () => {
    setIsRecording(false);
    setAudioBlob(null);
    setRecordingDuration(0);
    setTextOverride('');
    setIsProcessing(false);
    setError(null);
    setResult(null);
    audioChunksRef.current = [];
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const startRecording = async () => {
    setError(null);
    setResult(null);
    audioChunksRef.current = [];

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Audio recording is not supported in this browser environment.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      timerRef.current = window.setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError('Microphone access was denied or audio device is unavailable.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const handleProcess = async () => {
    if (!currentShop) {
      setError('Please select a shop before submitting voice data.');
      return;
    }

    if (!audioBlob && !textOverride.trim()) {
      setError('Please record audio or enter a statement text.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('shop_id', currentShop.id);
      formData.append('source', 'MOBILE_WEB');

      if (audioBlob) {
        formData.append('audio', audioBlob, 'statement.webm');
      }
      if (textOverride.trim()) {
        formData.append('transcript_override', textOverride.trim());
      }

      const response = await voiceApi.processVoice(formData);
      if (response.success && response.data) {
        setResult(response.data);
        if (onSuccess) {
          onSuccess();
        }
      } else {
        setError(response.error?.message || 'Processing failed.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setError(e.response?.data?.error?.message || e.message || 'An error occurred during voice processing.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Volume2 className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900">Voice Inventory Capture</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {error && (
            <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600" />
              <div>{error}</div>
            </div>
          )}

          {!result ? (
            <>
              {/* Recording Controls */}
              <div className="flex flex-col items-center justify-center p-6 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isProcessing}
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-all shadow-md ${
                    isRecording
                      ? 'bg-rose-600 text-white hover:bg-rose-700 animate-pulse'
                      : audioBlob
                      ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                      : 'bg-indigo-600 text-white hover:bg-indigo-700'
                  }`}
                >
                  {isRecording ? <Square className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                </button>

                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700">
                    {isRecording
                      ? `Recording: ${recordingDuration}s`
                      : audioBlob
                      ? 'Audio sample recorded'
                      : 'Tap microphone to speak'}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Example: "Sold 5 bags of rice" or "Received 20 boxes of oil"
                  </p>
                </div>
              </div>

              {/* Text override / fallback */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  Text Input / Transcript Override
                </label>
                <input
                  type="text"
                  placeholder="Or type directly: e.g. Sold 10 bags of rice"
                  value={textOverride}
                  onChange={(e) => setTextOverride(e.target.value)}
                  disabled={isProcessing || isRecording}
                  className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isProcessing}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleProcess}
                  disabled={isProcessing || isRecording || (!audioBlob && !textOverride.trim())}
                  className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-xs flex items-center space-x-2 transition-colors"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <span>Process Statement</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </>
          ) : (
            /* Result Screen */
            <div className="space-y-4">
              <div
                className={`p-4 rounded-xl border flex items-start space-x-3 ${
                  result.status === 'CONFIRMED'
                    ? 'bg-emerald-50 border-emerald-200'
                    : result.status === 'FLAGGED'
                    ? 'bg-amber-50 border-amber-200'
                    : 'bg-rose-50 border-rose-200'
                }`}
              >
                {result.status === 'CONFIRMED' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
                )}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-sm text-slate-900">
                      Decision: {result.decision}
                    </span>
                    <StatusBadge status={result.status} size="sm" />
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{result.explanation}</p>
                </div>
              </div>

              {/* Structured Claim Grid */}
              <div className="grid grid-cols-2 gap-3 text-sm bg-slate-50 p-4 rounded-xl border border-slate-200">
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Transcript</span>
                  <span className="font-medium text-slate-800">{result.transcript || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Speaker Status</span>
                  <span className="font-medium text-slate-800">
                    {result.speaker_status} ({Math.round(result.speaker_confidence * 100)}%)
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Movement</span>
                  <span className="font-medium text-slate-800">
                    {result.quantity !== null ? `${result.quantity} ${result.unit || ''}` : 'Unresolved'}{' '}
                    {result.direction ? `(${result.direction})` : ''}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Inventory Impact</span>
                  <span
                    className={`font-semibold ${
                      result.status === 'CONFIRMED' ? 'text-emerald-700' : 'text-slate-500'
                    }`}
                  >
                    {result.status === 'CONFIRMED'
                      ? 'Stock Updated'
                      : 'Inventory Unchanged'}
                  </span>
                </div>
              </div>

              {result.status === 'FLAGGED' && (
                <p className="text-xs text-amber-700 bg-amber-50 p-3 rounded-lg border border-amber-200">
                  This statement has been routed to the owner review queue for verification.
                </p>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={resetState}
                  className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Record Another
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
