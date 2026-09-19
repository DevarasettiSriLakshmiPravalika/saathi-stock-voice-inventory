import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, Square, Shield, CheckCircle2, AlertCircle, Loader2, Users } from 'lucide-react';
import { voiceApi } from '../api/voice';
import { membersApi } from '../api/members';
import { VoiceProfile, ShopMember } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';

export const VoiceEnrollment: React.FC = () => {
  const { user, currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [members, setMembers] = useState<ShopMember[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [duration, setDuration] = useState(0);
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [enrollSuccess, setEnrollSuccess] = useState<VoiceProfile | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const isOwner = currentRole === 'OWNER';

  const fetchData = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const pRes = await voiceApi.listVoiceProfiles(currentShop.id);
      if (pRes.success && pRes.data) {
        setProfiles(pRes.data);
      }

      if (isOwner) {
        const mRes = await membersApi.listMembers(currentShop.id);
        if (mRes.success && mRes.data) {
          setMembers(mRes.data);
        }
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Failed to load voice enrollment data.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop, isOwner]);

  useEffect(() => {
    fetchData();
    if (user) {
      setSelectedUserId(user.id);
    }
  }, [fetchData, user]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to manage voice profiles."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={Mic}
      />
    );
  }

  const startRecording = async () => {
    setError(null);
    setEnrollSuccess(null);
    chunksRef.current = [];

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Audio recording is not supported in this browser environment.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.start();
      setIsRecording(true);
      setDuration(0);
      timerRef.current = window.setInterval(() => setDuration((d) => d + 1), 1000);
    } catch {
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

  const handleEnroll = async () => {
    if (!currentShop || !audioBlob) return;

    setIsEnrolling(true);
    setError(null);
    setEnrollSuccess(null);

    try {
      const formData = new FormData();
      formData.append('shop_id', currentShop.id);
      if (selectedUserId && selectedUserId !== user?.id) {
        formData.append('member_user_id', selectedUserId);
      }
      formData.append('audio', audioBlob, 'enrollment.webm');

      const res = await voiceApi.enrollVoice(formData);
      if (res.success && res.data) {
        setEnrollSuccess(res.data);
        setAudioBlob(null);
        fetchData();
      } else {
        setError(res.error?.message || 'Voice enrollment failed.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setError(e.response?.data?.error?.message || e.message || 'Voice enrollment failed.');
    } finally {
      setIsEnrolling(false);
    }
  };

  if (!currentShop) {
    return <EmptyState title="No Shop Selected" description="Please choose an active shop." />;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">Voice Profile Enrollment</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Train speaker identification models to recognize authorized shop staff
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {enrollSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-sm flex items-start space-x-2">
          <CheckCircle2 className="w-5 h-5 mt-0.5 shrink-0 text-emerald-600" />
          <div>
            <span className="font-semibold">Voice profile enrolled successfully!</span>
            <p className="text-xs text-emerald-700 mt-0.5">
              Status: {enrollSuccess.enrollment_status} | Quality score:{' '}
              {Math.round(enrollSuccess.quality_score * 100)}% | Model:{' '}
              {enrollSuccess.model_version}
            </p>
          </div>
        </div>
      )}

      {/* Enrollment Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-100">
          <Shield className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-semibold text-slate-900">Record Voice Sample</h2>
        </div>

        {/* Member selection if owner */}
        {isOwner && members.length > 0 && (
          <div>
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
              Select Member to Enroll
            </label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="w-full max-w-md px-3.5 py-2 text-xs border border-slate-300 rounded-lg bg-white"
            >
              <option value={user?.id}>Self ({user?.name || 'Owner'})</option>
              {members
                .filter((m) => m.user_id !== user?.id)
                .map((m) => (
                  <option key={m.id} value={m.user_id}>
                    {m.name || m.user_id} ({m.role})
                  </option>
                ))}
            </select>
          </div>
        )}

        {/* Recording Widget */}
        <div className="flex flex-col items-center justify-center p-8 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
          <button
            type="button"
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isEnrolling}
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
            <p className="text-sm font-medium text-slate-800">
              {isRecording
                ? `Recording speech: ${duration}s`
                : audioBlob
                ? 'Sample recorded ready for enrollment'
                : 'Press to record speaker voice sample'}
            </p>
            <p className="text-xs text-slate-400 mt-1 max-w-md">
              Speak naturally for 3–5 seconds: "This is my voice sample for Saathi inventory management."
            </p>
          </div>

          {audioBlob && (
            <button
              onClick={handleEnroll}
              disabled={isEnrolling}
              className="px-5 py-2 text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg shadow-xs flex items-center space-x-2 transition-colors"
            >
              {isEnrolling && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Submit & Create Voice Profile</span>
            </button>
          )}
        </div>
      </div>

      {/* Existing Enrolled Profiles Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
          <Users className="w-4 h-4 text-indigo-600" />
          <h3 className="text-sm font-semibold text-slate-900">Enrolled Shop Voice Profiles</h3>
        </div>

        {isLoading ? (
          <LoadingSpinner message="Loading enrolled profiles..." />
        ) : profiles.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-400">
            No voice profiles have been enrolled for this shop yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-200 text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="py-2.5">User ID</th>
                  <th className="py-2.5 text-center">Status</th>
                  <th className="py-2.5 text-right">Quality Score</th>
                  <th className="py-2.5 text-right">Model</th>
                  <th className="py-2.5 text-right">Last Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {profiles.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="py-2.5 font-mono text-slate-700">{p.user_id}</td>
                    <td className="py-2.5 text-center">
                      <StatusBadge status={p.enrollment_status} size="sm" />
                    </td>
                    <td className="py-2.5 text-right font-medium text-slate-800">
                      {Math.round(p.quality_score * 100)}%
                    </td>
                    <td className="py-2.5 text-right text-slate-500 font-mono">{p.model_version}</td>
                    <td className="py-2.5 text-right text-slate-400">
                      {new Date(p.updated_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
