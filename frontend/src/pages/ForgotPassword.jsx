import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Mail, ShieldCheck, CheckCircle, AlertCircle, ArrowLeft } from 'lucide-react';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState({ type: '', msg: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: '', msg: '' });
    try {
      await api.post('/auth/forgot-password', { email });
      setStatus({
        type: 'success',
        msg: 'If an institutional account exists for this email address, password reset instructions have been dispatched.'
      });
      setEmail('');
    } catch (err) {
      setStatus({ type: 'error', msg: 'Unable to process request. Please check email address.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-lg shadow-md p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-navy-900 text-white rounded-lg flex items-center justify-center mx-auto shadow-sm">
            <ShieldCheck className="w-7 h-7 text-amber-400" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">Reset Password</h1>
          <p className="text-xs text-slate-500">
            Enter your registered official email address to receive password recovery instructions.
          </p>
        </div>

        {status.msg && (
          <div className={`p-3 rounded text-xs flex items-center gap-2 ${status.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
            {status.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{status.msg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Official Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@gov.in"
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded focus:ring-1 focus:ring-navy-900 focus:outline-none text-slate-800"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-navy-900 hover:bg-slate-800 text-white font-semibold py-2.5 rounded text-xs shadow-sm transition-colors"
          >
            {loading ? 'Processing...' : 'Send Reset Instructions'}
          </button>
        </form>

        <div className="text-center pt-2">
          <Link to="/login" className="text-navy-900 text-xs font-semibold hover:underline inline-flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Institutional Login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
