import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FilePlus, History, Home, Info, PhoneCall, BookOpen, ShieldAlert, Menu, X } from 'lucide-react';

const Navbar = () => {
  const { user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const publicLinks = [
    { to: '/contact', label: 'Contact Us', icon: PhoneCall },
    { to: '/', label: 'Home', icon: Home },
    { to: '/about', label: 'About Us', icon: Info },
    { to: '/rules', label: 'Legal Metrology Rules', icon: BookOpen },
    { to: '/guidelines', label: 'Guidelines', icon: ShieldAlert },
  ];

  const officerLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/inspection/new', label: 'New Inspection', icon: FilePlus },
    { to: '/inspection-history', label: 'Inspection History', icon: History },
    { to: '/rules', label: 'Legal Metrology Rules', icon: BookOpen },
    { to: '/guidelines', label: 'Guidelines', icon: ShieldAlert },
  ];

  const links = user ? officerLinks : publicLinks;

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <nav className="bg-navy-900 text-slate-200 border-b border-navy-800 shadow-md relative z-40">
      <div className="max-w-7xl mx-auto px-4">
        {/* Desktop Horizontal Navigation Bar */}
        <div className="hidden md:flex items-center space-x-1 overflow-x-auto custom-scrollbar">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === '/'}
                className={({ isActive }) =>
                  `px-4 py-2.5 text-xs font-medium flex items-center gap-1.5 whitespace-nowrap transition-colors border-b-2 ${
                    isActive
                      ? 'border-amber-400 text-white bg-navy-800 font-semibold'
                      : 'border-transparent text-slate-300 hover:text-white hover:bg-navy-800/60'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5 text-slate-400" />
                {link.label}
              </NavLink>
            );
          })}
        </div>

        {/* Mobile Navbar Header with Hamburger Button */}
        <div className="flex md:hidden items-center justify-between py-2.5">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
            {user ? 'Officer Menu' : 'Navigation'}
          </span>
          <button
            onClick={toggleMobileMenu}
            aria-label="Toggle navigation menu"
            className="p-1.5 rounded text-slate-300 hover:text-white hover:bg-navy-800 transition-colors focus:outline-none cursor-pointer flex items-center gap-1 text-xs font-semibold"
          >
            {mobileMenuOpen ? (
              <>
                <X className="w-5 h-5" />
                <span>Close</span>
              </>
            ) : (
              <>
                <Menu className="w-5 h-5" />
                <span>Menu</span>
              </>
            )}
          </button>
        </div>

        {/* Mobile Dropdown Menu Content */}
        {mobileMenuOpen && (
          <div className="md:hidden py-2 border-t border-navy-800 space-y-1">
            {links.map((link) => {
              const Icon = link.icon;
              return (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.to === '/'}
                  onClick={closeMobileMenu}
                  className={({ isActive }) =>
                    `px-3 py-2.5 rounded text-xs font-medium flex items-center gap-2.5 transition-colors ${
                      isActive
                        ? 'bg-navy-800 text-amber-400 font-semibold border-l-4 border-amber-400'
                        : 'text-slate-200 hover:bg-navy-800/60 hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 text-slate-400 shrink-0" />
                  <span>{link.label}</span>
                </NavLink>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;

