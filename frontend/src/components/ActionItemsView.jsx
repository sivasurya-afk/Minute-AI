import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  Check, 
  X, 
  HelpCircle, 
  Edit3, 
  Trash2, 
  Sparkles,
  ChevronDown,
  CheckCircle2,
  Calendar,
  User,
  FolderKanban,
  FileSpreadsheet
} from 'lucide-react';
import { api } from '../services/api';

export default function ActionItemsView() {
  const [items, setItems] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedProject, setSelectedProject] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedPriority, setSelectedPriority] = useState('All');
  const [selectedType, setSelectedType] = useState('All');

  // Editing state
  const [editingItem, setEditingItem] = useState(null);

  useEffect(() => {
    loadData();
  }, [selectedProject, selectedStatus, selectedPriority, selectedType]);

  async function loadData() {
    try {
      setLoading(true);
      const [itemsRes, projRes] = await Promise.all([
        api.getActionItems({
          project_key: selectedProject,
          status: selectedStatus,
          priority: selectedPriority,
          action_type: selectedType,
          search: search.trim() || undefined,
        }),
        api.getProjects(),
      ]);
      setItems(itemsRes.action_items || []);
      setProjects(projRes.projects || []);
    } catch (err) {
      console.error('Failed to load action items', err);
    } finally {
      setLoading(false);
    }
  }

  function handleSearchSubmit(e) {
    e.preventDefault();
    loadData();
  }

  async function handleStatusChange(itemId, status) {
    try {
      await api.updateStatus(itemId, status);
      setItems(prev => prev.map(i => i.id === itemId ? { ...i, status } : i));
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    }
  }

  async function handleDelete(itemId) {
    if (!confirm('Are you sure you want to delete this action item?')) return;
    try {
      await api.deleteActionItem(itemId);
      setItems(prev => prev.filter(i => i.id !== itemId));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  }

  async function handleSaveEdit(e) {
    e.preventDefault();
    if (!editingItem) return;

    try {
      await api.updateActionItem(editingItem.id, {
        action_title: editingItem.action_title,
        description: editingItem.description,
        assignee: editingItem.assignee,
        jira_project_key: editingItem.jira_project_key,
        priority: editingItem.priority,
        due_date: editingItem.due_date,
        status: editingItem.status,
      });
      setItems(prev => prev.map(i => i.id === editingItem.id ? editingItem : i));
      setEditingItem(null);
    } catch (err) {
      alert(`Failed to save changes: ${err.message}`);
    }
  }

  const priorityStyles = {
    'Highest': { border: 'border-l-rose-500', badge: 'bg-rose-50 text-rose-700 border-rose-200' },
    'High': { border: 'border-l-orange-500', badge: 'bg-orange-50 text-orange-700 border-orange-200' },
    'Medium': { border: 'border-l-amber-400', badge: 'bg-amber-50 text-amber-700 border-amber-200' },
    'Low': { border: 'border-l-blue-400', badge: 'bg-blue-50 text-blue-700 border-blue-200' },
    'Lowest': { border: 'border-l-slate-400', badge: 'bg-slate-50 text-slate-700 border-slate-200' },
  };

  const statusStyles = {
    'Approved': 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    'Pending Review': 'bg-amber-50 text-amber-700 border-amber-200/80',
    'Needs Clarification': 'bg-indigo-50 text-indigo-700 border-indigo-200/80',
    'Rejected': 'bg-rose-50 text-rose-700 border-rose-200/80',
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">Action Items Workstation</h1>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                {items.length} Tasks
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Review, edit, and categorize AI-extracted tasks before pushing to Jira.
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center gap-2">
            <a
              href={api.exportCsvUrl}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </a>
            <a
              href={api.exportExcelUrl}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold transition-all"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
              <span>Export Excel</span>
            </a>
          </div>
        </div>

        {/* Faceted Filter Toolbar */}
        <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
          {/* Search bar */}
          <form onSubmit={handleSearchSubmit} className="relative sm:col-span-2 lg:col-span-2">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search title, description..."
              className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </form>

          {/* Project Filter */}
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="All">All Jira Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.project_key}>
                [{p.project_key}] {p.project_name}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="All">All Statuses</option>
            <option value="Pending Review">Pending Review</option>
            <option value="Approved">Approved</option>
            <option value="Needs Clarification">Needs Clarification</option>
            <option value="Rejected">Rejected</option>
          </select>

          {/* Priority Filter */}
          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="All">All Priorities</option>
            <option value="Highest">Highest</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
            <option value="Lowest">Lowest</option>
          </select>
        </div>
      </div>

      {/* Action Items List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-3 text-xs font-medium text-slate-500">Filtering action items...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <CheckCircle2 className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800">No action items found</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Try resetting your search query or filters, or process a new transcript.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const pStyle = priorityStyles[item.priority] || { border: 'border-l-slate-300', badge: 'bg-slate-50 text-slate-600 border-slate-200' };
            const sStyle = statusStyles[item.status] || 'bg-slate-50 text-slate-700 border-slate-200';
            const confidencePct = Math.round((item.confidence_score || 0.85) * 100);

            return (
              <div
                key={item.id}
                className={`bg-white rounded-xl p-5 border border-slate-200/80 border-l-4 ${pStyle.border} shadow-[0_1px_3px_rgba(0,0,0,0.02)] hover:shadow-md transition-all flex flex-col md:flex-row md:items-start justify-between gap-4`}
              >
                {/* Main Content */}
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Project key badge */}
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-50 border border-indigo-200/60 text-indigo-700">
                      {item.jira_project_key || 'UNASSIGNED'}
                    </span>

                    {/* Action Item Title */}
                    <h3 className="text-sm font-bold text-slate-900">{item.action_title}</h3>

                    {/* Priority Badge */}
                    {item.priority && (
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${pStyle.badge}`}>
                        {item.priority}
                      </span>
                    )}

                    {/* Status Pill */}
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${sStyle}`}>
                      {item.status}
                    </span>

                    {/* Action Type */}
                    {item.action_type && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600">
                        {item.action_type}
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-600 leading-relaxed">{item.description}</p>

                  {/* Metadata Chips: Assignee, Due Date, Meeting */}
                  <div className="flex items-center gap-4 text-xs text-slate-500 pt-1 flex-wrap">
                    <span className="flex items-center gap-1 font-medium">
                      <User className="w-3 h-3 text-slate-400" />
                      {item.assignee || 'Unassigned'}
                    </span>
                    {item.due_date && (
                      <span className="flex items-center gap-1 font-medium">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        Due: {item.due_date}
                      </span>
                    )}
                    {item.meeting_name && (
                      <span className="text-slate-400">
                        From: <span className="font-medium text-slate-600">{item.meeting_name}</span>
                      </span>
                    )}
                    <span className="text-[10px] text-indigo-600 font-semibold bg-indigo-50/80 px-2 py-0.5 rounded border border-indigo-100">
                      AI Confidence: {confidencePct}%
                    </span>
                  </div>

                  {/* Source Excerpt */}
                  {item.source_excerpt && (
                    <div className="mt-2 text-[11px] italic text-slate-500 bg-[#F8F9FA] p-2.5 rounded-lg border-l-2 border-indigo-400">
                      "{item.source_excerpt}"
                    </div>
                  )}

                  {/* Clarification reason if present */}
                  {item.clarification_reason && (
                    <div className="text-[11px] text-amber-700 bg-amber-50/70 p-2 rounded-lg border border-amber-200/60">
                      ⚠️ Needs Clarification: {item.clarification_reason}
                    </div>
                  )}
                </div>

                {/* Right Side Review Actions & Edit */}
                <div className="flex flex-row md:flex-col items-end gap-2 shrink-0 pt-1">
                  <div className="flex items-center gap-1">
                    <button
                      title="Approve"
                      onClick={() => handleStatusChange(item.id, 'Approved')}
                      className={`p-1.5 rounded-lg text-xs font-semibold transition-all ${
                        item.status === 'Approved'
                          ? 'bg-emerald-600 text-white'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200/60 hover:bg-emerald-100'
                      }`}
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      title="Needs Clarification"
                      onClick={() => handleStatusChange(item.id, 'Needs Clarification')}
                      className={`p-1.5 rounded-lg text-xs font-semibold transition-all ${
                        item.status === 'Needs Clarification'
                          ? 'bg-amber-600 text-white'
                          : 'bg-amber-50 text-amber-700 border border-amber-200/60 hover:bg-amber-100'
                      }`}
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                    </button>
                    <button
                      title="Reject"
                      onClick={() => handleStatusChange(item.id, 'Rejected')}
                      className={`p-1.5 rounded-lg text-xs font-semibold transition-all ${
                        item.status === 'Rejected'
                          ? 'bg-rose-600 text-white'
                          : 'bg-rose-50 text-rose-700 border border-rose-200/60 hover:bg-rose-100'
                      }`}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setEditingItem({ ...item })}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 border border-slate-200 transition-all text-xs"
                      title="Edit Item"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 transition-all text-xs"
                      title="Delete Item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Drawer Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Edit Action Item</h2>
              <button onClick={() => setEditingItem(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Action Title</label>
                <input
                  type="text"
                  value={editingItem.action_title || ''}
                  onChange={(e) => setEditingItem({ ...editingItem, action_title: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editingItem.description || ''}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assignee</label>
                  <input
                    type="text"
                    value={editingItem.assignee || ''}
                    onChange={(e) => setEditingItem({ ...editingItem, assignee: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Jira Project Key</label>
                  <select
                    value={editingItem.jira_project_key || ''}
                    onChange={(e) => setEditingItem({ ...editingItem, jira_project_key: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-white"
                  >
                    <option value="">None / Unassigned</option>
                    {projects.map((p) => (
                      <option key={p.id} value={p.project_key}>
                        [{p.project_key}] {p.project_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Priority</label>
                  <select
                    value={editingItem.priority || ''}
                    onChange={(e) => setEditingItem({ ...editingItem, priority: e.target.value })}
                    className="w-full px-2 py-1.5 rounded-lg border border-slate-200 bg-white"
                  >
                    <option value="Highest">Highest</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                    <option value="Lowest">Lowest</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Due Date</label>
                  <input
                    type="text"
                    placeholder="e.g. Friday"
                    value={editingItem.due_date || ''}
                    onChange={(e) => setEditingItem({ ...editingItem, due_date: e.target.value })}
                    className="w-full px-2 py-1.5 rounded-lg border border-slate-200"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Status</label>
                  <select
                    value={editingItem.status || 'Pending Review'}
                    onChange={(e) => setEditingItem({ ...editingItem, status: e.target.value })}
                    className="w-full px-2 py-1.5 rounded-lg border border-slate-200 bg-white"
                  >
                    <option value="Pending Review">Pending Review</option>
                    <option value="Approved">Approved</option>
                    <option value="Needs Clarification">Needs Clarification</option>
                    <option value="Rejected">Rejected</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingItem(null)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 shadow-sm"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
