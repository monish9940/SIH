import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, CheckCircle2, Cpu, FileText, Zap, ArrowRight, PackageCheck } from 'lucide-react';

const Home = () => {
  return (
    <div className="space-y-12 pb-12">
      {/* Hero Section */}
      <section className="bg-white border-b border-slate-200 py-12 px-4">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Heading & Information */}
          <div className="lg:col-span-7 space-y-6">
            <h1 className="text-3xl md:text-5xl font-extrabold text-slate-900 leading-tight tracking-tight">
              Check Compliance. <br />
              <span className="text-navy-900">Build Trust.</span>
            </h1>

            <p className="text-slate-600 text-base leading-relaxed max-w-2xl">
              Scan any packaged commodity and instantly verify compliance with the Legal Metrology (Packaged Commodities) Rules, 2011 — no manual checklists required.
            </p>

            {/* Hero CTA Buttons */}
            <div className="flex flex-wrap gap-4 pt-2">
              <Link
                to="/signup"
                className="bg-navy-900 hover:bg-slate-800 text-white font-bold px-6 py-3 rounded text-sm shadow-md transition-all flex items-center gap-2"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="bg-gov-orange hover:bg-orange-600 text-white font-bold px-6 py-3 rounded text-sm shadow-sm transition-all flex items-center gap-2"
              >
                <span>Institutional Login</span>
              </Link>
            </div>

            {/* Quick Feature Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                <ShieldCheck className="w-5 h-5 text-navy-900 mx-auto mb-1" />
                <p className="text-xs font-bold text-slate-800">Rule-Based Engine</p>
                <p className="text-[10px] text-slate-500">PCR 2011 Verified</p>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                <Cpu className="w-5 h-5 text-navy-900 mx-auto mb-1" />
                <p className="text-xs font-bold text-slate-800">AI-Powered OCR</p>
                <p className="text-[10px] text-slate-500">Fast Label Analysis</p>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                <Zap className="w-5 h-5 text-navy-900 mx-auto mb-1" />
                <p className="text-xs font-bold text-slate-800">Instant Results</p>
                <p className="text-[10px] text-slate-500">Real-time Feedback</p>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center">
                <FileText className="w-5 h-5 text-navy-900 mx-auto mb-1" />
                <p className="text-xs font-bold text-slate-800">Detailed Report</p>
                <p className="text-[10px] text-slate-500">PDF Generation</p>
              </div>
            </div>
          </div>

          {/* Right Column: Packaged Product Visual & Live Compliance Badge */}
          <div className="lg:col-span-5 relative">
            <div className="bg-slate-100 p-6 rounded-xl border border-slate-200 shadow-md">
              <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm space-y-4">
                <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <PackageCheck className="w-5 h-5 text-navy-900" />
                    <span className="text-xs font-bold text-slate-700">Sample Commodity Inspection</span>
                  </div>
                  <span className="badge-compliant">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Compliant
                  </span>
                </div>

                {/* Label Mock Visual */}
                <div className="bg-amber-50/60 border border-amber-200 rounded p-4 text-xs font-mono space-y-2 text-slate-700">
                  <p className="font-bold text-slate-900 text-sm text-center border-b border-amber-200 pb-1">
                    PACKAGED COMMODITY LABEL
                  </p>
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <div><span className="font-semibold">Net Weight:</span> Standard SI Unit</div>
                    <div><span className="font-semibold">MRP (Incl. taxes):</span> Currency & Tax</div>
                    <div><span className="font-semibold">Mfg Date:</span> Month & Year</div>
                    <div><span className="font-semibold">Batch No:</span> Lot / Batch ID</div>
                  </div>
                  <p className="text-[10px] text-slate-500 pt-1 border-t border-amber-200">
                    Mfd by: Manufacturer / Packer Full Name & Postal Address
                  </p>
                </div>

                {/* Verified Extracted Ledger */}
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between items-center bg-slate-50 p-2 rounded">
                    <span className="text-slate-600">MRP Declaration:</span>
                    <span className="font-semibold text-emerald-700 flex items-center gap-1">Verified <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /></span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-50 p-2 rounded">
                    <span className="text-slate-600">Net Quantity:</span>
                    <span className="font-semibold text-emerald-700 flex items-center gap-1">Verified <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /></span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-50 p-2 rounded">
                    <span className="text-slate-600">Manufacturer Info:</span>
                    <span className="font-semibold text-emerald-700 flex items-center gap-1">Verified <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Compliance Checklist Section */}
      <section className="max-w-7xl mx-auto px-4">
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-6">
          <div className="border-b border-slate-200 pb-3">
            <h2 className="text-xl font-bold text-slate-900">Compliance Checklist</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Our AI system automatically verifies the presence and accuracy of these mandatory declarations as per Legal Metrology Rules:
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {[
              "Manufacturer Details",
              "Net Quantity",
              "Maximum Retail Price (MRP)",
              "Consumer Care Details",
              "Commodity Name",
              "Month & Year of Manufacture",
              "Unit Sale Price (USP)",
              "Country of Origin"
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2.5 bg-slate-50 p-3 rounded border border-slate-200">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="text-xs font-semibold text-slate-700">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
