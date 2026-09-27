import React, { useState, useEffect } from 'react';
import { 
  FolderKanban, 
  Plus, 
  Search, 
  Edit3, 
  Trash2, 
  Check, 
  X, 
  Tag, 
  Users, 
  ShieldCheck 
} from 'lucide-react';
import { api } from '../services/api';

export default function JiraProjectsView() {
  const [projects, setProjects] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    project_name: '',
    project_key: '',
    description: '',
    team_name: 'General',
    keywords_str: '',
    is_active: true,
  });

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setLoading(true);
      const res = await api.getProjects();
      setProjects(res.projects || []);
    } catch (err) {
      console.error('Failed to load projects', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleActive(p) {
    try {
      const newStatus = !p.is_active;
      await api.toggleProject(p.id, newStatus);
      setProjects(prev => prev.map(item => item.id === p.id ? { ...item, is_active: newStatus } : item));
    } catch (err) {
      alert(`Toggle failed: ${err.message}`);
    }
  }

  async function handleDelete(id) {
    if (!confirm('Are you sure you want to delete this Jira project context?')) return;
    try {
      await api.deleteProject(id);
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!formData.project_name.trim() || !formData.project_key.trim()) {
      alert('Project Name and Key are required.');
      return;
    }

    try {
      const kw = formData.keywords_str.split(',').map(s => s.trim()).filter(Boolean);
      await api.createProject({
        project_name: formData.project_name,
        project_key: formData.project_key.toUpperCase(),
        description: formData.description,
        team_name: formData.team_name,
        keywords: kw,
        is_active: formData.is_active,
      });
      setIsAddModalOpen(false);
      setFormData({ project_name: '', project_key: '', description: '', team_name: 'General', keywords_str: '', is_active: true });
      loadProjects();
    } catch (err) {
      alert(`Failed to add project: ${err.message}`);
    }
  }

  async function handleUpdate(e) {
    e.preventDefault();
    if (!editingProject) return;

    try {
      const kw = (editingProject.keywords_str || '').split(',').map(s => s.trim()).filter(Boolean);
      await api.updateProject(editingProject.id, {
        project_name: editingProject.project_name,
        description: editingProject.description,
        team_name: editingProject.team_name,
        keywords: kw,
        is_active: editingProject.is_active,
      });
      setEditingProject(null);
      loadProjects();
    } catch (err) {
      alert(`Failed to update project: ${err.message}`);
    }
  }

  const filtered = projects.filter(p => {
    const q = search.toLowerCase();
    return (
      p.project_name?.toLowerCase().includes(q) ||
      p.project_key?.toLowerCase().includes(q) ||
      p.team_name?.toLowerCase().includes(q) ||
      (p.keywords || []).some(k => k.toLowerCase().includes(q))
    );
  });

  const activeCount = projects.filter(p => p.is_active).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Jira Projects Registry</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              {activeCount} of {projects.length} Active Contexts
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Configure target Jira projects that provide semantic context for AI task classification.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Project</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-[0_1px_2px_rgba(0,0,0,0.02)] flex items-center gap-2">
        <Search className="w-4 h-4 text-slate-400 ml-1" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by project key, name, team, or keywords..."
          className="w-full text-xs text-slate-800 placeholder-slate-400 focus:outline-none"
        />
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[300px]">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
          <FolderKanban className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-800">No Jira projects match query</h3>
          <p className="text-xs text-slate-500 mt-1">Click "Register New Project" to add a Jira classification target.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((p) => (
            <div
              key={p.id}
              className={`bg-white rounded-xl p-5 border ${
                p.is_active ? 'border-slate-200/90' : 'border-slate-200/50 opacity-75'
              } shadow-[0_1px_3px_rgba(0,0,0,0.02)] hover:shadow-md transition-all flex flex-col justify-between space-y-4`}
            >
              <div>
                {/* Header row: Key, Title, Toggle */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-md font-bold font-mono text-xs bg-indigo-50 border border-indigo-200/60 text-indigo-700">
                      {p.project_key}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 leading-snug">{p.project_name}</h3>
                  </div>

                  <button
                    onClick={() => handleToggleActive(p)}
                    className={`w-8 h-4 rounded-full transition-colors relative ${
                      p.is_active ? 'bg-indigo-600' : 'bg-slate-300'
                    }`}
                    title={p.is_active ? 'Active Context' : 'Inactive Context'}
                  >
                    <span
                      className={`block w-3 h-3 rounded-full bg-white shadow-sm transition-transform ${
                        p.is_active ? 'translate-x-4' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mb-2">
                  <Users className="w-3 h-3 text-slate-400" />
                  <span>Team: <b className="text-slate-700">{p.team_name || 'General'}</b></span>
                </div>

                <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed mb-3">
                  {p.description || 'No description provided.'}
                </p>

                {/* Keywords Chips */}
                {(p.keywords || []).length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {p.keywords.map((kw, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-600 font-medium"
                      >
                        #{kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                <span className={`text-[11px] font-semibold ${p.is_active ? 'text-emerald-600' : 'text-slate-400'}`}>
                  {p.is_active ? '● AI Classification Active' : '○ Context Disabled'}
                </span>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setEditingProject({ ...p, keywords_str: (p.keywords || []).join(', ') })}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 border border-slate-200"
                    title="Edit Details"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(p.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200"
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Register Project Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Register Jira Project Context</h2>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-3 text-xs">
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block font-semibold text-slate-700 mb-1">Project Name *</label>
                  <input
                    type="text"
                    placeholder="e.g. Core Authentication Service"
                    value={formData.project_name}
                    onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                    required
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Project Key *</label>
                  <input
                    type="text"
                    placeholder="e.g. AUTH"
                    value={formData.project_key}
                    onChange={(e) => setFormData({ ...formData, project_key: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 font-mono uppercase"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Scope & Technical Responsibilities *</label>
                <textarea
                  rows={3}
                  placeholder="Detail the technical domain so the AI accurately matches tasks..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Team / Squad</label>
                  <input
                    type="text"
                    placeholder="e.g. Identity Squad"
                    value={formData.team_name}
                    onChange={(e) => setFormData({ ...formData, team_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Keywords (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="auth, oauth, login, jwt"
                    value={formData.keywords_str}
                    onChange={(e) => setFormData({ ...formData, keywords_str: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="active_cb"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded text-indigo-600"
                />
                <label htmlFor="active_cb" className="text-slate-700 font-medium">
                  Enable for AI action item classification
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 shadow-sm"
                >
                  Register Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingProject && (
        <div className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Modify Project [{editingProject.project_key}]</h2>
              <button onClick={() => setEditingProject(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpdate} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Project Name</label>
                <input
                  type="text"
                  value={editingProject.project_name || ''}
                  onChange={(e) => setEditingProject({ ...editingProject, project_name: e.target.value })}
                  className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Scope & Description</label>
                <textarea
                  rows={3}
                  value={editingProject.description || ''}
                  onChange={(e) => setEditingProject({ ...editingProject, description: e.target.value })}
                  className="w-full p-2.5 rounded-lg border border-slate-200"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Team</label>
                  <input
                    type="text"
                    value={editingProject.team_name || ''}
                    onChange={(e) => setEditingProject({ ...editingProject, team_name: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Keywords</label>
                  <input
                    type="text"
                    value={editingProject.keywords_str || ''}
                    onChange={(e) => setEditingProject({ ...editingProject, keywords_str: e.target.value })}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingProject(null)}
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
