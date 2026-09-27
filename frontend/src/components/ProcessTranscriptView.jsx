import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Upload, 
  Mic, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  Check, 
  X, 
  HelpCircle,
  FolderKanban,
  FileCode,
  Layers,
  ArrowRight
} from 'lucide-react';
import { api } from '../services/api';

export default function ProcessTranscriptView({ onNavigate }) {
  const [inputMode, setInputMode] = useState('paste'); // 'paste' | 'file' | 'audio'
  const [meetingName, setMeetingName] = useState('Weekly Engineering Architecture Sync');
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().split('T')[0]);
  const [transcriptText, setTranscriptText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  
  const [activeProjects, setActiveProjects] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [extractedResult, setExtractedResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const res = await api.getProjects(true);
      setActiveProjects(res.projects || []);
    } catch (err) {
      console.error('Failed to load active projects', err);
    }
  }

  // Pre-load sample transcript
  function handleLoadSample() {
    setMeetingName('Core Platform & Auth Architecture Review');
    setTranscriptText(`Alex: Good morning team. Let's review the critical tasks before next week's sprint.
Sarah: The React authentication modal currently doesn't refresh tokens on expiration. Alex, can you fix this token expiration bug in the frontend service by Thursday?
Alex: Yes, I will take care of that bug and submit a PR by Thursday.
David: We also noticed Redis memory pressure spiking during peak hours. Bob, you need to implement cache TTL key eviction in the core backend by Friday.
Bob: Got it, I am on it and will test TTL eviction under load by Friday.
Sarah: Should we also consider switching from Postgres to Mongo?
Alex: That's just a general idea for Q4, let's not create any tickets for that right now.
David: Maria, please set up Grafana alerting for CPU usage over 85% in Kubernetes by Monday.
Maria: Confirmed, I will configure the Kubernetes alerting rule by Monday.`);
  }

  async function handleProcess() {
    setErrorMessage(null);
    setExtractedResult(null);

    if (inputMode === 'paste') {
      if (!transcriptText.trim()) {
        setErrorMessage('Please enter or paste transcript text.');
        return;
      }
    } else {
      if (!selectedFile) {
        setErrorMessage('Please select a file to upload.');
        return;
      }
    }

    try {
      setIsProcessing(true);
      setProcessingStep(1);

      // Simulate smooth progress steps
      const stepTimer1 = setTimeout(() => setProcessingStep(2), 800);
      const stepTimer2 = setTimeout(() => setProcessingStep(3), 1600);
      const stepTimer3 = setTimeout(() => setProcessingStep(4), 2600);

      let response;
      if (inputMode === 'paste') {
        response = await api.processText({
          transcript_text: transcriptText,
          meeting_name: meetingName,
          meeting_date: meetingDate,
          source_type: 'paste',
        });
      } else {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('meeting_name', meetingName);
        formData.append('meeting_date', meetingDate);
        response = await api.processFile(formData);
      }

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);

      setProcessingStep(5);
      setExtractedResult(response);
    } catch (err) {
      setErrorMessage(err.message || 'Processing failed');
    } finally {
      setIsProcessing(false);
    }
  }

  async function handleQuickStatus(itemId, newStatus) {
    try {
      await api.updateStatus(itemId, newStatus);
      // update local state
      setExtractedResult(prev => ({
        ...prev,
        action_items: prev.action_items.map(item => 
          item.id === itemId ? { ...item, status: newStatus } : item
        )
      }));
    } catch (err) {
      alert(`Status update failed: ${err.message}`);
    }
  }

  const steps = [
    'Parsing & Validating Transcript',
    'Whisper Speech-to-Text (if audio)',
    'Groq AI Commitment vs Suggestion Filter',
    'Pydantic Schema Validation & Project Mapping',
    'Persisting Action Items in Supabase',
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Process Meeting Transcript</h1>
            <p className="text-xs text-slate-500 mt-1">
              Extract explicit commitments, map them to configured Jira projects, and review with confidence scores.
            </p>
          </div>

          <button
            onClick={handleLoadSample}
            className="self-start sm:self-auto px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition-all"
          >
            📋 Fill Sample Transcript
          </button>
        </div>

        {/* Active Jira Context Chips */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
            <FolderKanban className="w-3.5 h-3.5 text-indigo-600" />
            Active Jira Scopes ({activeProjects.length}):
          </span>
          {activeProjects.map((p) => (
            <span
              key={p.id}
              className="px-2 py-0.5 rounded-md bg-indigo-50 border border-indigo-200/60 text-indigo-700 text-[11px] font-semibold"
            >
              [{p.project_key}] {p.project_name}
            </span>
          ))}
          {activeProjects.length === 0 && (
            <span className="text-xs text-amber-600 italic">No Jira projects configured yet.</span>
          )}
        </div>
      </div>

      {/* Input Form Card */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] space-y-5">
        {/* Meeting metadata row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">Meeting Name *</label>
            <input
              type="text"
              value={meetingName}
              onChange={(e) => setMeetingName(e.target.value)}
              placeholder="e.g. Sprint Planning, Core Architecture Review"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Meeting Date *</label>
            <input
              type="date"
              value={meetingDate}
              onChange={(e) => setMeetingDate(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Input Format Selector Tabs */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-2">Transcript Source Input</label>
          <div className="flex items-center gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200 w-fit">
            <button
              type="button"
              onClick={() => setInputMode('paste')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                inputMode === 'paste'
                  ? 'bg-white text-indigo-600 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Paste Text</span>
            </button>
            <button
              type="button"
              onClick={() => setInputMode('file')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                inputMode === 'file'
                  ? 'bg-white text-indigo-600 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>File (.txt, .vtt, .srt)</span>
            </button>
            <button
              type="button"
              onClick={() => setInputMode('audio')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                inputMode === 'audio'
                  ? 'bg-white text-indigo-600 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Audio (Whisper V3)</span>
            </button>
          </div>
        </div>

        {/* Input Fields depending on mode */}
        {inputMode === 'paste' && (
          <div>
            <textarea
              rows={8}
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              placeholder="Paste speaker-annotated transcript discussion here...&#10;e.g.&#10;Alice: Can you update the auth API by Wednesday?&#10;Bob: Sure, I will complete that task by Wednesday."
              className="w-full p-3 rounded-xl border border-slate-200 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
            <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
              <span>{transcriptText.split(/\s+/).filter(Boolean).length} words</span>
              <span>Supported: plain text, timestamps, speaker tags</span>
            </div>
          </div>
        )}

        {(inputMode === 'file' || inputMode === 'audio') && (
          <div className="border-2 border-dashed border-slate-200 rounded-2xl p-6 text-center hover:border-indigo-400 transition-colors bg-slate-50/50">
            <Upload className="w-8 h-8 mx-auto text-indigo-600 mb-2" />
            <p className="text-xs font-semibold text-slate-700 mb-1">
              {inputMode === 'file' ? 'Upload .txt, .vtt, or .srt transcript' : 'Upload meeting audio file'}
            </p>
            <p className="text-[11px] text-slate-400 mb-3">
              {inputMode === 'file' ? 'Plain text, WebVTT subtitle, or SubRip SRT' : 'MP3, WAV, M4A, OGG up to 25MB'}
            </p>
            <input
              type="file"
              accept={inputMode === 'file' ? '.txt,.vtt,.srt' : '.mp3,.wav,.m4a,.ogg,.flac'}
              onChange={(e) => setSelectedFile(e.target.files[0])}
              className="text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
            {selectedFile && (
              <div className="mt-3 text-xs text-emerald-700 font-medium bg-emerald-50 py-1.5 px-3 rounded-lg inline-block border border-emerald-200">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </div>
            )}
          </div>
        )}

        {/* Error Callout */}
        {errorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Processing Step Indicator */}
        {isProcessing && (
          <div className="p-4 bg-indigo-50/60 border border-indigo-100 rounded-xl space-y-3">
            <div className="flex items-center justify-between text-xs font-semibold text-indigo-900">
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600 animate-spin" />
                Processing Transcript with Groq AI...
              </span>
              <span>Step {processingStep} of 5</span>
            </div>
            <div className="space-y-1.5">
              {steps.map((st, idx) => {
                const isDone = processingStep > idx + 1;
                const isCurrent = processingStep === idx + 1;
                return (
                  <div key={idx} className="flex items-center gap-2 text-xs">
                    {isDone ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    ) : isCurrent ? (
                      <div className="w-3.5 h-3.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin shrink-0"></div>
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full border border-slate-300 shrink-0"></div>
                    )}
                    <span className={isCurrent ? 'font-bold text-indigo-900' : isDone ? 'text-slate-600' : 'text-slate-400'}>
                      {st}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div>
          <button
            type="button"
            disabled={isProcessing}
            onClick={handleProcess}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isProcessing ? 'Synthesizing Action Items...' : 'Extract & Classify Action Items'}</span>
          </button>
        </div>
      </div>

      {/* Extracted Results Preview */}
      {extractedResult && (
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-[0_1px_3px_rgba(0,0,0,0.03)] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Extracted Action Items ({extractedResult.action_items?.length || 0})
                </h2>
                <p className="text-[11px] text-slate-500">
                  {extractedResult.is_duplicate 
                    ? 'Transcript already existed. Displaying previously saved items.'
                    : 'Saved to Supabase. Ready for your review.'}
                </p>
              </div>
            </div>

            <button
              onClick={() => onNavigate('action_items')}
              className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              <span>Open Workstation</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {extractedResult.action_items?.map((item) => {
              const priorityColors = {
                'Highest': 'border-rose-500 text-rose-700 bg-rose-50',
                'High': 'border-orange-500 text-orange-700 bg-orange-50',
                'Medium': 'border-amber-500 text-amber-700 bg-amber-50',
                'Low': 'border-blue-500 text-blue-700 bg-blue-50',
                'Lowest': 'border-slate-400 text-slate-700 bg-slate-50',
              };

              return (
                <div
                  key={item.id}
                  className="p-4 rounded-xl border border-slate-200/90 bg-[#FAFBFD] hover:border-slate-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-3"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-50 border border-indigo-200/60 text-indigo-700">
                        {item.jira_project_key || 'Unassigned'}
                      </span>
                      <span className="text-sm font-bold text-slate-800">{item.action_title}</span>
                      {item.priority && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${priorityColors[item.priority] || ''}`}>
                          {item.priority}
                        </span>
                      )}
                      <span className="text-[11px] font-medium text-slate-500">
                        👤 {item.assignee || 'Unassigned'}
                      </span>
                      {item.due_date && (
                        <span className="text-[11px] font-medium text-slate-500">
                          📅 {item.due_date}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-600">{item.description}</p>

                    {item.source_excerpt && (
                      <div className="text-[11px] italic text-slate-500 bg-slate-100/70 p-2 rounded-lg border-l-2 border-indigo-400">
                        "{item.source_excerpt}"
                      </div>
                    )}
                  </div>

                  {/* Review Actions */}
                  <div className="flex items-center gap-1.5 self-end md:self-center shrink-0">
                    <button
                      onClick={() => handleQuickStatus(item.id, 'Approved')}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all ${
                        item.status === 'Approved'
                          ? 'bg-emerald-600 text-white shadow-sm'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200/60 hover:bg-emerald-100'
                      }`}
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={() => handleQuickStatus(item.id, 'Needs Clarification')}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all ${
                        item.status === 'Needs Clarification'
                          ? 'bg-amber-600 text-white shadow-sm'
                          : 'bg-amber-50 text-amber-700 border border-amber-200/60 hover:bg-amber-100'
                      }`}
                    >
                      <HelpCircle className="w-3.5 h-3.5" />
                      <span>Clarify</span>
                    </button>
                    <button
                      onClick={() => handleQuickStatus(item.id, 'Rejected')}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all ${
                        item.status === 'Rejected'
                          ? 'bg-rose-600 text-white shadow-sm'
                          : 'bg-rose-50 text-rose-700 border border-rose-200/60 hover:bg-rose-100'
                      }`}
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
