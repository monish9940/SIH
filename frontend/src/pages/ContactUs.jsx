import React, { useState } from 'react';
import api from '../services/api';
import { Phone, Mail, MessageSquare, Clock, Send, CheckCircle, AlertCircle } from 'lucide-react';

const ContactUs = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: ''
  });
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: '', msg: '' });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: '', msg: '' });
    try {
      await api.post('/contact', formData);
      setStatus({ type: 'success', msg: 'Your support ticket has been submitted successfully! Ticket ID generated.' });
      setFormData({ name: '', email: '', phone: '', subject: '', message: '' });
      setTimeout(() => setShowModal(false), 2000);
    } catch (err) {
      setStatus({ type: 'error', msg: err.response?.data?.detail || 'Failed to submit contact request.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Title Header */}
      <div className="text-center space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-600">CONSUMER SUPPORT</p>
        <h1 className="text-3xl font-extrabold text-slate-900">Contact Us</h1>
        <p className="text-xs text-slate-500 max-w-xl mx-auto">
          Need assistance with product compliance, an inspection, or a consumer grievance? Our support channels are here to help.
        </p>
      </div>

      {/* National Consumer Helpline Hero Box */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          <div className="md:col-span-7 space-y-3 border-b md:border-b-0 md:border-r border-slate-200 pb-6 md:pb-0 md:pr-6">
            <span className="bg-amber-100 text-amber-900 border border-amber-300 text-[10px] font-bold px-2.5 py-0.5 rounded uppercase">
              Official Consumer Support
            </span>
            <h2 className="text-xl font-bold text-slate-900">National Consumer Helpline</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              For consumer complaints, queries, and grievance assistance, you can contact the National Consumer Helpline of the Department of Consumer Affairs.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <a href="tel:1915" className="bg-navy-900 hover:bg-slate-800 text-white font-bold text-sm px-4 py-2 rounded inline-flex items-center gap-2 shadow-sm">
                <Phone className="w-4 h-4 text-amber-400" />
                1915
              </a>
              <a href="tel:1800114000" className="border border-navy-900 text-navy-900 hover:bg-slate-50 font-bold text-sm px-4 py-2 rounded inline-flex items-center gap-2">
                <Phone className="w-4 h-4 text-navy-900" />
                1800-11-4000
              </a>
            </div>
          </div>

          <div className="md:col-span-5 space-y-3 text-xs text-slate-700">
            <div className="flex items-start gap-3">
              <Phone className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-900">Toll-Free Helpline</p>
                <p className="text-slate-500">1915 / 1800-11-4000</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Mail className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-900">Email</p>
                <p className="text-slate-500">nch-ca@gov.in</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MessageSquare className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-900">SMS Support</p>
                <p className="text-slate-500">8800001915</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Clock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-slate-900">Working Hours</p>
                <p className="text-slate-500">8:00 AM - 8:00 PM (except national holidays)</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Two Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900">Get In Touch</h3>
          <p className="text-xs text-slate-500">
            Contact the Compliance Checker support team or access state-level Legal Metrology department directories.
          </p>
          <button
            onClick={() => alert("Department Contacts Directory:\n\nHeadquarters: Ministry of Consumer Affairs, Krishi Bhawan, New Delhi\nLegal Metrology Controller: controller-lm@gov.in\nPhone: 011-23386123")}
            className="w-full border border-navy-900 text-navy-900 hover:bg-slate-50 font-semibold py-2 rounded text-xs transition-colors"
          >
            View Department Contacts
          </button>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900">Send Us a Message</h3>
          <p className="text-xs text-slate-500">
            Submit your query or report a technical issue directly to our dedicated support desk.
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="w-full bg-navy-900 hover:bg-slate-800 text-white font-semibold py-2 rounded text-xs transition-colors shadow-sm"
          >
            Open Support Ticket
          </button>
        </div>
      </div>

      {/* Support Ticket Modal Form */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-slate-200 rounded-lg max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-900">Open Support Ticket</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 font-bold text-lg">×</button>
            </div>

            {status.msg && (
              <div className={`p-3 rounded text-xs flex items-center gap-2 ${status.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
                {status.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                <span>{status.msg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="Officer / Citizen Name"
                  className="w-full border border-slate-300 rounded px-3 py-1.5 focus:ring-1 focus:ring-navy-900 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Email Address</label>
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="email@example.com"
                    className="w-full border border-slate-300 rounded px-3 py-1.5 focus:ring-1 focus:ring-navy-900 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Mobile Number</label>
                  <input
                    type="tel"
                    name="phone"
                    required
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+91 9876543210"
                    className="w-full border border-slate-300 rounded px-3 py-1.5 focus:ring-1 focus:ring-navy-900 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Subject</label>
                <input
                  type="text"
                  name="subject"
                  required
                  value={formData.subject}
                  onChange={handleChange}
                  placeholder="Inquiry / Issue Subject"
                  className="w-full border border-slate-300 rounded px-3 py-1.5 focus:ring-1 focus:ring-navy-900 focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Message Detail</label>
                <textarea
                  name="message"
                  required
                  rows="4"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Describe your query or reported issue..."
                  className="w-full border border-slate-300 rounded px-3 py-1.5 focus:ring-1 focus:ring-navy-900 focus:outline-none"
                ></textarea>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 bg-navy-900 hover:bg-slate-800 text-white font-semibold rounded shadow-sm flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  {loading ? 'Submitting...' : 'Submit Ticket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContactUs;
