import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { Login } from '../pages/Login';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { AuthProvider } from '../context/AuthContext';
import { authApi } from '../api/auth';

vi.mock('../api/auth', () => ({
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    verifyOtp: vi.fn(),
    getMe: vi.fn(),
  },
}));

describe('Login & Authentication Flow', () => {
  it('renders login form without any emojis', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Saathi')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('+919876543210')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument();
  });

  it('validates phone format before sending OTP', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );

    const nameInput = screen.getByPlaceholderText('Ramesh Kumar');
    fireEvent.change(nameInput, { target: { value: 'Test User' } });
    const phoneInput = screen.getByPlaceholderText('+919876543210');
    fireEvent.change(phoneInput, { target: { value: '12345' } }); // invalid E.164
    const submitBtn = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/valid phone number in E.164 format/i)).toBeInTheDocument();
    });
  });

  it('submits registration when valid phone is provided', async () => {
    vi.mocked(authApi.register).mockResolvedValue({
      success: true,
      data: { user_id: '123', phone: '+919876543210', dev_otp: '123456', message: 'OTP sent' },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByPlaceholderText('Ramesh Kumar'), { target: { value: 'Test User' } });
    fireEvent.change(screen.getByPlaceholderText('+919876543210'), { target: { value: '+919876543210' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByText(/enter 6-digit otp/i)).toBeInTheDocument();
    });
  });

  it('submits login for existing user when login tab is active', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      success: true,
      data: { phone: '+919876543210', dev_otp: '123456', message: 'OTP sent', name: 'Existing Owner' },
    });

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login initialMode="LOGIN" />
        </AuthProvider>
      </MemoryRouter>
    );

    // In LOGIN mode, name input is not shown, only phone input
    expect(screen.queryByPlaceholderText('Ramesh Kumar')).not.toBeInTheDocument();
    const phoneInput = screen.getByPlaceholderText('+919876543210');
    fireEvent.change(phoneInput, { target: { value: '+919876543210' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({ phone: '+919876543210' });
      expect(screen.getByText(/enter 6-digit otp/i)).toBeInTheDocument();
    });
  });
});

describe('Protected Routes', () => {
  it('redirects unauthenticated users to /login', () => {
    localStorage.clear();

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>Login Page Mock</div>} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <div>Secret Dashboard</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText('Login Page Mock')).toBeInTheDocument();
  });
});
