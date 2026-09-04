import React from 'react';
import { Building2, ShieldCheck, Package, Eye, Lock, Award } from 'lucide-react';

const AboutUs = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Title Header */}
      <div className="text-center space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-600">INSTITUTIONAL OVERVIEW</p>
        <h1 className="text-3xl font-extrabold text-slate-900">About Us</h1>
        <p className="text-xs text-slate-500 max-w-2xl mx-auto leading-relaxed">
          The Department of Legal Metrology ensures fair trade practices and consumer protection by enforcing standard weights, measures, and accurate declarations on packaged commodities across India.
        </p>
      </div>

      {/* Grid of Main Institutional Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: About Legal Metrology */}
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-navy-900 font-bold text-base border-b border-slate-100 pb-2">
            <Building2 className="w-5 h-5 text-amber-500" />
            <h2>About Legal Metrology</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Legal Metrology is a critical wing of the Department of Consumer Affairs, tasked with regulating weights and measures. It establishes transparency and accuracy in trade transactions, ensuring that every citizen receives the exact quantity they pay for.
          </p>
          <p className="text-xs text-slate-600 leading-relaxed">
            By maintaining rigorous standards, the department fosters a level playing field for businesses while safeguarding consumers against malpractice. This includes the regular calibration of industrial weighing instruments and the certification of measuring devices used in daily commerce.
          </p>
        </div>

        {/* Card 2: Role of Compliance Checker */}
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-navy-900 font-bold text-base border-b border-slate-100 pb-2">
            <ShieldCheck className="w-5 h-5 text-amber-500" />
            <h2>Role of Compliance Checker</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            The Compliance Checker is an automated digital portal designed to streamline the verification of packaged commodities. It empowers officials and citizens alike to ensure that goods in the market adhere strictly to statutory declarations.
          </p>
          <div className="bg-slate-50 p-3 rounded border border-slate-200 text-xs font-semibold text-slate-700">
            KEY FUNCTION: Rapid verification of MRP, Net Weight, Date of Manufacture, and Manufacturer details.
          </div>
        </div>

        {/* Card 3: Packaged Commodities */}
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-navy-900 font-bold text-base border-b border-slate-100 pb-2">
            <Package className="w-5 h-5 text-amber-500" />
            <h2>Packaged Commodities</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            The Legal Metrology (Packaged Commodities) Rules mandate specific declarations on pre-packaged goods intended for retail sale. These declarations provide essential information, allowing consumers to make informed purchasing decisions:
          </p>
          <ul className="text-xs text-slate-600 space-y-1.5 list-disc list-inside pt-1">
            <li>Name and address of the manufacturer or packer.</li>
            <li>Common or generic name of the commodity.</li>
            <li>Net quantity in standard units of weight or measure.</li>
            <li>Maximum Retail Price (MRP) inclusive of all taxes.</li>
            <li>Month and year of manufacture or packing.</li>
          </ul>
        </div>

        {/* Card 4: Consumer Protection */}
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-3">
          <div className="flex items-center gap-2.5 text-navy-900 font-bold text-base border-b border-slate-100 pb-2">
            <Award className="w-5 h-5 text-amber-500" />
            <h2>Consumer Protection</h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            The overarching purpose of these rules is the steadfast protection of consumer rights. We strive to eliminate ambiguity in packaging and pricing, ensuring trust in the marketplace.
          </p>
          <div className="grid grid-cols-2 gap-3 pt-2">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center space-y-1">
              <Eye className="w-5 h-5 text-navy-900 mx-auto" />
              <p className="text-xs font-bold text-slate-800">Transparency</p>
              <p className="text-[10px] text-slate-500">Clear declarations on all packaging</p>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded text-center space-y-1">
              <Lock className="w-5 h-5 text-navy-900 mx-auto" />
              <p className="text-xs font-bold text-slate-800">Enforcement</p>
              <p className="text-[10px] text-slate-500">Strict action against violators</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutUs;
