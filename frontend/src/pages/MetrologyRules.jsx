import React from 'react';
import { BookOpen, AlertTriangle, Scan, Search, ShieldCheck, FileCheck, CheckCircle2, Cpu, Zap, FileSpreadsheet } from 'lucide-react';

const MetrologyRules = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Page Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-navy-900 border border-blue-200 text-xs font-semibold px-3 py-1 rounded-full">
          <BookOpen className="w-3.5 h-3.5" />
          <span>LEGAL METROLOGY FRAMEWORK</span>
        </div>

        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
          Legal Metrology (Packaged Commodities) Rules, 2011
        </h1>

        <p className="text-slate-600 text-sm leading-relaxed max-w-4xl">
          The Legal Metrology (Packaged Commodities) Rules, 2011 prescribe requirements relating to pre-packaged commodities, including declarations and information that must be provided to consumers. These rules form the regulatory foundation used by the Compliance Checker to identify relevant package declarations during digital inspection.
        </p>

        {/* Important Alert Notice */}
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r text-xs text-amber-900 space-y-1">
          <div className="flex items-center gap-2 font-bold text-amber-900">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Important Compliance Notice</span>
          </div>
          <p>
            The Rules were notified on 7th March 2011 and came into force on 1st April 2011. The Rules have subsequently been amended. For authoritative legal text, users should refer to the latest consolidated publication and official notifications issued by the Department of Consumer Affairs.
          </p>
        </div>

        {/* Key Framework Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 pt-2">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded text-center">
            <p className="text-xs text-slate-500 font-medium">Recent Legislation</p>
            <p className="text-base font-bold text-navy-900 mt-1">PCR Rules 2011</p>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded text-center">
            <p className="text-xs text-slate-500 font-medium">Rules Notified</p>
            <p className="text-base font-bold text-navy-900 mt-1">7th March 2011</p>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded text-center">
            <p className="text-xs text-slate-500 font-medium">Effective From</p>
            <p className="text-base font-bold text-navy-900 mt-1">1st April 2011</p>
          </div>
          <div className="p-4 bg-slate-50 border border-slate-200 rounded text-center">
            <p className="text-xs text-slate-500 font-medium">Primary Purpose</p>
            <p className="text-base font-bold text-navy-900 mt-1">Consumer Protection</p>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-xl font-bold text-slate-900">How It Works</h2>
          <p className="text-xs text-slate-500">A streamlined process for automated compliance verification.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-5 gap-4 relative">
          {[
            { step: "1. Scan / Upload", desc: "Submit product label image or scan", icon: Scan },
            { step: "2. Extract", desc: "Automated OCR text extraction", icon: Search },
            { step: "3. Verify", desc: "Check against rule repository", icon: ShieldCheck },
            { step: "4. Results", desc: "Instant compliance status", icon: CheckCircle2 },
            { step: "5. Report", desc: "Download official inspection report", icon: FileCheck },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="bg-slate-50 border border-slate-200 rounded p-4 text-center space-y-2 relative">
                <div className="w-10 h-10 bg-navy-900 text-white rounded-full flex items-center justify-center mx-auto shadow-sm">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-xs font-bold text-slate-900">{item.step}</h3>
                <p className="text-[11px] text-slate-500 leading-snug">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* System Capabilities Section */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-6">
        <div className="text-center space-y-1">
          <h2 className="text-xl font-bold text-slate-900">System Capabilities</h2>
          <p className="text-xs text-slate-500">Institutional grade tools for packaged commodity compliance.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded flex gap-4 items-start">
            <div className="p-2.5 bg-navy-900 text-white rounded shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Rule-Based Verification</h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Direct adherence to current Legal Metrology regulations, ensuring all statutory checks are grounded in official guidelines.
              </p>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded flex gap-4 items-start">
            <div className="p-2.5 bg-navy-900 text-white rounded shrink-0">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">AI-Powered OCR</h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Advanced optical character recognition to accurately extract text metadata from complex packaging designs.
              </p>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded flex gap-4 items-start">
            <div className="p-2.5 bg-navy-900 text-white rounded shrink-0">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Instant Results</h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Real-time processing capabilities delivering immediate feedback on label compliance status.
              </p>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded flex gap-4 items-start">
            <div className="p-2.5 bg-navy-900 text-white rounded shrink-0">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Detailed Reports</h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Comprehensive, officially formatted reports documenting specific areas of compliance and necessary corrections.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetrologyRules;
