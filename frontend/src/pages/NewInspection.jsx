import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { ArrowLeft, UploadCloud, FileImage, Cpu, Info, Check, AlertCircle } from 'lucide-react';

const commodityOptions = [
  'General Pre-packaged Goods',
  'Food & Beverages',
  'Cosmetics & Toiletries',
  'Electronics & Electrical Appliances',
  'Pharmaceutical & Medical Products',
  'Household Chemicals & Cleaners',
  'Textiles & Apparel Packages'
];

const NewInspection = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [commodityType, setCommodityType] = useState('General Pre-packaged Goods');
  const [inspectionProfile, setInspectionProfile] = useState('Standard PCR Rules 2011');
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const fileInputRef = useRef(null);
  const pollTimerRef = useRef(null);
  const navigate = useNavigate();

  // Cleanup polling timer on component unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setError('File size exceeds maximum limit of 10MB.');
        return;
      }
      setError('');
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.size > 10 * 1024 * 1024) {
        setError('File size exceeds maximum limit of 10MB.');
        return;
      }
      setError('');
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleAnalyze = async () => {
    if (!selectedFile || !(selectedFile instanceof File)) {
      setError('Please upload or select a valid packaged commodity image file first.');
      return;
    }

    setAnalyzing(true);
    setError('');

    try {
      // 1. Create FormData for inspection creation & image upload
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('commodity_type', commodityType);
      formData.append('inspection_profile', inspectionProfile);

      const res = await api.post('/inspections', formData);
      const { inspection_id } = res.data;

      // 2. Trigger async OCR & Compliance Analysis (returns 202 Accepted)
      await api.post(`/inspections/${inspection_id}/analyze`);

      // 3. Poll analysis-status until COMPLETED or FAILED
      const startTime = Date.now();
      const POLLING_INTERVAL_MS = 1500;
      const POLLING_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes timeout

      pollTimerRef.current = setInterval(async () => {
        try {
          if (Date.now() - startTime > POLLING_TIMEOUT_MS) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
            setError('Analysis is taking longer than expected. Please check your Inspection History shortly.');
            setAnalyzing(false);
            return;
          }

          const statusRes = await api.get(`/inspections/${inspection_id}/analysis-status`);
          const { status, error: statusError } = statusRes.data;

          if (status === 'COMPLETED') {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
            navigate(`/inspection/${inspection_id}`);
          } else if (status === 'FAILED') {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
            setError(statusError || 'Analysis failed. Please try uploading a clearer image.');
            setAnalyzing(false);
          }
        } catch (pollErr) {
          console.error('Polling error:', pollErr);
          const pollStatusCode = pollErr.response?.status;
          if (pollStatusCode === 401 || pollStatusCode === 403 || pollStatusCode === 404) {
            clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
            setError(pollErr.response?.data?.detail || 'Unauthorized or inspection not found.');
            setAnalyzing(false);
          }
        }
      }, POLLING_INTERVAL_MS);

    } catch (err) {
      console.error('Analysis trigger error:', err);
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      let errMsg = 'Failed to process inspection image. Please try again.';

      if (detail) {
        errMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      } else if (status === 401) {
        errMsg = 'Session expired or unauthenticated. Please log in again.';
      } else if (status === 403) {
        errMsg = 'Forbidden: You do not have permission for this action.';
      } else if (status === 422) {
        errMsg = 'Unprocessable Entity (HTTP 422): Invalid image payload or parameters.';
      } else if (status === 503) {
        errMsg = 'OCR Engine is initializing on server. Please try again in a few seconds.';
      } else if (status) {
        errMsg = `Server Error (HTTP ${status}): Unable to start analysis.`;
      } else if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errMsg = 'Network Error: Connection failed. Please check backend server status.';
      } else if (err.message) {
        errMsg = err.message;
      }
      setError(errMsg);
      setAnalyzing(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Back Link */}
      <div>
        <Link to="/dashboard" className="text-navy-900 text-xs font-bold hover:underline inline-flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </Link>
      </div>

      {/* Page Title Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">New Inspection</h1>
        <p className="text-xs text-slate-500">Upload a clear image of the packaged commodity for automated compliance analysis.</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Upload Drag & Drop Area */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">Upload Product Image</h2>

          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-slate-300 hover:border-navy-900 bg-slate-50 hover:bg-slate-100/60 transition-all rounded-lg p-8 text-center space-y-3 cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/jpeg,image/jpg,image/png,image/webp"
              className="hidden"
            />

            {previewUrl ? (
              <div className="space-y-3">
                <img src={previewUrl} alt="Product Label Preview" className="max-h-56 mx-auto rounded border border-slate-300 shadow-sm object-contain" />
                <div className="flex items-center justify-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 py-1.5 px-3 rounded border border-emerald-200 max-w-xs mx-auto">
                  <FileImage className="w-4 h-4" />
                  <span className="truncate">{selectedFile.name}</span>
                </div>
                <p className="text-[11px] text-slate-400">Click or drag another image to replace</p>
              </div>
            ) : (
              <>
                <div className="w-12 h-12 bg-navy-900 text-white rounded-full flex items-center justify-center mx-auto shadow-sm">
                  <UploadCloud className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-800">
                    Drag and drop an image file here, or click to browse your computer.
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">Supported formats: JPG, PNG, WEBP (Max 10MB)</p>
                </div>
                <button
                  type="button"
                  className="border border-navy-900 text-navy-900 hover:bg-navy-900 hover:text-white px-4 py-1.5 rounded text-xs font-semibold transition-colors inline-block"
                >
                  Browse Files
                </button>
              </>
            )}
          </div>
        </div>

        {/* Right Column: Analysis Settings */}
        <div className="lg:col-span-5 bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-6 flex flex-col justify-between">
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">Analysis Settings</h2>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Commodity Type</label>
              <select
                value={commodityType}
                onChange={(e) => setCommodityType(e.target.value)}
                className="w-full border border-slate-300 rounded px-3 py-2 text-xs font-medium text-slate-800 bg-white focus:ring-1 focus:ring-navy-900 focus:outline-none"
              >
                {commodityOptions.map((opt, idx) => (
                  <option key={idx} value={opt}>{opt}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Inspection Profile</label>
              <select
                value={inspectionProfile}
                onChange={(e) => setInspectionProfile(e.target.value)}
                className="w-full border border-slate-300 rounded px-3 py-2 text-xs font-medium text-slate-800 bg-white focus:ring-1 focus:ring-navy-900 focus:outline-none"
              >
                <option value="Standard PCR Rules 2011">Standard PCR Rules 2011</option>
                <option value="Food & Edible Oils Protocol">Food & Edible Oils Protocol</option>
                <option value="Cosmetics PCR Schedule III">Cosmetics PCR Schedule III</option>
                <option value="Imported Packaged Commodities">Imported Packaged Commodities</option>
              </select>
            </div>
          </div>

          <div className="space-y-3 pt-4">
            <button
              onClick={handleAnalyze}
              disabled={analyzing || !selectedFile}
              className={`w-full font-bold py-3 rounded text-xs shadow-md transition-all flex items-center justify-center gap-2 ${
                analyzing || !selectedFile
                  ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                  : 'bg-gov-orange hover:bg-orange-600 text-white cursor-pointer'
              }`}
            >
              <Cpu className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Processing OCR & Compliance Engine...' : 'Analyze Product'}</span>
            </button>
            <p className="text-[10px] text-center text-slate-400">Upload an image to enable analysis</p>
          </div>
        </div>
      </div>

      {/* Important Instructions Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-blue-900 flex items-start gap-3 text-xs">
        <div className="p-1 bg-blue-100 rounded text-blue-800 shrink-0">
          <Info className="w-4 h-4" />
        </div>
        <div>
          <p className="font-bold text-blue-950">Important Instructions:</p>
          <p className="text-blue-800 mt-0.5 leading-relaxed">
            Ensure the principal display panel is clearly visible, well-lit, and in focus. Glare or blurriness may affect analysis accuracy.
          </p>
        </div>
      </div>
    </div>
  );
};

export default NewInspection;
