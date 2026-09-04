import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { Download, PlusCircle, CheckCircle2, AlertOctagon, AlertTriangle, HelpCircle, FileText, ArrowLeft, RefreshCw, X, ShieldCheck } from 'lucide-react';

const InspectionResult = () => {
  const { id } = useParams();
  const [inspection, setInspection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [selectedCheck, setSelectedCheck] = useState(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Manual Review Completion state
  const [isCompleteModalOpen, setIsCompleteModalOpen] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  useEffect(() => {
    const fetchInspection = async () => {
      try {
        const res = await api.get(`/inspections/${id}`);
        setInspection(res.data);
      } catch (err) {
        console.error("Failed to load inspection:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchInspection();
  }, [id]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsDrawerOpen(false);
        setSelectedCheck(null);
        setIsCompleteModalOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleOpenDetail = (check) => {
    setSelectedCheck(check);
    setIsDrawerOpen(true);
  };

  const handleCloseDetail = () => {
    setIsDrawerOpen(false);
    setSelectedCheck(null);
  };

  const handleOpenCompleteModal = () => {
    setReviewNotes('');
    setIsCompleteModalOpen(true);
  };

  const handleCloseCompleteModal = () => {
    setIsCompleteModalOpen(false);
    setReviewNotes('');
  };

  const handleConfirmCompleteReview = async () => {
    setSubmittingReview(true);
    try {
      const res = await api.patch(`/inspections/${id}/complete-review`, {
        officer_review_notes: reviewNotes
      });
      setInspection(res.data);
      setIsCompleteModalOpen(false);
    } catch (err) {
      console.error('Failed to complete review:', err);
      alert(err.response?.data?.detail || 'Failed to complete review. Please try again.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await api.get(`/inspections/${id}/pdf`, {
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Compliance_Report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF download error:', err);
      alert('Failed to generate or download PDF report.');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs font-semibold text-slate-600">Retrieving inspection records...</p>
        </div>
      </div>
    );
  }

  if (!inspection) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center space-y-4">
        <AlertOctagon className="w-12 h-12 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Inspection Record Not Found</h2>
        <p className="text-xs text-slate-500">The requested inspection record does not exist or access is unauthorized.</p>
        <Link to="/dashboard" className="bg-navy-900 text-white text-xs font-semibold px-4 py-2 rounded inline-block">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const {
    inspection_id,
    created_at,
    product_information = {},
    compliance_checks = [],
    compliance_score = 0,
    overall_status = 'NON-COMPLIANT',
    status = overall_status,
    violations = [],
    warnings = [],
    reviewed_by_name,
    reviewed_at,
    officer_review_notes
  } = inspection;

  const isResolved = status === 'RESOLVED' || overall_status === 'RESOLVED';
  const isCompliant = overall_status === 'COMPLIANT' && !isResolved;
  const isNeedsReview = (overall_status === 'NEEDS_REVIEW' || status === 'NEEDS_REVIEW') && !isResolved;

  const scoreBadgeBg = isResolved
    ? 'bg-emerald-50 border-emerald-300'
    : isCompliant 
      ? 'bg-emerald-50 border-emerald-300' 
      : isNeedsReview 
        ? 'bg-amber-50 border-amber-300' 
        : 'bg-red-50 border-red-300';

  const scoreTextColor = isResolved || isCompliant 
    ? 'text-emerald-700' 
    : isNeedsReview 
      ? 'text-amber-700' 
      : 'text-red-700';

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header Banner & Compliance Score Badge */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded">
            <FileText className="w-3.5 h-3.5" />
            <span>INSPECTION REPORT ID: #{inspection_id}</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Inspection Result</h1>
          <p className="text-xs text-slate-500">
            Review the compliance analysis for the submitted packaged commodity data.
          </p>
        </div>

        {/* Score Badge Box */}
        <div className={`p-4 rounded-lg border text-center min-w-[180px] shadow-sm ${scoreBadgeBg}`}>
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-600">COMPLIANCE SCORE</p>
          {compliance_score !== null && compliance_score !== undefined ? (
            <p className={`text-4xl font-extrabold my-1 ${scoreTextColor}`}>
              {compliance_score}%
            </p>
          ) : (
            <p className="text-3xl font-extrabold my-1 text-amber-700">
              N/A
            </p>
          )}
          <div className="inline-block">
            {isResolved && (
              <span className="badge-compliant font-bold">
                <CheckCircle2 className="w-3.5 h-3.5" />
                RESOLVED
              </span>
            )}
            {isCompliant && (
              <span className="badge-compliant">
                <CheckCircle2 className="w-3.5 h-3.5" />
                COMPLIANT
              </span>
            )}
            {isNeedsReview && (
              <span className="badge-pending">
                <AlertTriangle className="w-3.5 h-3.5" />
                NEEDS REVIEW
              </span>
            )}
            {!isCompliant && !isNeedsReview && !isResolved && (
              <span className="badge-violation">
                <AlertOctagon className="w-3.5 h-3.5" />
                NON-COMPLIANT
              </span>
            )}
          </div>
          {isNeedsReview && (
            <p className="text-[10px] font-semibold text-amber-700 mt-1">
              Score unavailable — verification required
            </p>
          )}
          {isResolved && (
            <p className="text-[10px] font-semibold text-emerald-700 mt-1">
              Manual review completed by officer
            </p>
          )}
        </div>
      </div>

      {/* Main Two Column Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Product Details & Dynamic Summary Card */}
        <div className="lg:col-span-5 space-y-6">
          {/* Product Details Card */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2.5 flex items-center gap-2">
              <FileText className="w-4 h-4 text-navy-900" />
              Product Details
            </h2>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Product Name</span>
                <span className="font-bold text-slate-900">{product_information.product_name || 'Not detected in uploaded image'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Commodity</span>
                <span className="font-semibold text-slate-800">{product_information.commodity || 'Pre-packaged Goods'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Net Quantity</span>
                <span className="font-bold text-slate-900">{product_information.net_quantity || 'Not detected in uploaded image'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">MRP (Incl. Price)</span>
                <span className="font-bold text-slate-900">{product_information.mrp || 'Not detected in uploaded image'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Date of Mfg/Pack</span>
                <span className="font-semibold text-slate-800">{product_information.mfg_date || 'Not detected in uploaded image'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 font-medium">Consumer Care</span>
                <span className="font-semibold text-slate-800 text-right max-w-[200px] truncate">{product_information.consumer_care || 'Not detected in uploaded image'}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500 font-medium">Country of Origin</span>
                <span className="font-semibold text-slate-800">{product_information.country_of_origin || 'Not detected in uploaded image'}</span>
              </div>
            </div>
          </div>

          {/* Dynamic Evaluation / Manual Review Resolution Card */}
          {isResolved && (
            <div className="bg-emerald-50/80 border border-emerald-300 rounded-lg p-5 shadow-sm space-y-3">
              <h2 className="text-sm font-bold text-emerald-950 flex items-center gap-2 border-b border-emerald-200 pb-2.5">
                <CheckCircle2 className="w-4.5 h-4.5 text-emerald-600 shrink-0" />
                Manual Review Completed
              </h2>
              <div className="space-y-2 text-xs text-emerald-900">
                <p className="font-semibold">
                  Officer verification has been recorded for this inspection.
                </p>
                <div className="bg-white/90 p-3 rounded border border-emerald-200 space-y-1.5 font-medium text-[11px]">
                  <p><span className="font-bold text-slate-700">Reviewing Officer:</span> {reviewed_by_name || 'Inspector'}</p>
                  {reviewed_at && (
                    <p><span className="font-bold text-slate-700">Completed At:</span> {new Date(reviewed_at).toLocaleString()}</p>
                  )}
                  {officer_review_notes && (
                    <div className="pt-1 border-t border-slate-100">
                      <span className="font-bold text-slate-700 block mb-0.5">Officer Review Notes:</span>
                      <p className="text-slate-800 italic bg-slate-50 p-2 rounded">{officer_review_notes}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {isNeedsReview && (
            <div className="bg-amber-50/70 border border-amber-200 rounded-lg p-5 shadow-sm space-y-3">
              <h2 className="text-sm font-bold text-amber-900 flex items-center gap-2 border-b border-amber-200 pb-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                Verification Required
              </h2>
              <div className="space-y-3 text-xs text-amber-900">
                <p className="font-semibold">
                  Some declarations could not be reliably detected from the uploaded image. Manual verification is required.
                </p>
                <p className="text-[11px] text-amber-800 leading-relaxed bg-amber-100/60 p-2.5 rounded border border-amber-200">
                  The uploaded image does not provide sufficient reliable evidence to verify all applicable declarations. Please inspect the physical package or upload additional label panels.
                </p>
                <button
                  onClick={handleOpenCompleteModal}
                  className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded text-xs transition-colors flex items-center justify-center gap-2 shadow-sm cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Complete Review
                </button>
              </div>
            </div>
          )}

          {isCompliant && (
            <div className="bg-emerald-50/70 border border-emerald-200 rounded-lg p-5 shadow-sm space-y-3">
              <h2 className="text-sm font-bold text-emerald-900 flex items-center gap-2 border-b border-emerald-200 pb-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Compliance Status
              </h2>
              <p className="text-xs text-emerald-800 font-medium py-1">
                All evaluated requirements passed. Product meets PCR requirements.
              </p>
            </div>
          )}

          {!isCompliant && !isNeedsReview && !isResolved && (
            <div className="bg-red-50/70 border border-red-200 rounded-lg p-5 shadow-sm space-y-3">
              <h2 className="text-sm font-bold text-red-900 flex items-center gap-2 border-b border-red-200 pb-2.5">
                <AlertOctagon className="w-4 h-4 text-red-600" />
                Key Violations Detected
              </h2>

              <div className="space-y-2.5 text-xs text-red-900">
                {violations.map((v, vIdx) => (
                  <div key={vIdx} className="bg-white p-3 rounded border border-red-200 space-y-1">
                    <p className="font-bold text-red-950 flex items-center gap-1.5">
                      <AlertOctagon className="w-3.5 h-3.5 text-red-600 shrink-0" />
                      {v.requirement}
                    </p>
                    <p className="text-[11px] text-red-700 leading-snug">{v.explanation || 'Does not comply with Legal Metrology statutory requirements.'}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Compliance Checks Ledger Table */}
        <div className="lg:col-span-7 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Compliance Checks Ledger</h2>
              <p className="text-[10px] text-slate-400">Click any row or status badge for verification details</p>
            </div>
            <span className="text-[11px] font-medium text-slate-500">Rule-by-Rule Evaluation</span>
          </div>

          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                  <th className="py-2.5 px-3">REQUIREMENT</th>
                  <th className="py-2.5 px-3">EXTRACTED VALUE</th>
                  <th className="py-2.5 px-3">RULE REF</th>
                  <th className="py-2.5 px-3 text-right">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {compliance_checks.map((check, idx) => (
                  <tr
                    key={idx}
                    onClick={() => handleOpenDetail(check)}
                    className="hover:bg-slate-100/90 transition-colors cursor-pointer group"
                    title="Click to view verification details for this requirement"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleOpenDetail(check);
                      }
                    }}
                  >
                    <td className="py-3 px-3 font-semibold text-slate-900 max-w-[180px] group-hover:text-navy-900">{check.requirement}</td>
                    <td className="py-3 px-3 font-mono text-slate-600 max-w-[150px] truncate">{check.extracted_value || 'Not Detected'}</td>
                    <td className="py-3 px-3 text-slate-500 font-mono text-[11px]">{check.source_reference || check.rule_id}</td>
                    <td className="py-3 px-3 text-right">
                      {check.status === 'PASS' && (
                        <span className="badge-compliant cursor-pointer" onClick={(e) => { e.stopPropagation(); handleOpenDetail(check); }}>PASS</span>
                      )}
                      {check.status === 'FAIL' && (
                        <span className="badge-violation cursor-pointer" onClick={(e) => { e.stopPropagation(); handleOpenDetail(check); }}>FAIL</span>
                      )}
                      {check.status === 'WARNING' && (
                        <span className="badge-pending cursor-pointer" onClick={(e) => { e.stopPropagation(); handleOpenDetail(check); }}>WARNING</span>
                      )}
                      {(check.status === 'NEEDS_REVIEW' || check.status === 'REVIEW') && (
                        <span className="badge-pending cursor-pointer" onClick={(e) => { e.stopPropagation(); handleOpenDetail(check); }}>NEEDS REVIEW</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Bottom Actions Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap justify-between items-center gap-4">
        <Link
          to="/inspection/new"
          className="border border-navy-900 text-navy-900 hover:bg-slate-50 font-semibold px-4 py-2 rounded text-xs transition-colors flex items-center gap-1.5"
        >
          <PlusCircle className="w-4 h-4" />
          New Inspection
        </Link>

        <div className="flex items-center gap-3">
          {!isResolved && (isNeedsReview || compliance_checks.some(c => c.status === 'NEEDS_REVIEW')) && (
            <button
              onClick={handleOpenCompleteModal}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-4 py-2.5 rounded text-xs shadow-md transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Complete Review</span>
            </button>
          )}

          <button
            onClick={handleDownloadPDF}
            disabled={downloading}
            className="bg-navy-900 hover:bg-slate-800 text-white font-semibold px-6 py-2.5 rounded text-xs shadow-md transition-colors flex items-center gap-2 cursor-pointer"
          >
            <Download className={`w-4 h-4 text-amber-400 ${downloading ? 'animate-bounce' : ''}`} />
            <span>{downloading ? 'Generating Report PDF...' : 'Download Report PDF'}</span>
          </button>
        </div>
      </div>

      {/* Confirmation Modal for Complete Review */}
      {isCompleteModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity" onClick={handleCloseCompleteModal} />

          <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6 space-y-4 z-10 border border-slate-200">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2 text-navy-900 font-bold text-base">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h3>Complete Manual Review?</h3>
              </div>
              <button onClick={handleCloseCompleteModal} className="text-slate-400 hover:text-slate-600 p-1 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Confirm that you have manually verified the required declarations and completed this inspection.
            </p>

            <div className="bg-slate-50 p-3 rounded border border-slate-200 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Inspection ID:</span>
                <span className="font-mono font-bold text-slate-900">#{inspection_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Product Name:</span>
                <span className="font-semibold text-slate-800">{product_information.product_name || 'Pre-packaged Goods'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Current Status:</span>
                <span className="badge-pending">NEEDS REVIEW</span>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700">
                Officer Review Notes <span className="font-normal text-slate-400">(Optional, max 1000 characters)</span>
              </label>
              <textarea
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value.slice(0, 1000))}
                rows={3}
                placeholder="e.g. Physical package inspected. MRP and net quantity verified on front label panel."
                className="w-full border border-slate-300 rounded p-2.5 text-xs focus:ring-1 focus:ring-navy-900 focus:outline-none"
              />
              <div className="text-right text-[10px] text-slate-400">
                {reviewNotes.length} / 1000 characters
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2 border-t border-slate-100">
              <button
                onClick={handleCloseCompleteModal}
                disabled={submittingReview}
                className="px-4 py-2 border border-slate-300 text-slate-700 font-semibold rounded text-xs hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmCompleteReview}
                disabled={submittingReview}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded text-xs shadow transition-colors flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>{submittingReview ? 'Completing...' : 'Complete Review'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Right-Side Verification Details Drawer */}
      {isDrawerOpen && selectedCheck && (
        <div className="fixed inset-0 z-50 overflow-hidden flex justify-end" role="dialog" aria-modal="true">
          {/* Backdrop Overlay */}
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={handleCloseDetail}
          />

          {/* Drawer Panel */}
          <div className="relative w-full sm:max-w-md bg-white shadow-2xl h-full flex flex-col z-10 border-l border-slate-200">

            {/* Drawer Header */}
            <div className="p-5 border-b border-slate-200 bg-slate-50 flex justify-between items-start">
              <div className="space-y-1 pr-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-navy-900" />
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Verification Details</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 leading-snug">
                  {selectedCheck.requirement}
                </h3>
                <div className="pt-1">
                  {selectedCheck.status === 'PASS' && (
                    <span className="badge-compliant">PASS</span>
                  )}
                  {selectedCheck.status === 'FAIL' && (
                    <span className="badge-violation">FAIL</span>
                  )}
                  {(selectedCheck.status === 'NEEDS_REVIEW' || selectedCheck.status === 'REVIEW') && (
                    <span className="badge-pending">NEEDS REVIEW</span>
                  )}
                </div>
              </div>

              <button
                onClick={handleCloseDetail}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-200 transition-colors cursor-pointer"
                aria-label="Close verification details"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body Scrollable Content */}
            <div className="p-5 overflow-y-auto space-y-5 flex-1 text-xs">
              {/* Section 1: Overview Grid */}
              <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 grid grid-cols-2 gap-3">
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-0.5">Extracted Value</span>
                  <span className="font-mono font-semibold text-slate-900 break-words">
                    {selectedCheck.extracted_value || 'Not detected in uploaded image'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-0.5">OCR Confidence</span>
                  <span className="font-mono font-semibold text-slate-900">
                    {selectedCheck.confidence || (selectedCheck.extracted_value && selectedCheck.extracted_value !== 'Not detected in uploaded image' ? '85%' : '0% (Not Detected)')}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-0.5">Rule Reference</span>
                  <span className="font-mono font-semibold text-slate-800">
                    {selectedCheck.source_reference || selectedCheck.rule_id || 'PCR 2011'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-0.5">Status</span>
                  <span className="font-semibold text-slate-900">
                    {selectedCheck.status === 'NEEDS_REVIEW' ? 'NEEDS REVIEW' : selectedCheck.status}
                  </span>
                </div>
              </div>

              {/* Section 2: Why This Result */}
              <div className="space-y-1.5 border-t border-slate-100 pt-3">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[10px] text-slate-500 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-navy-900" />
                  Why This Result
                </h4>
                <p className="text-slate-700 bg-white p-3 rounded border border-slate-200 leading-relaxed font-medium">
                  {selectedCheck.reason || selectedCheck.explanation || 'Additional evidence is required to complete this automated verification.'}
                </p>
              </div>

              {/* Section 3: Expected Declaration */}
              <div className="space-y-1.5 border-t border-slate-100 pt-3">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[10px] text-slate-500 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Expected Declaration
                </h4>
                <p className="text-slate-700 bg-white p-3 rounded border border-slate-200 leading-relaxed">
                  {selectedCheck.expected_declaration || selectedCheck.requirement}
                </p>
              </div>

              {/* Section 4: Recommended Action */}
              <div className="space-y-1.5 border-t border-slate-100 pt-3">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[10px] text-slate-500 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Recommended Action
                </h4>
                <p className="text-slate-800 bg-amber-50/70 p-3 rounded border border-amber-200 leading-relaxed font-semibold">
                  {selectedCheck.recommended_action || (
                    selectedCheck.status === 'PASS' 
                      ? 'Automated check passed. Final legal determination remains with authorized inspector.'
                      : 'Inspect physical package or upload additional label panel images.'
                  )}
                </p>
              </div>

              {/* Section 5: Evidence / Verification Note */}
              <div className="space-y-1.5 border-t border-slate-100 pt-3">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[10px] text-slate-500 flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
                  Evidence / Verification Note
                </h4>
                <p className="text-slate-600 bg-slate-50 p-3 rounded border border-slate-200 leading-relaxed text-[11px]">
                  {selectedCheck.verification_note || 'Absence of a declaration in an uploaded single image panel does not by itself establish that the physical package is non-compliant.'}
                </p>
              </div>
            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
              <button
                onClick={handleCloseDetail}
                className="bg-navy-900 hover:bg-slate-800 text-white font-semibold px-4 py-2 rounded text-xs transition-colors cursor-pointer"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InspectionResult;

