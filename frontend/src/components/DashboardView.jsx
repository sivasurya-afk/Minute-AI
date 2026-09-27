import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  FolderKanban, 
  ArrowUpRight,
  Sparkles,
  TrendingUp,
  BarChart3,
  PieChart,
  Calendar
} from 'lucide-react';
import { api } from '../services/api';

export default function DashboardView({ onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      const res = await api.getDashboardSummary();
      setData(res);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-xs font-medium text-slate-500">Loading intelligence dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        Failed to load dashboard data: {error}
      </div>
    );
  }

  const { metrics, charts, recent_transcripts } = data;

  const statCards = [
    {
      title: 'Transcripts Processed',
      value: metrics.total_transcripts,
      sub: 'Meetings analyzed',
      icon: FileText,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50/80',
      border: 'border-indigo-100',
    },
    {
      title: 'Extracted Action Items',
      value: metrics.total_action_items,
      sub: 'Verified tasks',
      icon: TrendingUp,
      color: 'text-violet-600',
      bg: 'bg-violet-50/80',
      border: 'border-violet-100',
    },
    {
      title: 'Awaiting Review',
      value: metrics.awaiting_review,
      sub: 'Pending human sign-off',
      icon: Clock,
      color: 'text-amber-600',
      bg: 'bg-amber-50/80',
      border: 'border-amber-100',
    },
    {
      title: 'Needs Clarification',
      value: metrics.requiring_clarification,
      sub: 'Ambiguous or low confidence',
      icon: AlertCircle,
      color: 'text-rose-600',
      bg: 'bg-rose-50/80',
      border: 'border-rose-100',
    },
    {
      title: 'Configured Projects',
      value: metrics.configured_projects,
      sub: 'Jira target scopes',
      icon: FolderKanban,
      color: 'text-blue-600',
      bg: 'bg-blue-50/80',
      border: 'border-blue-100',
    },
    {
      title: 'Approved Action Items',
      value: metrics.approved_items,
      sub: 'Ready for Jira sync',
      icon: CheckCircle2,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50/80',
      border: 'border-emerald-100',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Hero Banner */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Executive Dashboard</h1>
            <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200/50">
              Live Synthesis
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-xl">
            Real-time pipeline converting meeting transcripts into classified, high-confidence Jira action items.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('process')}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Process New Transcript</span>
          </button>
          <button
            onClick={() => onNavigate('action_items')}
            className="flex items-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-all"
          >
            <span>Review Items</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-[0_1px_2px_rgba(0,0,0,0.03)] hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-medium text-slate-500 line-clamp-1">{card.title}</span>
                <div className={`p-1.5 rounded-lg ${card.bg} ${card.color}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 tracking-tight">{card.value}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">{card.sub}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4 Interactive SVG Visual Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart 1: Action Items by Jira Project */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
                <FolderKanban className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">Action Items by Jira Project</h2>
            </div>
            <span className="text-xs text-slate-400">Semantic Allocation</span>
          </div>

          <div className="space-y-3">
            {charts.by_project.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No project items yet</p>
            ) : (
              charts.by_project.map((p, idx) => {
                const total = metrics.total_action_items || 1;
                const pct = Math.round((p.count / total) * 100);
                const colors = ['bg-indigo-600', 'bg-blue-500', 'bg-emerald-500', 'bg-violet-500', 'bg-amber-500'];
                const barColor = colors[idx % colors.length];

                return (
                  <div key={p.project}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-semibold text-slate-700">{p.project}</span>
                      <span className="text-slate-500">{p.count} items ({pct}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div className={`${barColor} h-2 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Chart 2: Status Breakdown */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
                <PieChart className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">Review Status Distribution</h2>
            </div>
            <span className="text-xs text-slate-400">Human-in-the-Loop</span>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            {charts.by_status.map((st) => {
              const statusColors = {
                'Approved': { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200/60', dot: 'bg-emerald-500' },
                'Pending Review': { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200/60', dot: 'bg-amber-500' },
                'Needs Clarification': { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200/60', dot: 'bg-indigo-500' },
                'Rejected': { bg: 'bg-rose-50', text: 'text-rose-700', border: 'border-rose-200/60', dot: 'bg-rose-500' },
              };
              const style = statusColors[st.status] || { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200', dot: 'bg-slate-400' };

              return (
                <div key={st.status} className={`p-3 rounded-xl border ${style.border} ${style.bg} flex items-center justify-between`}>
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${style.dot}`}></span>
                    <span className="text-xs font-medium text-slate-700">{st.status}</span>
                  </div>
                  <span className={`text-base font-bold ${style.text}`}>{st.count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Chart 3: Priority Distribution */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-amber-50 text-amber-600">
                <BarChart3 className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">Action Items by Priority</h2>
            </div>
            <span className="text-xs text-slate-400">Explicit commitments</span>
          </div>

          <div className="flex items-end gap-3 h-32 pt-4 px-2">
            {charts.by_priority.map((pr) => {
              const maxCount = Math.max(...charts.by_priority.map(x => x.count), 1);
              const heightPct = Math.max(Math.round((pr.count / maxCount) * 100), 12);
              
              const pColors = {
                'Highest': 'bg-rose-500',
                'High': 'bg-orange-500',
                'Medium': 'bg-amber-400',
                'Low': 'bg-blue-400',
                'Lowest': 'bg-slate-400',
                'Unspecified': 'bg-slate-300',
              };

              return (
                <div key={pr.priority} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                  <span className="text-[10px] font-bold text-slate-700">{pr.count}</span>
                  <div 
                    className={`w-full rounded-t-md transition-all duration-500 ${pColors[pr.priority] || 'bg-indigo-400'}`}
                    style={{ height: `${heightPct}%` }}
                  ></div>
                  <span className="text-[10px] text-slate-500 truncate w-full text-center">{pr.priority}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Chart 4: Extracted Timeline */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-violet-50 text-violet-600">
                <Calendar className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">Action Items Extracted Over Time</h2>
            </div>
            <span className="text-xs text-slate-400">Processing cadence</span>
          </div>

          <div className="space-y-2 pt-2">
            {charts.by_time.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No timeline records yet</p>
            ) : (
              charts.by_time.slice(-4).map((t) => {
                const total = metrics.total_action_items || 1;
                const pct = Math.round((t.count / total) * 100);
                return (
                  <div key={t.date} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-xs font-medium text-slate-600 font-mono">{t.date}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-indigo-600">{t.count} items</span>
                      <span className="text-[10px] text-slate-400">({pct}%)</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Recent Transcripts Feed */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-slate-900">Recent Meeting Discussions</h2>
          <button
            onClick={() => onNavigate('history')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            <span>View All Archives</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 uppercase text-[10px]">
                <th className="pb-2.5 font-semibold">Meeting Name</th>
                <th className="pb-2.5 font-semibold">Format</th>
                <th className="pb-2.5 font-semibold">Meeting Date</th>
                <th className="pb-2.5 font-semibold text-center">Items Extracted</th>
                <th className="pb-2.5 font-semibold text-center">Approved</th>
                <th className="pb-2.5 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recent_transcripts.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-6 text-center text-slate-400">
                    No transcripts processed yet.
                  </td>
                </tr>
              ) : (
                recent_transcripts.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 font-semibold text-slate-800">{t.meeting_name}</td>
                    <td className="py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600 font-medium">
                        {(t.source_type || 'paste').toUpperCase()}
                      </span>
                    </td>
                    <td className="py-3 text-slate-500">{t.meeting_date || 'N/A'}</td>
                    <td className="py-3 text-center font-bold text-indigo-600">{t.action_item_count || 0}</td>
                    <td className="py-3 text-center font-bold text-emerald-600">{t.approved_count || 0}</td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => onNavigate('action_items')}
                        className="text-indigo-600 hover:text-indigo-700 font-semibold"
                      >
                        Inspect →
                      </button>
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
}
