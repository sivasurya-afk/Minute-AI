import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardView from './components/DashboardView';
import ProcessTranscriptView from './components/ProcessTranscriptView';
import ActionItemsView from './components/ActionItemsView';
import JiraProjectsView from './components/JiraProjectsView';
import TranscriptHistoryView from './components/TranscriptHistoryView';
import SettingsView from './components/SettingsView';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [user, setUser] = useState({
    id: '00000000-0000-0000-0000-000000000001',
    email: 'demo@minute.ai',
    full_name: 'Demo User',
    is_demo: true,
  });

  useEffect(() => {
    // Auto-login to demo mode if no token
    const token = localStorage.getItem('minute_ai_token');
    if (!token) {
      api.demoLogin().then((res) => {
        localStorage.setItem('minute_ai_token', res.token);
        setUser(res.user);
      }).catch(console.error);
    }
  }, []);

  function handleLogout() {
    localStorage.removeItem('minute_ai_token');
    api.demoLogin().then((res) => {
      localStorage.setItem('minute_ai_token', res.token);
      setUser(res.user);
      setActiveTab('dashboard');
    });
  }

  return (
    <div className="min-h-screen bg-[#F0F2F5] text-slate-800 flex flex-col selection:bg-indigo-100 selection:text-indigo-800">
      {/* Top Sticky Navigation */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        user={user} 
        onLogout={handleLogout} 
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'dashboard' && <DashboardView onNavigate={setActiveTab} />}
        {activeTab === 'process' && <ProcessTranscriptView onNavigate={setActiveTab} />}
        {activeTab === 'action_items' && <ActionItemsView />}
        {activeTab === 'projects' && <JiraProjectsView />}
        {activeTab === 'history' && <TranscriptHistoryView onNavigate={setActiveTab} />}
        {activeTab === 'settings' && <SettingsView />}
      </main>

      {/* Subtle Minimal Footer */}
      <footer className="border-t border-[#E2E8F0] bg-[#F8F9FA] py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700">Minute AI</span>
            <span>•</span>
            <span>Groq LPU Inference & Supabase PostgreSQL</span>
          </div>
          <div className="text-[11px] text-slate-400">
            Initial Phase: Human-in-the-Loop Review (No direct ticket mutations)
          </div>
        </div>
      </footer>
    </div>
  );
}
