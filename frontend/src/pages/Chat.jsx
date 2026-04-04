import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send, Plus, CheckCircle, AlertCircle, ArrowRight,
  PauseCircle, Terminal, Loader, Zap, Menu, ChevronDown, Sparkles, ExternalLink, XCircle
} from 'lucide-react';
import { notify } from '../components/Notification';

// ─── Config ──────────────────────────────────────────────────────────────────
const API_URL = import.meta.env.VITE_API_URL || "";
const API_KEY = import.meta.env.VITE_API_KEY || "nagent-dev-key";
const WS_URL  = import.meta.env.VITE_WS_URL  || "";

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { "Authorization": `Bearer ${token}` } : {};
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
const STATUS_MAP = {
  completed: { color: '#10B981', label: 'Completed' },
  running:   { color: '#FFFFFF', label: 'Running'   },
  analyzing: { color: '#0066FF', label: 'Analysing' },
  executing: { color: '#FF8A00', label: 'Executing' },
  failed:    { color: '#EF4444', label: 'Failed'    },
};

const PERF_META = {
  inform:    { label: 'RESULT',      border: '#FFFFFF', Icon: CheckCircle },
  failure:   { label: 'FAILURE',     border: '#EF4444', Icon: AlertCircle },
  hibernate: { label: 'NEEDS INPUT', border: '#FF8A00', Icon: PauseCircle },
  request:   { label: 'REQUEST',     border: '#0066FF', Icon: ArrowRight  },
  default:   { label: 'EVENT',       border: '#71717A', Icon: Terminal    },
};

function fmtTime(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ─── SessionItem ──────────────────────────────────────────────────────────────
function SessionItem({ session, active, onClick }) {
  const s = STATUS_MAP[session.status] || STATUS_MAP.completed;
  return (
    <motion.button
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      onClick={onClick}
      className={`w-full text-left p-4 rounded-[16px] border transition-all duration-300 relative overflow-hidden ${
        active
          ? 'bg-[#1A1A1A] border-white/30 shadow-[0_0_18px_rgba(255,255,255,0.06)]'
          : 'bg-[#0E0E0E] border-white/[0.06] hover:border-white/20 hover:bg-[#141414]'
      }`}
    >
      {active && (
        <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-white shadow-[0_0_8px_#FFFFFF] rounded-l-[16px]" />
      )}
      <p className={`font-mono text-[10px] mb-1.5 truncate ${active ? 'text-white' : 'text-[#71717A]'}`}>
        {session.id.slice(0, 22)}…
      </p>
      <p className="text-sm font-medium text-white leading-snug line-clamp-2 mb-3">{session.name}</p>
      <div className="flex items-center justify-between">
        <span
          className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border"
          style={{ color: s.color, borderColor: `${s.color}40`, background: `${s.color}10` }}
        >
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color, boxShadow: `0 0 4px ${s.color}` }} />
          {s.label}
        </span>
        <span className="font-mono text-[10px] text-[#71717A]">{session.ts}</span>
      </div>
    </motion.button>
  );
}

