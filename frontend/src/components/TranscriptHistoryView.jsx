import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  Calendar, 
  FileText, 
  RefreshCw, 
  Trash2, 
  ChevronDown, 
  ChevronUp,
  CheckCircle2,
  Clock,
  Sparkles
} from 'lucide-react';
import { api } from '../services/api';

export default function TranscriptHistoryView({ onNavigate }) {
  const [transcripts, setTranscripts] = useState([]);
  const [search, setSearch] = useState('');
  const [filterDate, setFilterDate] = useState('');
  const [loading, setLoading] = useState(true);

  // Expanded transcript item
  const [expandedId, setExpandedId] = useState(null);
  const [detailsData, setDetailsData] = useState({});
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [reprocessingId, setReprocessingId] = useState(null);

  useEffect(() => {
    loadTranscripts();
  }, []);

  async function loadTranscripts() {
    try {
      setLoading(true);
      const res = await api.getTranscripts();
      setTranscripts(res.transcripts || []);
    } catch (err) {
      console.error('Failed to load transcripts', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleExpand(id) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }

    setExpandedId(id);
    if (!detailsData[id]) {
      try {
        setLoadingDetails(true);
        const res = await api.getTranscript(id);
        setDetailsData(prev => ({ ...prev, [id]: res }));
      } catch (err) {
        alert(`Failed to load transcript details: ${err.message}`);
      } finally {
        setLoadingDetails(false);
      }
    }
  }

  async function handleReprocess(id) {
    if (!confirm('This will clear previous action items for this meeting and re-run AI extraction. Continue?')) return;
    try {
      setReprocessingId(id);
      const res = await api.reprocessTranscript(id);
      alert(`Reprocessed successfully! Extracted ${res.count} items.`);
      // reload
      const resDetails = await api.getTranscript(id);
      setDetailsData(prev => ({ ...prev, [id]: resDetails }));
      loadTranscripts();
    } catch (err) {
      alert(`Reprocessing failed: ${err.message}`);
    } finally {
      setReprocessingId(null);
    }
  }

  async function handleDelete(id) {
    if (!confirm('Permanently delete this meeting transcript and all linked action items?')) return;
    try {
      await api.deleteTranscript(id);
      setTranscripts(prev => prev.filter(t => t.id !== id));
      if (expandedId === id) setExpandedId(null);
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  }

  const filtered = transcripts.filter(t => {
    const matchesSearch = !search || t.meeting_name?.toLowerCase().includes(search.toLowerCase());
    const matchesDate = !filterDate || String(t.meeting_date) === filterDate;
    return matchesSearch && matchesDate;
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Transcript Archive</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
              {filtered.length} Meetings
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Historical archive of all processed meeting discussions, extraction runs, and linked action items.
          </p>
        </div>

        <button
          onClick={() => onNavigate('process')}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Process New</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-[0_1px_2px_rgba(0,0,0,0.02)] grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transcripts by meeting name..."
            className="w-full pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
          />
        </div>
        <div>
          <input
            type="date"
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value)}
            className="w-full px-3 py-1.5 text-xs text-slate-700 border border-slate-200 rounded-lg focus:outline-none"
          />
        </div>
      </div>

      {/* Transcripts List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <History className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800">No transcripts found</h3>
          <p className="text-xs text-slate-500 mt-1">Try clearing filters or processing a new meeting transcript.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((t) => {
            const isExpanded = expandedId === t.id;
            const details = detailsData[t.id];

            return (
              <div
                key={t.id}
                className="bg-white rounded-xl border border-slate-200/90 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden transition-all"
              >
                {/* Main Row */}
                <div 
                  onClick={() => handleToggleExpand(t.id)}
                  className="p-4 cursor-pointer hover:bg-slate-50/60 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900">{t.meeting_name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-100 text-slate-600">
                        {(t.source_type || 'paste').toUpperCase()}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-500">
                      <span>📅 Held: <b className="text-slate-700">{t.meeting_date || 'N/A'}</b></span>
                      <span>•</span>
                      <span>Processed: {String(t.created_at || '').substring(0, 10)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end md:self-center">
                    <div className="flex items-center gap-3 text-right">
                      <div>
                        <div className="text-base font-bold text-indigo-600 leading-none">{t.action_item_count || 0}</div>
                        <div className="text-[10px] text-slate-400 uppercase">Extracted</div>
                      </div>
                      <div>
                        <div className="text-base font-bold text-emerald-600 leading-none">{t.approved_count || 0}</div>
                        <div className="text-[10px] text-slate-400 uppercase">Approved</div>
                      </div>
                    </div>

                    <div className="p-1 rounded-lg text-slate-400 hover:text-slate-600">
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <div className="p-5 bg-slate-50/70 border-t border-slate-200 space-y-4">
                    {loadingDetails && !details ? (
                      <div className="py-6 text-center text-xs text-slate-400">Loading details...</div>
                    ) : (
                      <>
                        {/* Tabs: Text vs Items */}
                        <div className="space-y-3">
                          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                            Meeting Transcript Text
                          </h4>
                          <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs font-mono max-h-48 overflow-y-auto whitespace-pre-wrap text-slate-700">
                            {details?.transcript?.transcript_text || t.transcript_text}
                          </div>
                        </div>

                        {/* Linked Items List */}
                        <div className="space-y-2 pt-2">
                          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                            Linked Action Items ({details?.action_items?.length || 0})
                          </h4>
                          <div className="space-y-2">
                            {(details?.action_items || []).map((item) => (
                              <div key={item.id} className="p-3 bg-white rounded-xl border border-slate-200/90 flex items-center justify-between text-xs">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-bold text-indigo-600 font-mono">[{item.jira_project_key || 'NONE'}]</span>
                                    <span className="font-semibold text-slate-800">{item.action_title}</span>
                                  </div>
                                  <div className="text-[11px] text-slate-500 mt-0.5">
                                    Assignee: {item.assignee || 'Unassigned'} | Priority: {item.priority || 'None'}
                                  </div>
                                </div>
                                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                                  {item.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Bottom Actions: Reprocess & Delete */}
                        <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
                          <button
                            disabled={reprocessingId === t.id}
                            onClick={() => handleReprocess(t.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 text-xs font-semibold transition-all"
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${reprocessingId === t.id ? 'animate-spin' : ''}`} />
                            <span>{reprocessingId === t.id ? 'Reprocessing...' : 'Safe AI Reprocess'}</span>
                          </button>

                          <button
                            onClick={() => handleDelete(t.id)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold transition-all"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Delete Transcript</span>
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
