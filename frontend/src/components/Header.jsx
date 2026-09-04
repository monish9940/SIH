import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, LogOut, PlusCircle } from 'lucide-react';

const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getDisplayName = () => {
    if (!user || !user.full_name) return '';
    const name = user.full_name.trim();
    if (name.toLowerCase().startsWith('inspector')) {
      return name;
    }
    return `Inspector ${name}`;
  };

  return (
    <header className="bg-white border-b border-slate-200 w-full text-slate-800">
      {/* Topmost Government Bar */}
      <div className="bg-slate-100 border-b border-slate-200 py-1.5 px-4 text-[10px] sm:text-[11px] font-medium text-slate-600">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-start sm:items-center gap-1.5 sm:gap-4">
          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
            <span className="font-semibold text-slate-700">GOVERNMENT OF INDIA</span>
            <span className="text-slate-400">|</span>
            <span className="truncate">Ministry of Consumer Affairs, Food & Public Distribution</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] shrink-0 self-end sm:self-auto">
            <span className="cursor-pointer hover:underline hidden sm:inline">Skip to Main Content</span>
            <select className="bg-transparent text-[11px] font-medium focus:outline-none cursor-pointer">
              <option>English</option>
              <option>Hindi</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Header Branding Area */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap justify-between items-center gap-3 sm:gap-4">
        {/* Left: State Emblem & Department Title */}
        <Link to="/" className="flex items-center gap-2.5 sm:gap-3 group shrink-0 max-w-[80vw] sm:max-w-none">
          <img
            src="/emblem.png"
            alt="State Emblem of India"
            className="h-10 sm:h-12 w-auto object-contain shrink-0 mix-blend-multiply"
          />
          <div>
            <h1 className="text-sm sm:text-lg font-bold text-slate-900 leading-tight group-hover:text-slate-900 transition-colors">
              Department of Legal Metrology
            </h1>
            <p className="text-[10px] sm:text-xs text-slate-500 font-medium">
              Ministry of Consumer Affairs, Food & Public Distribution
            </p>
          </div>
        </Link>

        {/* Center: System Title */}
        <div className="hidden lg:block text-center">
          <div className="text-base font-bold text-slate-900 tracking-tight">Compliance Checker</div>
          <div className="text-xs text-slate-500 font-medium">Packaged Commodity Compliance System</div>
        </div>

        {/* Right: Authenticated User Actions OR [ Login ] [ Get Started ] */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {user ? (
            <>
              <Link
                to="/inspection/new"
                className="bg-orange-600 hover:bg-orange-700 text-white px-2.5 sm:px-3.5 py-1.5 sm:py-2 rounded text-xs font-bold flex items-center gap-1 sm:gap-1.5 shadow-sm transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span className="hidden xs:inline">New Inspection</span>
                <span className="xs:hidden">New</span>
              </Link>
              <div className="flex items-center gap-1.5 sm:gap-2 bg-slate-100 px-2 sm:px-3 py-1.5 sm:py-2 rounded border border-slate-200 text-xs font-bold text-slate-800">
                <User className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-900 shrink-0" />
                <span className="max-w-[100px] sm:max-w-[150px] truncate">{getDisplayName()}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 sm:p-2 text-slate-600 hover:text-red-600 hover:bg-slate-100 rounded border border-slate-200 transition-colors cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="border border-slate-900 text-slate-900 hover:bg-slate-900 hover:text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded text-xs font-bold transition-all flex items-center gap-1 shadow-sm"
              >
                <User className="w-3.5 h-3.5" />
                <span>Login</span>
              </Link>
              <Link
                to="/signup"
                className="bg-slate-900 hover:bg-slate-800 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded text-xs font-bold shadow-md transition-all flex items-center gap-1"
              >
                <span>Get Started</span>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;

