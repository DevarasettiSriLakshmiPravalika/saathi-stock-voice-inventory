import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Phone, User as UserIcon, ShieldCheck, ArrowRight, Loader2, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { authApi } from '../api/auth';
import { useAuth } from '../context/AuthContext';

interface LoginProps {
  initialMode?: 'LOGIN' | 'SIGNUP';
}

export const Login: React.FC<LoginProps> = ({ initialMode }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // Determine initial mode from prop or current URL path
  const defaultMode = initialMode || (location.pathname === '/login' ? 'LOGIN' : 'SIGNUP');
  const [mode, setMode] = useState<'LOGIN' | 'SIGNUP'>(defaultMode);
  const [step, setStep] = useState<'FORM' | 'VERIFY_OTP'>('FORM');

  // Form fields
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('+91');
  const [otp, setOtp] = useState('');
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestSwitch, setSuggestSwitch] = useState<'LOGIN' | 'SIGNUP' | null>(null);

  // Sync mode if pathname changes
  useEffect(() => {
    if (location.pathname === '/login') {
      setMode('LOGIN');
      setError(null);
      setSuggestSwitch(null);
    } else if (location.pathname === '/signup') {
      setMode('SIGNUP');
      setError(null);
      setSuggestSwitch(null);
    }
  }, [location.pathname]);

  const handleTabSwitch = (newMode: 'LOGIN' | 'SIGNUP') => {
    setMode(newMode);
    setError(null);
    setSuggestSwitch(null);
    setStep('FORM');
    if (newMode === 'LOGIN') {
      navigate('/login', { replace: true });
    } else {
      navigate('/signup', { replace: true });
    }
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuggestSwitch(null);

    // E.164 phone validation check
    const phoneTrimmed = phone.trim();
    if (!/^\+[1-9]\d{6,14}$/.test(phoneTrimmed)) {
      setError('Please provide a valid phone number in E.164 format (e.g. +919876543210).');
      return;
    }

    if (mode === 'SIGNUP' && !name.trim()) {
      setError('Please enter your full name to create an account.');
      return;
    }

    setIsLoading(true);
    try {
      if (mode === 'SIGNUP') {
        const res = await authApi.register({
          name: name.trim() || 'Shop Owner',
          phone: phoneTrimmed,
        });

        if (res.success && res.data) {
          if (res.data.dev_otp) {
            setDevOtp(res.data.dev_otp);
            setOtp(res.data.dev_otp); // Pre-fill in dev mode
          }
          setStep('VERIFY_OTP');
        } else {
          setError(res.error?.message || 'Registration failed.');
        }
      } else {
        // LOGIN mode
        const res = await authApi.login({
          phone: phoneTrimmed,
        });

        if (res.success && res.data) {
          if (res.data.dev_otp) {
            setDevOtp(res.data.dev_otp);
            setOtp(res.data.dev_otp); // Pre-fill in dev mode
          }
          setStep('VERIFY_OTP');
        } else {
          setError(res.error?.message || 'Login failed.');
        }
      }
    } catch (err: unknown) {
      const e = err as { response?: { status?: number; data?: { error?: { code?: string; message?: string } } }; message?: string };
      const errCode = e.response?.data?.error?.code;
      const errMsg = e.response?.data?.error?.message || e.message || 'Authentication request failed.';

      if (errCode === 'DUPLICATE_PHONE') {
        setError('This phone number is already registered. Please log in instead.');
        setSuggestSwitch('LOGIN');
      } else if (errCode === 'USER_NOT_FOUND') {
        setError('No account found for this phone number. Please sign up to create your account.');
        setSuggestSwitch('SIGNUP');
      } else {
        setError(errMsg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!otp.trim()) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await authApi.verifyOtp({
        phone: phone.trim(),
        otp: otp.trim(),
      });

      if (res.success && res.data) {
        const userShops = await login(res.data.access_token, res.data.refresh_token, res.data.user);
        if (userShops.length === 0) {
          navigate('/shop-setup');
        } else {
          navigate('/dashboard');
        }
      } else {
        setError(res.error?.message || 'Verification failed.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setError(e.response?.data?.error?.message || e.message || 'Verification failed. Please check the code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-200 p-8 space-y-6">
        {/* Branding */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-indigo-600 text-white font-bold text-2xl flex items-center justify-center mx-auto shadow-sm">
            S
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Saathi</h1>
          <p className="text-sm text-slate-500">Voice-first inventory ledger for retail shops</p>
        </div>

        {/* Mode Selector Tabs (only shown on FORM step) */}
        {step === 'FORM' && (
          <div className="flex border-b border-slate-200">
            <button
              type="button"
              onClick={() => handleTabSwitch('LOGIN')}
              className={`flex-1 pb-3 text-sm font-semibold text-center border-b-2 transition-colors ${
                mode === 'LOGIN'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Log In
            </button>
            <button
              type="button"
              onClick={() => handleTabSwitch('SIGNUP')}
              className={`flex-1 pb-3 text-sm font-semibold text-center border-b-2 transition-colors ${
                mode === 'SIGNUP'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign Up
            </button>
          </div>
        )}

        {error && (
          <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex flex-col space-y-2">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
            {suggestSwitch && (
              <button
                type="button"
                onClick={() => handleTabSwitch(suggestSwitch)}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 text-left underline"
              >
                {suggestSwitch === 'LOGIN' ? 'Click here to Log In' : 'Click here to Sign Up'}
              </button>
            )}
          </div>
        )}

        {/* STEP 1: Phone & Name Input */}
        {step === 'FORM' && (
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                {mode === 'LOGIN' ? 'Welcome Back' : 'Create Your Account'}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {mode === 'LOGIN'
                  ? 'Enter your registered phone number to log in.'
                  : 'Sign up with your phone number to establish your shop ledger.'}
              </p>
            </div>

            {mode === 'SIGNUP' && (
              <div>
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                  Full Name / Owner Name
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <UserIcon className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ramesh Kumar"
                    className="w-full pl-9 pr-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                Phone Number (E.164 format)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Phone className="w-4 h-4" />
                </div>
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+919876543210"
                  className="w-full pl-9 pr-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white font-mono"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Include country code, e.g. +91 for India
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center justify-center space-x-2 shadow-xs transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sending Verification Code...</span>
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            <div className="text-center pt-2">
              {mode === 'LOGIN' ? (
                <p className="text-xs text-slate-500">
                  New to Saathi?{' '}
                  <button
                    type="button"
                    onClick={() => handleTabSwitch('SIGNUP')}
                    className="font-medium text-indigo-600 hover:text-indigo-800 underline"
                  >
                    Create an account (Sign Up)
                  </button>
                </p>
              ) : (
                <p className="text-xs text-slate-500">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => handleTabSwitch('LOGIN')}
                    className="font-medium text-indigo-600 hover:text-indigo-800 underline"
                  >
                    Log In
                  </button>
                </p>
              )}
            </div>
          </form>
        )}

        {/* STEP 2: OTP Verification */}
        {step === 'VERIFY_OTP' && (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold text-slate-900">Verify Phone</h2>
                <button
                  type="button"
                  onClick={() => {
                    setStep('FORM');
                    setError(null);
                  }}
                  className="text-xs text-slate-500 hover:text-slate-800 flex items-center space-x-1"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Change number</span>
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                We sent a 6-digit verification code to{' '}
                <span className="font-semibold text-slate-800 font-mono">{phone}</span>
              </p>
            </div>

            {/* Dev Mode OTP Banner */}
            {devOtp && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 space-y-1">
                <div className="flex items-center space-x-1.5 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Development Mode Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Verification code: <strong className="font-mono">{devOtp}</strong></span>
                  <button
                    type="button"
                    onClick={() => setOtp(devOtp)}
                    className="px-2 py-0.5 bg-emerald-600 text-white rounded text-[11px] hover:bg-emerald-700"
                  >
                    Auto-fill
                  </button>
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                Enter 6-Digit OTP
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.trim())}
                  placeholder="123456"
                  className="w-full pl-9 pr-3.5 py-2.5 text-base tracking-widest font-mono border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white text-center"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !otp.trim()}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center justify-center space-x-2 shadow-xs transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Code...</span>
                </>
              ) : (
                <>
                  <span>Verify & Access Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
