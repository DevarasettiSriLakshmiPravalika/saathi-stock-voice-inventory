import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';

// Pages
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Dashboard } from './pages/Dashboard';
import { Inventory } from './pages/Inventory';
import { Statements } from './pages/Statements';
import { StatementDetails } from './pages/StatementDetails';
import { Reviews } from './pages/Reviews';
import { Products } from './pages/Products';
import { Members } from './pages/Members';
import { VoiceEnrollment } from './pages/VoiceEnrollment';
import { Vocabulary } from './pages/Vocabulary';
import { QueryAssistant } from './pages/QueryAssistant';
import { ShopSetup } from './pages/ShopSetup';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication Routes */}
          <Route path="/login" element={<Login initialMode="LOGIN" />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected Application Routes */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/statements" element={<Statements />} />
            <Route path="/statements/:id" element={<StatementDetails />} />
            <Route
              path="/reviews"
              element={
                <ProtectedRoute allowedRoles={['OWNER']}>
                  <Reviews />
                </ProtectedRoute>
              }
            />
            <Route
              path="/products"
              element={
                <ProtectedRoute allowedRoles={['OWNER']}>
                  <Products />
                </ProtectedRoute>
              }
            />
            <Route
              path="/members"
              element={
                <ProtectedRoute allowedRoles={['OWNER']}>
                  <Members />
                </ProtectedRoute>
              }
            />
            <Route path="/voice-enrollment" element={<VoiceEnrollment />} />
            <Route
              path="/vocabulary"
              element={
                <ProtectedRoute allowedRoles={['OWNER']}>
                  <Vocabulary />
                </ProtectedRoute>
              }
            />
            <Route path="/query" element={<QueryAssistant />} />
            <Route path="/shop-setup" element={<ShopSetup />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
