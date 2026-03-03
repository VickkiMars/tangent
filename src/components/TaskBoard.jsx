import React, { useState, useEffect } from 'react';
import {
  CheckCircle, AlertCircle,
  Terminal, Cpu, Wrench, MessageSquare, Search,
  Clock, DollarSign, X, Download, ChevronDown, ChevronUp,
  Box, Layers, GitBranch, UserCheck, Activity,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import GraphView from './GraphView';

// ─── Colours ──────────────────────────────────────────────────────────────────
const C = {
  cyan:  '#FFFFFF', orange: '#FF8A00', green: '#10B981',
  red:   '#EF4444', blue:  '#0066FF', muted: '#71717A',
};

// ─── Mock thread / event data (kept for sidebar only) ─────────────────────────
const THREADS = [
  { id: 'tkt_12345_customer_refund', status: 'active',    time: '2m ago', cost: '$0.0064', name: 'Customer Refund'  },
  { id: 'tkt_67890_tech_support',    status: 'completed', time: '1h ago', cost: '$0.0120', name: 'Tech Support'     },
  { id: 'tkt_34567_account_issue',   status: 'failed',    time: '3h ago', cost: '$0.0080', name: 'Account Issue'    },
  { id: 'tkt_89123_data_export',     status: 'running',   time: '5m ago', cost: '$0.0030', name: 'Data Export'      },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getEventIcon(type, subtype) {
  if (type==='SYSTEM') return <Cpu size={13} style={{ color:C.muted }} />;
  if (type==='TOOL')   return <Wrench size={13} style={{ color:C.orange }} />;
  if (type==='AGENT') {
    if (subtype==='spawn')       return <div style={{ width:8, height:8, borderRadius:'50%', background:C.cyan,   boxShadow:`0 0 8px ${C.cyan}` }} />;
    if (subtype==='termination') return <div style={{ width:8, height:8, borderRadius:'50%', background:C.muted }} />;
    if (subtype==='hibernate')   return <div style={{ width:8, height:8, borderRadius:'50%', background:C.orange, boxShadow:`0 0 8px ${C.orange}` }} />;
    return <MessageSquare size={13} style={{ color:C.cyan }} />;
  }
  return <div style={{ width:8, height:8, borderRadius:'50%', background:'#fff' }} />;
}

// Map backend A2AMessage to frontend event format
function mapBackendEvent(msg) {
  const d = new Date(msg.timestamp * 1000);
  const timeStr = d.toLocaleTimeString([], { hour12: false });
  
  let type = 'AGENT';
  let subtype = msg.performative;
  let content = msg.payload?.natural_language || '';
  
  if (msg.sender_id === 'human') {
    type = 'SYSTEM';
    subtype = 'human_input';
  } else if (msg.sender_id === 'meta_agent') {
    type = 'SYSTEM';
  }

  // Formatting for UI
  if (subtype === 'inform') {
    content = `💬 "${content}"`;
    subtype = 'message';
  } else if (subtype === 'hibernate') {
    content = `⏸ Hibernated: ${msg.sender_id}\nAwaiting human decision\n${content}`;
  }

  return {
    id: msg.message_id,
    type,
    subtype,
    timestamp: timeStr,
    agent_id: msg.sender_id,
    task_id: msg.thread_id,
    content,
    reason: msg.payload?.natural_language,
    details: msg
  };
}

// ─── Tab button ───────────────────────────────────────────────────────────────
function Tab({ label, icon: Icon, active, onClick, badge = 0 }) {
  return (
    <button
      onClick={onClick}
      className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] uppercase font-bold tracking-wide transition-all duration-300 ${
        active ? 'bg-white text-black shadow-[0_0_14px_rgba(255,255,255,0.25)]' : 'text-[#71717A] hover:text-white'
      }`}
    >
      <Icon size={10} />
      {label}
      {badge > 0 && (
        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#FF8A00] text-black text-[8px] font-black flex items-center justify-center leading-none">
          {badge}
        </span>
      )}
    </button>
  );
}

// ─── TaskBoard ────────────────────────────────────────────────────────────────
const TaskBoard = ({ defaultTaskId = null }) => {
  const [selectedId, setSelectedId]         = useState(defaultTaskId || 'tkt_12345_customer_refund');
  const [inspectorData, setInspectorData]   = useState(null);
  const [filter, setFilter]                 = useState('all');
  const [centerTab, setCenterTab]           = useState('timeline'); // 'timeline' | 'graph' | 'input'
  const [humanResponses, setHumanResponses] = useState({}); // { agentId: responseText }
  const [mobilePanel, setMobilePanel]       = useState('main'); // 'threads' | 'main' | 'inspector'
  
  // Real data state
  const [workflowState, setWorkflowState] = useState(null);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    let ws;
    const fetchData = async () => {
      try {
        const res = await fetch(`http://localhost:8000/workflows/${selectedId}`, {
          headers: { 'X-API-Key': 'nagent-dev-key' }
        });
        if (res.ok) {
          const data = await res.json();
          setWorkflowState(data.state);
          const mappedLogs = data.logs.map(mapBackendEvent);
          setEvents(mappedLogs);
        } else {
          setWorkflowState(null);
          setEvents([]);
        }
      } catch (err) {
        console.error(err);
        setWorkflowState(null);
        setEvents([]);
      }
    };
    fetchData();

    ws = new WebSocket(`ws://localhost:8000/workflows/${selectedId}/events?api_key=nagent-dev-key`);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setEvents(prev => {
          // Prevent duplicates if already fetched via HTTP
          if (prev.some(e => e.id === msg.message_id)) return prev;
          return [...prev, mapBackendEvent(msg)];
        });
      } catch (err) {
        console.debug('Failed to parse WebSocket message', err);
      }
    };

    return () => {
      if (ws) ws.close();
    };
  }, [selectedId]);

  const currentEvents  = events;
  const filteredEvents = currentEvents.filter(e => filter === 'all' || e.type.toLowerCase() === filter);
  const pendingInputs  = currentEvents.filter(e => e.type === 'AGENT' && e.subtype === 'hibernate');
  const inputBadge     = pendingInputs.filter(e => !humanResponses[e.agent_id]).length;

  const submitHumanResponse = async (agentId) => {
    const draft = (humanResponses[agentId + '_draft'] || '').trim();
    if (!draft) return;
    
    const evt = pendingInputs.find(e => e.agent_id === agentId);
    if (!evt) return;

    try {
      await fetch(`http://localhost:8000/workflows/${selectedId}/input`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'nagent-dev-key'
        },
        body: JSON.stringify({ task_id: evt.task_id, input: draft })
      });
      setHumanResponses(prev => ({ ...prev, [agentId]: draft, [agentId + '_draft']: '' }));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div
      className="h-[calc(100dvh-5rem)] sm:h-[calc(100vh-6rem)] w-full max-w-[1920px] mx-auto grid grid-cols-12 gap-2 sm:gap-4 lg:gap-6 p-2 sm:p-4 lg:p-6 font-sans text-sm bg-[#000000]"
      style={{ color: '#A1A1AA' }}
    >
      {/* ── Mobile panel tabs ─────────────────────────────────────────── */}
      <div className="lg:hidden col-span-12 flex gap-1 p-1 bg-[#0E0E0E] rounded-full border border-white/[0.07] self-start">
        {[
          { key: 'threads',  label: 'Threads'  },
          { key: 'main',     label: 'Board'    },
          { key: 'inspector',label: 'Inspector', badge: inspectorData ? 1 : 0 },
        ].map(({ key, label, badge }) => (
          <button
            key={key}
            onClick={() => setMobilePanel(key)}
            className={`relative flex-1 py-2 rounded-full text-[11px] font-bold uppercase tracking-wide transition-all duration-300 ${
              mobilePanel === key ? 'bg-white text-black shadow-[0_0_12px_rgba(255,255,255,0.2)]' : 'text-[#71717A] hover:text-white'
            }`}
          >
            {label}
            {badge > 0 && (
              <span className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-[#FF8A00] text-black text-[7px] font-black flex items-center justify-center leading-none">
                {badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Col 1: Thread Registry ───────────────────────────────────── */}
      <div className={`col-span-12 lg:col-span-3 xl:col-span-2 gap-4 h-full ${mobilePanel === 'threads' ? 'flex' : 'hidden lg:flex'} flex-col`}>
        <div className="flex items-center justify-between px-2">
          <span className="text-[10px] font-medium text-[#71717A] tracking-widest uppercase">Threads</span>
          <button className="p-2 hover:bg-[#1A1A1A] rounded-full text-[#71717A] hover:text-white transition-colors">
            <Search size={13} />
          </button>
        </div>

        <div className="flex-grow overflow-y-auto space-y-3 pr-1">
          {THREADS.map((thread, idx) => (
            <motion.div
              key={thread.id}
              initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay: idx * 0.04 }}
              onClick={() => setSelectedId(thread.id)}
              className={`p-4 rounded-[16px] border cursor-pointer transition-all duration-300 relative overflow-hidden ${
                selectedId === thread.id
                  ? 'bg-[#1A1A1A] border-white/30 shadow-[0_0_18px_rgba(255,255,255,0.07)]'
                  : 'bg-[#0E0E0E] border-white/[0.07] hover:border-white/20 hover:bg-[#141414]'
              }`}
            >
              {selectedId === thread.id && (
                <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-white shadow-[0_0_8px_#FFFFFF]" />
              )}
              <div className="flex flex-col gap-1 mb-2">
                <span className={`font-mono text-[10px] tracking-tight ${selectedId===thread.id ? 'text-white' : 'text-[#71717A]'}`}>
                  {thread.id}
                </span>
                <span className="text-sm font-medium text-white truncate">{thread.name}</span>
              </div>
              <div className="flex items-center gap-3 mt-2">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1.5 ${
                  thread.status==='active'    ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]' :
                  thread.status==='running'   ? 'bg-[#0066FF]/10 border-[#0066FF]/30 text-[#0066FF]' :
                  thread.status==='failed'    ? 'bg-[#EF4444]/10 border-[#EF4444]/30 text-[#EF4444]' :
                                                'bg-[#71717A]/10 border-[#71717A]/30 text-[#71717A]'
                }`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    thread.status==='active'  ? 'bg-[#10B981] shadow-[0_0_5px_#10B981]' :
                    thread.status==='running' ? 'bg-[#0066FF] shadow-[0_0_5px_#0066FF]' :
                    thread.status==='failed'  ? 'bg-[#EF4444]' : 'bg-[#71717A]'
                  }`} />
                  {thread.status}
                </span>
                <span className="text-[10px] text-[#71717A] font-mono ml-auto">{thread.time}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* ── Col 2: Centre Panel with Tabs ────────────────────────────── */}
      <div className={`col-span-12 lg:col-span-6 xl:col-span-7 h-full bg-[#0E0E0E] rounded-[24px] border border-white/[0.07] overflow-hidden shadow-2xl ${mobilePanel === 'main' ? 'flex' : 'hidden lg:flex'} flex-col`}>

        {/* Sticky header */}
        <div className="border-b border-white/[0.07] px-4 sm:px-6 py-3 bg-[rgba(14,14,14,0.9)] backdrop-blur-xl z-10 sticky top-0 flex flex-col gap-2 sm:gap-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="font-sans text-sm sm:text-base font-semibold text-white tracking-tight truncate">
                {THREADS.find(t => t.id === selectedId)?.name || selectedId}
              </h2>
              <div className="text-[10px] text-[#71717A] flex gap-3 font-mono mt-0.5">
                <span className="flex items-center gap-1"><Clock size={10}/> {workflowState?.status || 'No state'}</span>
                <span className="flex items-center gap-1 hidden sm:flex"><Layers size={10}/> {currentEvents.length} events</span>
              </div>
            </div>
            {/* Filter pills (Timeline tab only) */}
            {centerTab === 'timeline' && (
              <div className="flex items-center p-1 bg-[#1A1A1A] rounded-full border border-white/[0.05] flex-shrink-0">
                {['all','agent','tool','system'].map(f => (
                  <button key={f} onClick={() => setFilter(f)}
                    className={`px-2 sm:px-3 py-1 rounded-full text-[9px] sm:text-[10px] uppercase font-bold tracking-wide transition-all duration-300 ${
                      filter===f ? 'bg-white text-black shadow-[0_0_12px_rgba(255,255,255,0.25)]' : 'text-[#71717A] hover:text-white'
                    }`}
                  >{f}</button>
                ))}
              </div>
            )}
          </div>

          {/* Tab bar */}
          <div className="flex items-center gap-1 p-1 bg-[#1A1A1A] rounded-full border border-white/[0.05] self-start">
            <Tab label="Timeline"    icon={Activity}  active={centerTab==='timeline'} onClick={() => setCenterTab('timeline')} />
            <Tab label="Dep. Graph"  icon={GitBranch} active={centerTab==='graph'}    onClick={() => setCenterTab('graph')} />
            <Tab label="Human Input" icon={UserCheck} active={centerTab==='input'}    onClick={() => setCenterTab('input')} badge={inputBadge} />
          </div>
        </div>

        {/* ── Timeline ──────────────────────────────────────────────── */}
        {centerTab === 'timeline' && (
          <div className="flex-grow overflow-y-auto p-4 sm:p-8 space-y-5 sm:space-y-8 relative">
            <div className="absolute inset-0 pointer-events-none opacity-20"
              style={{ background:'radial-gradient(circle at 50% 0%,rgba(255,255,255,0.12),transparent 70%)' }} />
            <div className="absolute left-[36px] sm:left-[52px] top-4 sm:top-8 bottom-4 sm:bottom-8 w-px bg-gradient-to-b from-transparent via-white/[0.08] to-transparent" />
            <AnimatePresence>
              {filteredEvents.length === 0 ? (
                <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }}
                  className="text-center text-[#71717A] py-20 font-mono text-xs">
                  [No events matching filter criteria]
                </motion.div>
              ) : filteredEvents.map((evt, idx) => (
                <TimelineEvent key={evt.id} evt={evt} idx={idx}
                  onInspect={() => setInspectorData(evt)} getEventIcon={getEventIcon} />
              ))}
            </AnimatePresence>
          </div>
        )}

        {/* ── Dependency Graph ──────────────────────────────────────── */}
        {centerTab === 'graph' && (
          <div className="flex-grow relative overflow-hidden">
            <GraphView tasks={workflowState?.tasks} manifest={workflowState?.manifest} />
          </div>
        )}

        {/* ── Human Input ───────────────────────────────────────────── */}
        {centerTab === 'input' && (
          <div className="flex-grow overflow-y-auto p-8 space-y-6">
            {pendingInputs.length === 0 ? (
              <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }}
                className="flex flex-col items-center justify-center h-full text-center pb-10">
                <div className="w-16 h-16 rounded-full bg-[#1A1A1A] flex items-center justify-center mb-4 border border-white/[0.06]">
                  <UserCheck size={24} className="text-[#71717A]" />
                </div>
                <p className="text-sm font-medium text-[#A1A1AA] mb-1">No agents awaiting input</p>
                <p className="text-xs text-[#71717A] max-w-[220px] leading-relaxed">
                  Agents that request human feedback will appear here while hibernated.
                </p>
              </motion.div>
            ) : pendingInputs.map(evt => (
              <motion.div key={evt.id} initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }}
                className="rounded-[20px] border border-[#FF8A00]/35 p-6 relative overflow-hidden"
                style={{ background:'linear-gradient(135deg,rgba(255,138,0,0.05),#0E0E0E)' }}>
                <div className="absolute inset-0 pointer-events-none"
                  style={{ background:'radial-gradient(circle at top right,rgba(255,138,0,0.06),transparent 60%)' }} />
                <div className="relative">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-2 h-2 rounded-full bg-[#FF8A00] shadow-[0_0_8px_#FF8A00]" />
                    <span className="text-[10px] font-bold text-[#FF8A00] uppercase tracking-widest">Agent Awaiting Input</span>
                    {humanResponses[evt.agent_id] && (
                      <span className="ml-auto text-[9px] text-[#10B981] font-bold uppercase tracking-wider flex items-center gap-1">
                        <CheckCircle size={10}/> Responded
                      </span>
                    )}
                  </div>
                  <p className="font-mono text-[10px] text-[#71717A] mb-3">{evt.agent_id}</p>
                  <p className="text-sm text-[#E2E8F0] leading-relaxed mb-5">{evt.reason}</p>

                  {humanResponses[evt.agent_id] ? (
                    <div className="bg-[#0A1A0A] border border-[#10B981]/20 rounded-[12px] px-4 py-3">
                      <p className="text-[10px] text-[#71717A] font-mono mb-1">Your response:</p>
                      <p className="text-sm text-[#10B981]">{humanResponses[evt.agent_id]}</p>
                    </div>
                  ) : (
                    <div className="flex gap-3">
                      <input
                        value={humanResponses[evt.agent_id+'_draft'] || ''}
                        onChange={e => setHumanResponses(prev => ({ ...prev, [evt.agent_id+'_draft']: e.target.value }))}
                        onKeyDown={e => e.key==='Enter' && submitHumanResponse(evt.agent_id)}
                        placeholder="Type your decision or instructions…"
                        className="flex-grow bg-[#1A1A1A] border border-white/10 rounded-full px-4 py-2.5 text-sm text-white placeholder-[#71717A] focus:outline-none focus:border-[#FF8A00]/50 transition-colors"
                      />
                      <button
                        onClick={() => submitHumanResponse(evt.agent_id)}
                        disabled={!(humanResponses[evt.agent_id+'_draft']||'').trim()}
                        className="px-5 py-2.5 rounded-full text-sm font-semibold text-black transition-all duration-300 disabled:opacity-30"
                        style={{ background:'#FF8A00' }}
                      >
                        Submit
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* ── Col 3: Inspector ─────────────────────────────────────────── */}
      <div className={`col-span-12 lg:col-span-3 h-full ${mobilePanel === 'inspector' ? 'flex' : 'hidden lg:flex'} flex-col`}>
        <div className="bg-[#0E0E0E] h-full rounded-[24px] border border-white/[0.07] overflow-hidden flex flex-col shadow-xl">
          <div className="h-12 border-b border-white/[0.05] flex items-center justify-between px-6 bg-[rgba(14,14,14,0.9)] backdrop-blur-sm">
            <span className="text-[10px] font-bold text-[#71717A] uppercase tracking-widest">Inspector</span>
            {inspectorData && (
              <button onClick={() => setInspectorData(null)} className="text-[#71717A] hover:text-[#EF4444] transition-colors">
                <X size={13}/>
              </button>
            )}
          </div>

          <AnimatePresence mode="wait">
            {!inspectorData ? (
              <motion.div key="empty" initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
                className="flex-grow flex flex-col items-center justify-center text-center p-8 text-[#71717A]">
                <div className="w-16 h-16 rounded-full bg-[#1A1A1A] flex items-center justify-center mb-4 border border-white/[0.05]">
                  <Box size={22} className="opacity-40" />
                </div>
                <p className="text-sm font-medium text-[#A1A1AA] mb-1">No Event Selected</p>
                <p className="text-xs opacity-50 max-w-[190px] leading-relaxed">
                  Click an event on the timeline to inspect its full payload.
                </p>
              </motion.div>
            ) : (
              <motion.div key={inspectorData.id}
                initial={{ x:16, opacity:0 }} animate={{ x:0, opacity:1 }} exit={{ x:16, opacity:0 }}
                className="flex-grow overflow-y-auto p-6 space-y-5">

                {/* Header card */}
                <div className="bg-[#151515] rounded-[16px] p-5 border border-white/[0.05] relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-[0.03] blur-[60px] rounded-full translate-x-10 -translate-y-10" />
                  <div className="flex items-center gap-3 mb-3 text-[#71717A]">
                    {getEventIcon(inspectorData.type, inspectorData.subtype)}
                    <span className="font-mono text-[10px] tracking-wide">{inspectorData.id}</span>
                  </div>
                  <h3 className="font-semibold text-white text-base mb-3 leading-tight">
                    {inspectorData.details?.type || inspectorData.details?.tool || inspectorData.type}
                  </h3>
                  <div className="flex flex-wrap gap-2 text-[10px] font-mono uppercase tracking-wide">
                    {inspectorData.duration && (
                      <span className="bg-[#1A1A1A] border border-white/10 px-2 py-1 rounded text-[#A1A1AA] flex items-center gap-1">
                        <Clock size={9}/> {inspectorData.duration}
                      </span>
                    )}
                    {inspectorData.status && (
                      <span className={`px-2 py-1 rounded border flex items-center gap-1 ${
                        inspectorData.status==='success'
                          ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]'
                          : 'bg-[#EF4444]/10 border-[#EF4444]/30 text-[#EF4444]'
                      }`}>
                        {inspectorData.status==='success' ? <CheckCircle size={9}/> : <AlertCircle size={9}/>}
                        {inspectorData.status}
                      </span>
                    )}
                  </div>
                </div>

                {/* JSON viewer */}
                <div className="relative group">
                  <div className="absolute right-3 top-3 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => navigator.clipboard?.writeText(JSON.stringify(inspectorData.details, null, 2))}
                      className="p-2 bg-[#1A1A1A] rounded-lg hover:bg-[#252525] text-white/70 hover:text-white border border-white/10 shadow-lg"
                      title="Copy JSON"
                    >
                      <Download size={13}/>
                    </button>
                  </div>
                  <div className="bg-[#050508] rounded-[16px] p-4 border border-white/[0.07] font-mono text-xs overflow-x-auto shadow-inner">
                    <div className="text-[#71717A] mb-2 select-none flex items-center gap-1.5">
                      <Terminal size={11}/> payload.json
                    </div>
                    <pre className="leading-relaxed">
                      <span className="text-white">{'{'}</span>
                      {Object.entries(inspectorData.details || {}).map(([key, val], i, arr) => (
                        <div key={key} className="pl-4">
                          <span className="text-white">{key}</span>
                          <span className="text-[#A1A1AA]">: </span>
                          <span className="text-[#FF8A00]">
                            {typeof val === 'object' ? JSON.stringify(val) : `"${val}"`}
                          </span>
                          {i < arr.length-1 && <span className="text-[#71717A]">,</span>}
                        </div>
                      ))}
                      <span className="text-white">{'}'}</span>
                    </pre>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

// ─── TimelineEvent ────────────────────────────────────────────────────────────
const TimelineEvent = ({ evt, idx, onInspect, getEventIcon }) => {
  const [expanded, setExpanded] = useState(false);
  const isAgent = evt.type === 'AGENT';
  const isTool  = evt.type === 'TOOL';

  return (
    <motion.div
      initial={{ opacity:0, x:-16 }} animate={{ opacity:1, x:0 }}
      transition={{ delay: idx * 0.04, type:'spring', stiffness:300, damping:24 }}
      className="relative pl-10 sm:pl-14 group"
    >
      <div
        onClick={onInspect}
        className={`absolute left-[32px] sm:left-[48px] top-1.5 w-2.5 h-2.5 rounded-full border-2 border-[#0E0E0E] z-10 cursor-pointer transition-all duration-300 group-hover:scale-125 ${
          isAgent && evt.subtype==='spawn'       ? 'bg-white shadow-[0_0_10px_#FFFFFF]' :
          isAgent && evt.subtype==='hibernate'   ? 'bg-[#FF8A00] shadow-[0_0_10px_#FF8A00]' :
          isAgent                                ? 'bg-white opacity-50' :
          isTool                                 ? 'bg-[#FF8A00] shadow-[0_0_10px_#FF8A00]' :
                                                   'bg-[#71717A]'
        }`}
      />

      <div className="rounded-[14px] p-4 transition-all duration-300 hover:bg-white/[0.02] border border-transparent hover:border-white/[0.04] cursor-pointer">
        <div className="flex items-center gap-3 mb-2" onClick={onInspect}>
          <div className="p-1.5 rounded-lg bg-[#1A1A1A] border border-white/[0.05]">
            {getEventIcon(evt.type, evt.subtype)}
          </div>
          <span className="font-mono text-[10px] text-[#71717A] tracking-wide">{evt.timestamp}</span>
          <span className={`text-[9px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full ${
            isAgent && evt.subtype==='hibernate' ? 'bg-[rgba(255,138,0,0.1)] text-[#FF8A00]' :
            isAgent                              ? 'bg-[rgba(255,255,255,0.1)] text-white'  :
            isTool                               ? 'bg-[rgba(255,138,0,0.1)] text-[#FF8A00]'  :
                                                   'bg-[rgba(113,113,122,0.1)] text-[#71717A]'
          }`}>
            {evt.subtype || evt.type}
          </span>
        </div>

        <div className="text-sm text-[#E2E8F0] whitespace-pre-wrap leading-7 font-mono pl-1" onClick={onInspect}>
          {evt.content}
        </div>

        {/* Expand agent message */}
        {isAgent && evt.subtype==='message' && (
          <div className="mt-3">
            <button
              onClick={e => { e.stopPropagation(); setExpanded(!expanded); }}
              className="text-[10px] font-bold text-[#71717A] hover:text-white flex items-center gap-1 transition-colors uppercase tracking-widest"
            >
              {expanded ? <ChevronUp size={10}/> : <ChevronDown size={10}/>}
              {expanded ? 'Collapse' : 'Expand'} response
            </button>
            <AnimatePresence>
              {expanded && (
                <motion.div initial={{ height:0, opacity:0 }} animate={{ height:'auto', opacity:1 }} exit={{ height:0, opacity:0 }} className="overflow-hidden">
                  <div className="mt-3 p-4 bg-[#050508] rounded-[12px] border border-white/[0.07] text-xs font-mono text-[#A1A1AA] whitespace-pre-wrap shadow-inner">
                    {evt.details?.raw_response ? JSON.stringify(evt.details.raw_response, null, 2) : 'Full response would appear here…'}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {isTool && (
          <div className="mt-2 text-xs text-[#71717A] flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <span className="flex items-center gap-1.5"><Clock size={11} className="text-[#A1A1AA]"/> {evt.duration}</span>
            {evt.status==='success' && <span className="text-[#10B981] flex items-center gap-1.5 font-medium"><CheckCircle size={11}/> Success</span>}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default TaskBoard;
