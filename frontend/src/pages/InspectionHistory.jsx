import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Search, Filter, Eye, FileText, PlusCircle, RefreshCw } from 'lucide-react';

const InspectionHistory = () => {
  const [inspections, setInspections] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/inspections?limit=50');
      setInspections(res.data);
    } catch (err) {
      console.error('Failed to fetch inspection history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredInspections = inspections.filter((item) => {
    const matchesSearch =
      item.inspection_id.toLowerCase().includes(search.toLowerCase()) ||
      (item.product_name && item.product_name.toLowerCase().includes(search.toLowerCase())) ||
      (item.manufacturer && item.manufacturer.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus =
      statusFilter === 'ALL' || item.overall_status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Inspection History</h1>
          <p className="text-xs text-slate-500">Comprehensive ledger of all statutory inspections conducted under your account.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchHistory}
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

      {/* Filter and Search Toolbar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-col sm:flex-row justify-between gap-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Inspection ID, Product, or Manufacturer..."
            className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-xs focus:ring-1 focus:ring-navy-900 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-slate-300 rounded px-3 py-2 text-xs font-medium bg-white focus:ring-1 focus:ring-navy-900 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLIANT">Compliant</option>
            <option value="RESOLVED">Resolved</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="NON-COMPLIANT">Non-Compliant</option>
          </select>
        </div>
      </div>

      {/* History Ledger Table */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                <th className="py-2.5 px-3">INSPECTION ID</th>
                <th className="py-2.5 px-3">DATE & TIME</th>
                <th className="py-2.5 px-3">PRODUCT / ENTITY</th>
                <th className="py-2.5 px-3">COMMODITY TYPE</th>
                <th className="py-2.5 px-3">SCORE</th>
                <th className="py-2.5 px-3">STATUS</th>
                <th className="py-2.5 px-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {loading ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-400">Loading records...</td>
                </tr>
              ) : filteredInspections.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-400">
                    No inspection records found matching your filters.
                  </td>
                </tr>
              ) : (
                filteredInspections.map((item) => (
                  <tr key={item.inspection_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">#{item.inspection_id}</td>
                    <td className="py-3 px-3 text-slate-500">{new Date(item.created_at).toLocaleString()}</td>
                    <td className="py-3 px-3 font-semibold text-slate-800">{item.product_name || item.product_information?.product_name || 'Pre-packaged Goods'}</td>
                    <td className="py-3 px-3 text-slate-500">{item.commodity_type || 'General'}</td>
                    <td className="py-3 px-3 font-bold text-slate-900">{item.compliance_score !== null && item.compliance_score !== undefined ? `${item.compliance_score}%` : 'N/A'}</td>
                    <td className="py-3 px-3">
                      {(item.status === 'RESOLVED' || item.overall_status === 'RESOLVED') && (
                        <span className="badge-compliant font-bold">Resolved</span>
                      )}
                      {item.overall_status === 'COMPLIANT' && item.status !== 'RESOLVED' && (
                        <span className="badge-compliant">Compliant</span>
                      )}
                      {item.overall_status === 'NON-COMPLIANT' && item.status !== 'RESOLVED' && (
                        <span className="badge-violation">Violation Found</span>
                      )}
                      {item.overall_status === 'NEEDS_REVIEW' && item.status !== 'RESOLVED' && (
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

export default InspectionHistory;
