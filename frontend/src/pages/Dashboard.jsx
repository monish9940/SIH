import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { PlusCircle, FileText, CheckCircle2, AlertTriangle, Clock, Eye, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#16A34A', '#DC2626', '#F59E0B'];

const Dashboard = () => {
  const [summary, setSummary] = useState({
    total_scans: 0,
    compliant: 0,
    issues_resolved: 0,
    pending_issues: 0
  });
  const [trends, setTrends] = useState([]);
  const [resolutionData, setResolutionData] = useState([]);
  const [recentInspections, setRecentInspections] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [sumRes, trendRes, resRes, listRes] = await Promise.all([
        api.get('/dashboard/summary'),
        api.get('/dashboard/trends'),
        api.get('/dashboard/resolution-status'),
        api.get('/inspections?limit=6')
      ]);

      setSummary(sumRes.data);
      setTrends(trendRes.data);
      setResolutionData([
        { name: 'Compliant', value: resRes.data.compliant || 0 },
        { name: 'Violations', value: resRes.data.violations || 0 },
        { name: 'Pending', value: resRes.data.pending || 0 }
      ]);
      setRecentInspections(listRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Dashboard Top Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Officer Dashboard</h1>
          <p className="text-xs text-slate-500">Overview of your inspection workload and recent activities.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
            title="Refresh Data"
            className="p-2 border border-slate-300 rounded bg-white hover:bg-slate-50 text-slate-600"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <Link
            to="/inspection/new"
            className="bg-gov-orange hover:bg-orange-600 text-white px-4 py-2 rounded text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            New Inspection
          </Link>
        </div>
      </div>

      {/* Top Statistic Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-slate-500">
            <span className="text-xs font-bold uppercase tracking-wider">TOTAL SCANS</span>
            <FileText className="w-5 h-5 text-navy-900" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{summary.total_scans.toLocaleString()}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-emerald-700">
            <span className="text-xs font-bold uppercase tracking-wider">COMPLIANT</span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-3xl font-extrabold text-emerald-600">{summary.compliant.toLocaleString()}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-amber-700">
            <span className="text-xs font-bold uppercase tracking-wider">ISSUES RESOLVED</span>
            <AlertTriangle className="w-5 h-5 text-amber-500" />
          </div>
          <p className="text-3xl font-extrabold text-amber-600">{summary.issues_resolved.toLocaleString()}</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="flex justify-between items-center text-red-700">
            <span className="text-xs font-bold uppercase tracking-wider">PENDING ISSUES</span>
            <Clock className="w-5 h-5 text-red-500" />
          </div>
          <p className="text-3xl font-extrabold text-red-600">{summary.pending_issues.toLocaleString()}</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Inspection Trends Chart */}
        <div className="lg:col-span-8 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">Inspection Trends (Last 7 Days)</h2>
            <span className="text-[11px] text-slate-500 font-medium">Daily Activity</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0B192C" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0B192C" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', fontSize: '12px', border: '1px solid #cbd5e1' }} />
                <Area type="monotone" dataKey="count" stroke="#0B192C" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right: Resolution Status Donut Chart */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4 flex flex-col justify-between">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-bold text-slate-900">Resolution Status</h2>
            <p className="text-[11px] text-slate-500">Distribution by inspection outcome</p>
          </div>

          <div className="h-48 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={resolutionData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {resolutionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="flex justify-around items-center pt-2 border-t border-slate-100 text-xs font-semibold text-slate-700">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-emerald-600"></span>
              <span>Compliant</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-600"></span>
              <span>Violations</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              <span>Pending</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Inspections Table */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <h2 className="text-sm font-bold text-slate-900">Recent Inspections</h2>
          <Link to="/inspection-history" className="text-xs text-navy-900 font-semibold hover:underline">
            View All
          </Link>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                <th className="py-2.5 px-3">INSPECTION ID</th>
                <th className="py-2.5 px-3">DATE</th>
                <th className="py-2.5 px-3">ENTITY / PRODUCT</th>
                <th className="py-2.5 px-3">STATUS</th>
                <th className="py-2.5 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {recentInspections.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-slate-400">
                    No inspection records found. Click "New Inspection" to begin analysis.
                  </td>
                </tr>
              ) : (
                recentInspections.map((item) => (
                  <tr key={item.inspection_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">{item.inspection_id}</td>
                    <td className="py-3 px-3 text-slate-500">{new Date(item.created_at).toLocaleDateString()}</td>
                    <td className="py-3 px-3 font-semibold text-slate-800">{item.product_name || 'Pre-packaged Goods'}</td>
                    <td className="py-3 px-3">
                      {item.overall_status === 'COMPLIANT' && (
                        <span className="badge-compliant">Compliant</span>
                      )}
                      {item.overall_status === 'NON-COMPLIANT' && (
                        <span className="badge-violation">Violation Found</span>
                      )}
                      {item.overall_status === 'NEEDS_REVIEW' && (
                        <span className="badge-pending">Pending Review</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        to={`/inspection/${item.inspection_id}`}
                        className="p-1.5 bg-slate-100 hover:bg-navy-900 hover:text-white rounded border border-slate-200 text-slate-600 inline-flex items-center gap-1 transition-colors text-[11px] font-semibold"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
