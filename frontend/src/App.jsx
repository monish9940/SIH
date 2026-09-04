import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';

// Public Page Loaded Immediately
import Home from './pages/Home';

// Lazy-Loaded Non-Home Pages
const MetrologyRules = lazy(() => import('./pages/MetrologyRules'));
const ContactUs = lazy(() => import('./pages/ContactUs'));
const AboutUs = lazy(() => import('./pages/AboutUs'));
const Guidelines = lazy(() => import('./pages/Guidelines'));
const Login = lazy(() => import('./pages/Login'));
const Signup = lazy(() => import('./pages/Signup'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));

// Lazy-Loaded Authenticated Officer Pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const NewInspection = lazy(() => import('./pages/NewInspection'));
const InspectionResult = lazy(() => import('./pages/InspectionResult'));
const InspectionHistory = lazy(() => import('./pages/InspectionHistory'));

const PageLoader = () => (
  <div className="flex justify-center items-center py-24 min-h-[400px]">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-3 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-xs font-semibold text-slate-500">Loading module...</p>
    </div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="flex flex-col min-h-screen bg-slate-50 font-sans text-slate-800 antialiased">
          <Header />
          <Navbar />

          <main className="flex-grow">
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Home />} />
                <Route path="/rules" element={<MetrologyRules />} />
                <Route path="/contact" element={<ContactUs />} />
                <Route path="/about" element={<AboutUs />} />
                <Route path="/guidelines" element={<Guidelines />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />

                {/* Protected Officer Routes */}
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/inspection/new"
                  element={
                    <ProtectedRoute>
                      <NewInspection />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/inspection/:id"
                  element={
                    <ProtectedRoute>
                      <InspectionResult />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/inspection-history"
                  element={
                    <ProtectedRoute>
                      <InspectionHistory />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </Suspense>
          </main>

          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