// ─── EventCard ─────────────────────────────────────────────────────────────────
function EventCard({ event }) {
  const meta = PERF_META[event.performative] || PERF_META.default;
  const Icon = meta.Icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[16px] border p-5 relative overflow-hidden"
      style={{ background: '#0E0E0E', borderColor: `${meta.border}25` }}
    >
      <div
        className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-[16px]"
        style={{ background: meta.border, boxShadow: `0 0 8px ${meta.border}` }}
      />
      <div className="pl-2">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-lg bg-white/[0.04] border border-white/[0.06]">
            <Icon size={13} style={{ color: meta.border }} />
          </div>
          <span
            className="text-[9px] font-bold uppercase tracking-[0.12em] px-2 py-0.5 rounded-full border"
            style={{ color: meta.border, borderColor: `${meta.border}40`, background: `${meta.border}10` }}
          >
            {meta.label}
          </span>
          <span className="font-mono text-[10px] text-[#71717A] ml-auto">{fmtTime(event.timestamp)}</span>
        </div>
        <p className="font-mono text-[10px] text-[#71717A] mb-2 truncate">{event.sender_id}</p>
        <div className="text-sm text-[#E2E8F0] leading-relaxed">
          <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{event.payload?.natural_language || ''}</ReactMarkdown></div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── HibernatePrompt ───────────────────────────────────────────────────────────
function HibernatePrompt({ event, onSubmit }) {
  const [text, setText]         = useState('');
  const [busy, setBusy]         = useState(false);

  const handleSubmit = async () => {
    if (!text.trim()) return;
    setBusy(true);
    await onSubmit(event.thread_id, text);
    setBusy(false);
    setText('');
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-[20px] border border-[#FF8A00]/40 p-6 relative overflow-hidden"
      style={{ background: 'linear-gradient(135deg, rgba(255,138,0,0.06), #0E0E0E)' }}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{ background: 'radial-gradient(circle at top right, rgba(255,138,0,0.07), transparent 60%)' }}
      />
      <div className="relative">
        <div className="flex items-center gap-2 mb-3">
          <PauseCircle size={15} className="text-[#FF8A00]" />
          <span className="text-[10px] font-bold text-[#FF8A00] uppercase tracking-widest">
            Agent Awaiting Input
          </span>
        </div>
        <p className="font-mono text-[10px] text-[#71717A] mb-3">{event.sender_id} · {event.thread_id}</p>
        <div className="text-sm text-[#E2E8F0] leading-relaxed mb-5">
          <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{event.payload?.natural_language || ''}</ReactMarkdown></div>
        </div>
        <div className="flex gap-3">
          <input
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            placeholder="Type your response…"
            className="flex-grow bg-[#1A1A1A] border border-white/10 rounded-full px-4 py-2.5 text-sm text-white placeholder-[#71717A] focus:outline-none focus:border-[#FF8A00]/50 transition-colors"
          />
          <button
            onClick={handleSubmit}
            disabled={!text.trim() || busy}
            className="px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-300 disabled:opacity-40"
            style={{ background: '#FF8A00', color: '#000' }}
          >
            {busy ? <Loader size={15} className="animate-spin" /> : 'Send'}
          </button>
        </div>
      </div>
    </motion.div>
  );
}

// ─── EmptyState ───────────────────────────────────────────────────────────────
function EmptyState({ onQuickStart }) {
  const suggestions = [
    'Research the top 5 competitors to Stripe and summarise their pricing models',
    'Write and review a Python function that validates ISO 8601 timestamps',
    'Draft a professional reply to a customer complaint about a late delivery',
  ];
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8 pb-20">
      <div className="relative w-24 h-24 mb-8">
        <div className="absolute inset-0 rounded-full bg-gradient-to-br from-white/20 to-[#FF8A00]/10 blur-2xl" />
        <div className="relative w-24 h-24 rounded-full bg-[#0E0E0E] border border-white/10 flex items-center justify-center">
          <Zap size={32} className="text-white" />
        </div>
      </div>
      <h2 className="text-2xl font-bold text-white mb-3 tracking-tight">Create your first workflow</h2>
      <p className="text-[#A1A1AA] text-sm max-w-sm leading-relaxed mb-10">
        Describe a complex objective. Tangent will architect, spawn, and orchestrate
        specialist AI agents to complete it — then dissolve without a trace.
      </p>
      <div className="grid grid-cols-1 gap-3 w-full max-w-md">
        {suggestions.map((q) => (
          <button
            key={q}
            onClick={() => onQuickStart(q)}
            className="text-left p-4 rounded-[14px] bg-[#0E0E0E] border border-white/[0.06] hover:border-white/30 hover:bg-[#141414] transition-all duration-300 group"
          >
            <span className="text-sm text-[#A1A1AA] group-hover:text-white transition-colors leading-relaxed">{q}</span>
            <ArrowRight size={13} className="inline ml-2 text-[#71717A] group-hover:text-white transition-colors" />
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Chat (page) ──────────────────────────────────────────────────────────────
export default function Chat() {
  const [sessions,     setSessions]     = useState([]);
  const [activeId,     setActiveId]     = useState(null);
  const [eventMap,     setEventMap]     = useState({});
  const [objective,    setObjective]    = useState('');
  const [provider,     setProvider]     = useState('google');
  const [model,        setModel]        = useState('gemini-3.1-flash-lite-preview');
  const [submitting,   setSubmitting]   = useState(false);
  const [demoMode,     setDemoMode]     = useState(false);
  const [showSidebar,  setShowSidebar]  = useState(false);

  const wsRef            = useRef(null);
  const scrollRef        = useRef(null);
  const textareaRef      = useRef(null);
  const newSessionIds    = useRef(new Set());
  const navigate         = useNavigate();

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [eventMap, activeId]);

  // Initial Fetch Sessions
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch(`${API_URL}/workflows`, { headers: getAuthHeaders() });
        if (res.ok) {
          const data = await res.json();
          const loadedSessions = data.map(d => ({
            id: d.session_id,
            name: d.original_objective?.slice(0, 60) || 'Untitled',
            status: d.status,
            ts: d.timestamp ? fmtTime(d.timestamp) : ''
          }));
          setSessions(loadedSessions);
        }
      } catch (err) {
        console.error("Failed to load sessions", err);
      }
    };
    fetchSessions();
  }, []);

  // Fetch history for active session if not populated
  useEffect(() => {
    if (activeId && !newSessionIds.current.has(activeId) && !eventMap[activeId]) {
      const fetchHistory = async () => {
        try {
          const res = await fetch(`${API_URL}/workflows/${activeId}`, { headers: getAuthHeaders() });
          if (res.ok) {
            const data = await res.json();
            setEventMap(prev => ({ ...prev, [activeId]: data.logs || [] }));
          }
        } catch (err) {
          console.error("Failed to load history", err);
        }
      };
      fetchHistory();
    }
  }, [activeId]);

  const connectWS = useCallback((sessionId) => {
    if (wsRef.current) {
      wsRef.current.onmessage = null;
      wsRef.current.close();
    }
    const wsUrl = WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;
    const ws = new WebSocket(
      `${wsUrl}/workflows/${sessionId}/events?api_key=${API_KEY}`
    );
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type !== 'notification') {
        setEventMap(prev => ({ ...prev, [sessionId]: [...(prev[sessionId] || []), msg] }));
      }
      if (msg.performative === 'failure') {
        setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status: 'failed' } : s));
        const errorText = msg.type === 'notification' ? msg.message : msg.payload?.natural_language;
        notify(errorText || 'A fatal workflow error occurred', 'error', 10000);
      } else if (msg.performative === 'completed') {
        setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status: 'completed' } : s));
      }
    };
    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, []);

  // Close WS on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.onmessage = null;
        wsRef.current.close();
      }
    };
  }, []);

  const submitObjective = async () => {
    const text = objective.trim();
    if (!text || submitting) return;
    setSubmitting(true);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const res = await fetch(`${API_URL}/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ objective: text, provider, model }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (!res.ok) throw new Error('non-2xx');
      const data = await res.json();
      const session = {
        id: data.session_id, name: text.slice(0, 60),
        status: 'analyzing',
        ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      newSessionIds.current.add(data.session_id);
      setSessions(prev => [session, ...prev]);
      setEventMap(prev => ({ ...prev, [data.session_id]: [] }));
      setActiveId(data.session_id);
      setObjective('');
      connectWS(data.session_id);
      setDemoMode(false);
    } catch (err) {
      clearTimeout(timeout);
      const msg = err.name === 'AbortError' ? 'Request timed out — backend may be unavailable' : err.message;
      console.error("Backend unavailable - Submission failed:", err);
      notify(`Workflow Submission Failed: ${msg}`, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const submitHumanInput = async (taskId, input) => {
    if (!activeId) return;
    try {
      await fetch(`${API_URL}/workflows/${activeId}/input`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ task_id: taskId, input }),
      });
    } catch (err) {
      console.warn('Human input submit failed (demo mode?):', err);
    }
  };

  const cancelWorkflow = async () => {
    if (!activeId) return;
    try {
      const res = await fetch(`${API_URL}/workflows/${activeId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() }
      });
      if (res.ok) {
        notify('Workflow cancellation requested', 'info');
      } else {
        const data = await res.json();
        notify(data.message || 'Failed to cancel workflow', 'error');
      }
    } catch (err) {
      console.error('Cancellation failed:', err);
      notify('Failed to cancel workflow', 'error');
    }
  };

  const activeSession = sessions.find(s => s.id === activeId);
  const activeEvents  = eventMap[activeId] || [];
  const statusMeta    = STATUS_MAP[activeSession?.status] || STATUS_MAP.completed;

  return (
    /* Escape Layout padding to get full-height split pane */
    <div className="-mx-4 sm:-mx-6 flex h-[calc(100dvh-12rem)] md:h-[calc(100vh-8rem)] overflow-hidden font-sans relative">

      {/* Mobile backdrop */}
      {showSidebar && (
        <div
          className="md:hidden fixed inset-0 bg-black/60 z-[120] backdrop-blur-sm"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className={`
        fixed md:relative top-0 left-0 h-full z-[130] md:z-auto
        w-[280px] sm:w-72 flex-shrink-0 flex flex-col
        border-r border-white/[0.06] bg-[#050505]
        transition-transform duration-300 ease-in-out
        ${showSidebar ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="px-5 py-5 border-b border-white/[0.06]">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest">Workflows</span>
            <button
              onClick={() => { setActiveId(null); setObjective(''); setShowSidebar(false); textareaRef.current?.focus(); }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white hover:bg-gray-200 text-black text-[10px] font-bold transition-colors shadow-[0_0_12px_rgba(255,255,255,0.2)]"
            >
              <Plus size={11} /> New
            </button>
          </div>
          <p className="text-[11px] text-[#71717A] mt-2">{sessions.length} session{sessions.length !== 1 ? 's' : ''}</p>
        </div>

        <div className="flex-grow overflow-y-auto p-3 space-y-2">
          <AnimatePresence>
            {sessions.map(s => (
              <SessionItem
                key={s.id}
                session={s}
                active={activeId === s.id}
                onClick={() => { setActiveId(s.id); setShowSidebar(false); }}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Connection status */}
        <div className="px-5 py-4 border-t border-white/[0.06]">
          <div className={`flex items-center gap-2 px-3 py-2 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
            demoMode
              ? 'bg-[#FF8A00]/10 border-[#FF8A00]/20 text-[#FF8A00]'
              : 'bg-[#10B981]/10 border-[#10B981]/20 text-[#10B981]'
          }`}>
            <span className={`w-2 h-2 rounded-full animate-pulse ${demoMode ? 'bg-[#FF8A00]' : 'bg-[#10B981]'}`} />
            {demoMode ? 'Demo Mode' : 'Live'}
          </div>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────────────────── */}
      <div className="flex-grow flex flex-col bg-[#000] overflow-hidden min-w-0">

        {/* Mobile top bar — always visible on mobile */}
        <div className="md:hidden h-12 border-b border-white/[0.06] px-4 flex items-center gap-3 bg-black/80 backdrop-blur-xl flex-shrink-0">
          <button
            onClick={() => setShowSidebar(true)}
            className="p-1.5 rounded-lg hover:bg-white/10 text-[#71717A] hover:text-white transition-colors flex-shrink-0"
            aria-label="Open workflows"
          >
            <Menu size={16} />
          </button>
          {activeSession ? (
            <>
              <span className="font-mono text-[10px] text-[#71717A] truncate flex-grow">{activeSession.name}</span>
              <button 
                onClick={() => navigate(`/workspace?taskId=${activeSession.id}`)}
                className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border flex-shrink-0 text-white border-white/20 bg-white/5 hover:bg-white/10 transition-colors"
                title="View in Workspace"
              >
                <ExternalLink size={12} />
                Workspace
              </button>
              <span
                className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border flex-shrink-0"
                style={{ color: statusMeta.color, borderColor: `${statusMeta.color}40`, background: `${statusMeta.color}10` }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: statusMeta.color }} />
                {statusMeta.label}
              </span>
              {(activeSession.status === 'analyzing' || activeSession.status === 'executing' || activeSession.status === 'running') && (
                <button
                  onClick={cancelWorkflow}
                  className="flex items-center justify-center p-1.5 rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] hover:bg-[#EF4444]/20 transition-all"
                  title="Cancel Execution"
                >
                  <XCircle size={15} />
                </button>
              )}
            </>
          ) : (
            <span className="text-[11px] text-[#71717A]">No workflow selected</span>
          )}
        </div>

        {/* Desktop workflow header */}
        {activeSession && (
          <div className="hidden md:flex h-14 border-b border-white/[0.06] px-8 items-center gap-3 bg-black/80 backdrop-blur-xl flex-shrink-0">
            <Terminal size={13} className="text-[#71717A] flex-shrink-0" />
            <span className="font-mono text-[10px] text-[#71717A] truncate">{activeSession.id}</span>
            <span className="text-[#71717A] hidden lg:inline">·</span>
            <span className="text-sm font-medium text-white truncate flex-grow hidden lg:inline">{activeSession.name}</span>
              <button 
                onClick={() => navigate(`/workspace?taskId=${activeSession.id}`)}
                className="ml-auto mr-2 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full border flex-shrink-0 text-white border-white/20 bg-white/5 hover:bg-white/10 transition-colors"
              >
                <ExternalLink size={12} />
                View in Workspace
              </button>
              <span
                className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full border flex-shrink-0"
                style={{ color: statusMeta.color, borderColor: `${statusMeta.color}40`, background: `${statusMeta.color}10` }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: statusMeta.color }} />
                {statusMeta.label}
              </span>
              {(activeSession.status === 'analyzing' || activeSession.status === 'executing' || activeSession.status === 'running') && (
                <button
                  onClick={cancelWorkflow}
                  className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] hover:bg-[#EF4444]/20 transition-all"
                >
                  <XCircle size={12} />
                  Cancel
                </button>
              )}
          </div>
        )}

        {/* Event feed */}
        <div ref={scrollRef} className="flex-grow overflow-y-auto px-4 sm:px-8 py-5 sm:py-8 space-y-4">
          {!activeId ? (
            <EmptyState onQuickStart={(q) => { setObjective(q); textareaRef.current?.focus(); }} />
          ) : activeEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full pb-20">
              <Loader size={22} className="text-white animate-spin mb-4" />
              <p className="text-sm text-[#71717A]">Orchestrating agents…</p>
            </div>
          ) : (
            <AnimatePresence initial={false}>
              {activeEvents.map((evt, i) =>
                evt.performative === 'hibernate' ? (
                  <HibernatePrompt key={evt.id ?? i} event={evt} onSubmit={submitHumanInput} />
                ) : (
                  <EventCard key={evt.id ?? i} event={evt} />
                )
              )}
            </AnimatePresence>
          )}
        </div>

        {/* Objective input bar */}
        <div className="flex-shrink-0 px-4 sm:px-8 py-4 sm:py-5 border-t border-white/[0.06] bg-[#000]/90 backdrop-blur-xl">
          <div className="max-w-3xl mx-auto">
            <div className="relative rounded-[20px] bg-[#141414] border border-white/[0.08] focus-within:border-white/[0.18] transition-all duration-200 shadow-[0_4px_24px_rgba(0,0,0,0.5)] focus-within:shadow-[0_0_0_3px_rgba(255,255,255,0.04),0_4px_24px_rgba(0,0,0,0.5)]">
              <textarea
                ref={textareaRef}
                rows={1}
                value={objective}
                onChange={e => setObjective(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitObjective(); } }}
                placeholder="How can Tangent help you today?"
                className="w-full resize-none bg-transparent text-sm text-white placeholder-[#4A4A4A] focus:outline-none leading-relaxed max-h-36 overflow-y-auto px-5 pt-4 pb-14"
              />
              <div className="absolute bottom-0 left-0 right-0 px-3 pb-3 flex items-center justify-between">
                <div className="relative group">
                  <div className="absolute inset-y-0 left-2.5 flex items-center pointer-events-none">
                    <Sparkles size={10} className="text-[#FF8A00]/70" />
                  </div>
                  <select
                    value={`${provider}:${model}`}
                    onChange={e => {
                      const [p, m] = e.target.value.split(':');
                      setProvider(p);
                      setModel(m);
                    }}
                    className="appearance-none bg-transparent hover:bg-white/[0.04] text-[#555] hover:text-[#999] text-[11px] font-medium rounded-lg pl-6 pr-6 py-1.5 outline-none transition-all duration-200 cursor-pointer"
                  >
                    <option value="google:gemini-3.1-flash-lite-preview" className="bg-[#141414] text-white">Gemini 3.1 Flash Lite</option>
                    <option value="openai:gpt-4o" className="bg-[#141414] text-white">GPT-4o</option>
                    <option value="anthropic:claude-3-5-sonnet-latest" className="bg-[#141414] text-white">Claude 3.5 Sonnet</option>
                  </select>
                  <div className="absolute inset-y-0 right-1.5 flex items-center pointer-events-none">
                    <ChevronDown size={9} className="text-[#444] group-hover:text-[#777] transition-colors duration-200" />
                  </div>
                </div>
                <button
                  onClick={submitObjective}
                  disabled={!objective.trim() || submitting}
                  className="flex items-center justify-center w-8 h-8 rounded-[10px] transition-all duration-200 disabled:cursor-not-allowed"
                  style={{
                    background: objective.trim() && !submitting ? '#FF8A00' : 'rgba(255,255,255,0.06)',
                    boxShadow: objective.trim() && !submitting ? '0 0 16px rgba(255,138,0,0.35)' : 'none',
                  }}
                >
                  {submitting
                    ? <Loader size={14} className="animate-spin text-white" />
                    : <Send size={14} className={objective.trim() ? 'text-black' : 'text-[#444]'} style={{ transform: 'translate(1px, -1px)' }} />
                  }
                </button>
              </div>
            </div>
            <p className="text-center text-[10px] text-[#2A2A2A] mt-2 font-mono tracking-wide">
              Enter ↵ to send · Shift+Enter for newline
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
