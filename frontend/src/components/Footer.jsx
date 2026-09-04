import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="bg-navy-950 text-slate-400 mt-auto border-t border-navy-800 text-xs">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-6 border-b border-slate-800">
          <div>
            <h3 className="text-white text-sm font-bold tracking-tight mb-1">Compliance Checker</h3>
            <p className="text-slate-400 max-w-xl">
              An initiative by the Department of Consumer Affairs to ensure transparent and compliant packaged commodities across India.
            </p>
          </div>

          <div className="flex flex-wrap gap-4 text-xs font-medium text-slate-300">
            <Link to="/privacy" className="hover:text-amber-400 transition-colors">Privacy Policy</Link>
            <span>•</span>
            <Link to="/terms" className="hover:text-amber-400 transition-colors">Terms of Service</Link>
            <span>•</span>
            <Link to="/contact" className="hover:text-amber-400 transition-colors">Help Desk</Link>
            <span>•</span>
            <Link to="/accessibility" className="hover:text-amber-400 transition-colors">Accessibility Statement</Link>
            <span>•</span>
            <Link to="/sitemap" className="hover:text-amber-400 transition-colors">Sitemap</Link>
          </div>
        </div>

        <div className="pt-4 flex flex-col sm:flex-row justify-between items-center text-[11px] text-slate-500 gap-2">
          <p>© 2026 Department of Consumer Affairs, Government of India. All rights reserved.</p>
          <p className="italic">Designed for Official Verification & Regulatory Screening</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
