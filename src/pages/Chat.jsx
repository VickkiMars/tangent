import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Plus, CheckCircle, AlertCircle, ArrowRight,
  PauseCircle, Terminal, Loader, Zap, Menu,
} from 'lucide-react';

// ─── Config ──────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000';
const API_KEY  = 'nagent-dev-key';

// ─── Mock data (demo mode when backend is unreachable) ────────────────────────
const MOCK_SESSIONS = [
  { id: 'mock_refund',  name: 'Process refund for order ORD-9876',  status: 'completed', ts: '10:15 AM' },
  { id: 'mock_market',  name: 'Analyse Q4 APAC market trends',       status: 'running',   ts: '09:32 AM' },
  { id: 'mock_docs',    name: 'Generate API technical documentation', status: 'failed',    ts: '08:01 AM' },
];

const MOCK_EVENTS = [
  { id: 'm1', performative: 'inform',  sender_id: 'order_lookup.47a9f3',        thread_id: 'task_lookup',  timestamp: 1740480900, payload: { natural_language: 'Order ORD-9876 found. Item: Wireless Headphones · $299.99. Return eligible: ✓' } },
  { id: 'm2', performative: 'inform',  sender_id: 'refund_processor.b8e4d1',    thread_id: 'task_refund',  timestamp: 1740480907, payload: { natural_language: 'Refund processed. ID: ref_789012. $299.99 returned to original payment method.' } },
  { id: 'm3', performative: 'inform',  sender_id: 'notification_sender.c2f5a7', thread_id: 'task_notify',  timestamp: 1740480912, payload: { natural_language: 'Confirmation email dispatched to john.doe@example.com.' } },
];

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
        <p className="text-sm text-[#E2E8F0] leading-relaxed">{event.payload?.natural_language}</p>
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
        <p className="text-sm text-[#E2E8F0] leading-relaxed mb-5">{event.payload?.natural_language}</p>
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
      <h2 className="text-2xl font-bold text-white mb-3 tracking-tight">Deploy your first workflow</h2>
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
  const [sessions,     setSessions]     = useState(MOCK_SESSIONS);
  const [activeId,     setActiveId]     = useState(null);
  const [eventMap,     setEventMap]     = useState({ mock_refund: MOCK_EVENTS });
  const [objective,    setObjective]    = useState('');
  const [provider,     setProvider]     = useState('openai');
  const [model,        setModel]        = useState('gpt-4o');
  const [submitting,   setSubmitting]   = useState(false);
  const [demoMode,     setDemoMode]     = useState(false);
  const [showSidebar,  setShowSidebar]  = useState(false);

  const wsRef       = useRef(null);
  const scrollRef   = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [eventMap, activeId]);

  const connectWS = useCallback((sessionId) => {
    if (wsRef.current) wsRef.current.close();
    const ws = new WebSocket(
      `ws://${API_BASE.replace(/^https?:\/\//, '')}/workflows/${sessionId}/events?api_key=${API_KEY}`
    );
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setEventMap(prev => ({ ...prev, [sessionId]: [...(prev[sessionId] || []), msg] }));
      if (msg.performative === 'failure') {
        setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, status: 'failed' } : s));
      }
    };
    ws.onerror = () => ws.close();
    wsRef.current = ws;
  }, []);

  const submitObjective = async () => {
    const text = objective.trim();
    if (!text || submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
        body: JSON.stringify({ objective: text, provider, model }),
      });
      if (!res.ok) throw new Error('non-2xx');
      const data = await res.json();
      const session = {
        id: data.session_id, name: text.slice(0, 60),
        status: 'analyzing',
        ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setSessions(prev => [session, ...prev]);
      setActiveId(data.session_id);
      setObjective('');
      connectWS(data.session_id);
      setDemoMode(false);
    } catch {
      // Backend unavailable → drip mock events for visual demo
      const mockId = `demo_${Date.now()}`;
      setSessions(prev => [{
        id: mockId, name: text.slice(0, 60), status: 'completed',
        ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }, ...prev]);
      setActiveId(mockId);
      setObjective('');
      setDemoMode(true);
      MOCK_EVENTS.forEach((evt, i) => {
        setTimeout(() => {
          setEventMap(prev => ({
            ...prev,
            [mockId]: [...(prev[mockId] || []), { ...evt, id: `${mockId}_${i}`, timestamp: Date.now() / 1000 }],
          }));
        }, (i + 1) * 900);
      });
    } finally {
      setSubmitting(false);
    }
  };

  const submitHumanInput = async (taskId, input) => {
    if (!activeId) return;
    try {
      await fetch(`${API_BASE}/workflows/${activeId}/input`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
        body: JSON.stringify({ task_id: taskId, input }),
      });
    } catch (err) {
      console.warn('Human input submit failed (demo mode?):', err);
    }
  };

  const activeSession = sessions.find(s => s.id === activeId);
  const activeEvents  = eventMap[activeId] || [];
  const statusMeta    = STATUS_MAP[activeSession?.status] || STATUS_MAP.completed;

  return (
    /* Escape Layout padding to get full-height split pane */
    <div className="-mx-4 sm:-mx-6 -mt-4 sm:-mt-8 flex h-[calc(100dvh-4.5rem)] sm:h-[calc(100vh-5.5rem)] overflow-hidden font-sans relative">

      {/* Mobile backdrop */}
      {showSidebar && (
        <div
          className="md:hidden fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
          onClick={() => setShowSidebar(false)}
        />
      )}

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className={`
        fixed md:relative top-0 left-0 h-full z-50 md:z-auto
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
              <span
                className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border flex-shrink-0"
                style={{ color: statusMeta.color, borderColor: `${statusMeta.color}40`, background: `${statusMeta.color}10` }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: statusMeta.color }} />
                {statusMeta.label}
              </span>
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
            <span
              className="ml-auto flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full border flex-shrink-0"
              style={{ color: statusMeta.color, borderColor: `${statusMeta.color}40`, background: `${statusMeta.color}10` }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: statusMeta.color }} />
              {statusMeta.label}
            </span>
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
        <div className="flex-shrink-0 px-4 sm:px-8 py-4 sm:py-5 border-t border-white/[0.06] bg-black/80 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end gap-3 bg-[#0E0E0E] border border-white/10 rounded-[20px] px-5 py-4 focus-within:border-white/30 transition-colors shadow-lg shadow-black/30">
              <div className="flex flex-col gap-2 justify-end mb-1">
                <select
                  value={`${provider}:${model}`}
                  onChange={e => {
                    const [p, m] = e.target.value.split(':');
                    setProvider(p);
                    setModel(m);
                  }}
                  className="bg-[#1A1A1A] border border-white/10 text-[#71717A] hover:text-white text-xs rounded-lg px-2 py-1.5 outline-none transition-colors"
                >
                  <option value="openai:gpt-4o">GPT-5 pro</option>
                  <option value="anthropic:claude-3-5-sonnet-latest">Claude 3.5 Sonnet</option>
                  <option value="google:gemini-3.0-flash">Gemini 3.0 Flash</option>
                </select>
              </div>
              <textarea
                ref={textareaRef}
                rows={1}
                value={objective}
                onChange={e => setObjective(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitObjective(); } }}
                placeholder="Describe your objective — Tangent will architect the workflow…"
                className="flex-grow resize-none bg-transparent text-sm text-white placeholder-[#71717A] focus:outline-none leading-relaxed max-h-36 overflow-y-auto"
              />
              <button
                onClick={submitObjective}
                disabled={!objective.trim() || submitting}
                className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-full transition-all duration-300 disabled:opacity-30"
                style={{
                  background: objective.trim() && !submitting
                    ? 'white'
                    : '#1A1A1A',
                }}
              >
                {submitting
                  ? <Loader size={15} className="animate-spin text-white" />
                  : <Send size={15} className={objective.trim() ? 'text-black' : 'text-[#71717A]'} />
                }
              </button>
            </div>
            <p className="text-center text-[10px] text-[#71717A] mt-2.5 font-mono">
              Enter ↵ to send · Shift+Enter for newline
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
