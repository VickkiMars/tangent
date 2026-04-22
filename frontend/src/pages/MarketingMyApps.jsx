import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Box, Play, Calendar, HardDrive, RefreshCw, 
  Terminal, Search, Plus, CheckCircle, ArrowRight,
  Sparkles, Check, Copy, User, ChevronRight, LayoutGrid, Clock, Info
} from 'lucide-react';
import { MOCK_MY_APPS, MOCK_APP_RESULT_LOGS } from '../mockData';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// --- Sub-components for the Marketing Screenshots ---

const AppItemSidebar = ({ app, active }) => (
  <div className={`w-full text-left p-3.5 rounded-[16px] border transition-all duration-300 relative overflow-hidden ${
    active ? 'bg-[#1A1A1A] border-white/20 shadow-[0_0_18px_rgba(129,140,248,0.06)]' : 'bg-[#0E0E0E] border-white/[0.04]'
  }`}>
    {active && <div className="absolute left-0 top-0 bottom-0 w-[2.5px] bg-[#818CF8] shadow-[0_0_8px_#818CF8] rounded-l-[16px]" />}
    <p className="text-[13px] font-medium text-white line-clamp-1 mb-2">{app.name}</p>
    <div className="flex items-center justify-between">
      <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full border border-[#818CF8]/20 bg-[#818CF8]/5 text-[#818CF8]">Ready</span>
      <span className="font-mono text-[9px] text-[#52525B]">v1.0</span>
    </div>
  </div>
);

const EventCard = ({ event }) => (
  <div className="rounded-[20px] border border-white/[0.04] p-5 relative overflow-hidden my-3 bg-white/[0.02]">
    <div className="absolute left-0 top-0 bottom-0 w-[2.5px] rounded-l-[20px] bg-[#818CF8] shadow-[0_0_6px_rgba(129,140,248,0.4)]" />
    <div className="pl-1.5 font-sans">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[9px] font-black uppercase tracking-[0.15em] px-2 py-0.5 rounded-full border border-[#818CF8]/30 bg-[#818CF8]/05 text-[#818CF8]">
          {event.performative === 'request' ? 'RUNNING' : 'RESULT'}
        </span>
        <span className="font-mono text-[9px] text-[#52525B] ml-auto uppercase tracking-tighter opacity-70">{event.sender_id.split('-')[0]}</span>
      </div>
      <div className="text-[13px] text-[#D1D5DB] leading-relaxed markdown-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{event.payload?.natural_language || ''}</ReactMarkdown>
      </div>
    </div>
  </div>
);

// --- Main Page Component ---

export default function MarketingMyApps() {
  const [step, setStep] = useState('library'); // 'library' | 'prompt' | 'result'
  const apps = MOCK_MY_APPS;
  const targetApp = apps[1]; // Blog SEO Strategy
  const [deployParams] = useState({ TOPIC: 'Multi-Agent Orchestration' });

  // Believable varied timestamps for the screenshot
  const timestamps = ["4m ago", "1h ago", "2d ago", "Yesterday", "5h ago", "Oct 12"];

  return (
    <div className="flex w-[1200px] h-[630px] rounded-2xl border border-white/10 overflow-hidden relative bg-[#000000] mx-auto my-auto shadow-2xl selection:bg-[#818CF8] selection:text-black">
      
      <AnimatePresence mode="wait">
        
        {/* --- STEP 1: LIBRARY VIEW --- */}
        {step === 'library' && (
          <motion.div 
            key="library"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex w-full h-full"
          >
            {/* Sidebar */}
            <aside className="w-[280px] flex-shrink-0 border-r border-white/[0.06] bg-[#050505] flex flex-col">
              <div className="px-6 py-6 border-b border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] font-bold text-[#71717A] uppercase tracking-[0.2em]">Templates</span>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white text-black text-[10px] font-bold shadow-[0_0_12px_rgba(255,255,255,0.2)]">
                  <Plus size={11} /> New
                </button>
              </div>
              <div className="flex-grow p-4 space-y-3">
                {apps.slice(0, 5).map((app, i) => (
                  <AppItemSidebar key={app.id} app={app} active={i === 1} />
                ))}
              </div>
              <div className="p-6 border-t border-white/[0.06] bg-black/40">
                  <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#818CF8]/10 flex items-center justify-center border border-[#818CF8]/20">
                          <User size={14} className="text-[#818CF8]" />
                      </div>
                      <div className="flex flex-col">
                          <span className="text-[11px] font-bold text-white uppercase tracking-wider">Premium Access</span>
                          <span className="text-[9px] text-[#52525B] font-mono">v3.1 Flash-Lite</span>
                      </div>
                  </div>
              </div>
            </aside>

            {/* Main Content */}
            <main className="flex-grow flex flex-col p-10 relative">
              <div className="absolute inset-0 bg-radial-gradient from-[#818CF8]/05 to-transparent pointer-events-none" />
              <div className="flex items-center justify-between mb-10">
                <div>
                  <h1 className="text-3xl font-bold text-white tracking-tight mb-2 flex items-center gap-3">
                    <Box className="w-8 h-8 text-[#818CF8]" />
                    My Apps
                  </h1>
                  <p className="text-[#71717A] text-sm">Productized workflows for autonomous execution.</p>
                </div>
                <div className="flex items-center gap-3">
                   <div className="flex items-center p-1 bg-[#1A1A1A] rounded-full border border-white/[0.05]">
                       <button className="px-3 py-1 rounded-full text-[9px] uppercase font-bold tracking-wide bg-white text-black shadow-lg">Grid</button>
                       <button className="px-3 py-1 rounded-full text-[9px] uppercase font-bold tracking-wide text-[#71717A]">List</button>
                   </div>
                   <button className="p-2.5 bg-[#0E0E0E] border border-white/10 rounded-full text-[#71717A]">
                     <Search size={16} />
                   </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6 overflow-hidden">
                {apps.slice(0, 4).map((app, i) => (
                  <motion.div 
                    key={app.id}
                    initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                    className={`p-6 rounded-[24px] border transition-all duration-500 relative group overflow-hidden ${i === 1 ? 'border-[#818CF8]/40 bg-[#0E0E0E] shadow-[0_0_30px_rgba(129,140,248,0.06)]' : 'border-white/[0.06] bg-[#0E0E0E] hover:border-white/20 hover:shadow-[0_0_20px_rgba(255,255,255,0.02)]'}`}
                  >
                    <div className="absolute top-0 right-0 w-24 h-24 bg-[#818CF8]/5 blur-[40px] rounded-full pointer-events-none" />
                    <div className="flex justify-between items-start mb-4 relative z-10">
                      <h3 className="text-lg font-bold text-white tracking-tight">{app.name}</h3>
                      <span className="text-[10px] font-mono text-[#52525B]">{app.id.substring(0, 8)}</span>
                    </div>
                    <div className="flex gap-2 mb-10 relative z-10">
                       <span className="text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full border border-white/10 text-[#71717A] bg-white/[0.02]">Gemini-1.5</span>
                       {app.parameters.length > 0 ? (
                         <div className="relative group/tooltip">
                            <span className="text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full border border-[#818CF8]/20 text-[#818CF8] bg-[#818CF8]/5 underline underline-offset-4 decoration-dotted decoration-[#818CF8]/50 cursor-help transition-all hover:bg-[#818CF8]/10">
                                Parameterized
                            </span>
                            <div className="absolute top-full left-0 mt-3 w-48 p-3 rounded-xl bg-[#1A1A1A] border border-white/10 shadow-2xl opacity-0 translate-y-2 group-hover/tooltip:opacity-100 group-hover/tooltip:translate-y-0 transition-all pointer-events-none z-50">
                               <p className="text-[10px] text-[#A1A1AA] leading-relaxed">Contains dynamic variables that can be customized at runtime before execution.</p>
                            </div>
                         </div>
                       ) : (
                         <span className="text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full border border-white/10 text-[#52525B] bg-white/[0.02]">
                            Static
                         </span>
                       )}
                    </div>
                    <div className="flex items-center justify-between pt-4 border-t border-white/[0.04]">
                         <div className="flex items-center gap-1.5 text-[#52525B]">
                             <Clock size={12} />
                             <span className="text-[10px] font-mono">Last run: {timestamps[i]}</span>
                         </div>
                         <button 
                            onClick={(e) => { 
                                e.stopPropagation(); 
                                if(app.parameters.length > 0) setStep('prompt'); 
                                else setStep('result');
                            }}
                            className={`px-5 py-2 rounded-xl text-xs font-bold transition-all bg-[#818CF8] text-black shadow-[0_0_15px_rgba(129,140,248,0.2)] active:scale-95 hover:scale-[1.03]`}
                        >
                            {app.parameters.length > 0 ? 'Configure' : 'Run'}
                        </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </main>
          </motion.div>
        )}

        {/* --- STEP 2: PROMPT OVERLAY --- */}
        {step === 'prompt' && (
          <motion.div 
            key="prompt"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-[10px]"
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }}
              className="bg-[#0E0E0E] w-[480px] border border-white/10 p-10 rounded-[36px] shadow-[0_40px_100px_rgba(0,0,0,0.9)] relative"
            >
              <div className="absolute top-0 right-0 w-56 h-56 bg-[#818CF8]/10 blur-[80px] rounded-full translate-x-14 -translate-y-14" />
              <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-xl bg-[#818CF8]/10 border border-[#818CF8]/20">
                      <Terminal size={18} className="text-[#818CF8]" />
                  </div>
                  <h2 className="text-2xl font-bold text-white tracking-tight">Configure Launch</h2>
              </div>
              <p className="text-sm text-[#71717A] mb-8 leading-relaxed">Required inputs for <span className="text-white font-semibold">{targetApp.name}</span>.</p>
              
              <div className="space-y-6">
                <div>
                  <label className="block text-[10px] font-black uppercase tracking-[0.25em] text-[#52525B] mb-2.5">Industry Topic</label>
                  <div className="relative group">
                    <input 
                      type="text" 
                      value={deployParams.TOPIC}
                      className="w-full bg-[#141414] border border-white/[0.08] rounded-2xl px-6 py-4.5 text-sm text-white focus:outline-none focus:border-[#818CF8]/40 transition-all font-medium shadow-inner"
                      readOnly
                    />
                    <Sparkles size={16} className="absolute right-6 top-1/2 -translate-y-1/2 text-[#818CF8]/40" />
                  </div>
                </div>
                
                <div className="pt-8 flex gap-4">
                   <button onClick={() => setStep('library')} className="flex-1 py-4 rounded-2xl text-xs font-bold text-[#71717A] hover:bg-white/5 transition-colors border border-transparent">Cancel</button>
                   <button 
                    onClick={() => setStep('result')}
                    className="flex-[1.5] py-4 rounded-2xl text-xs font-bold bg-white text-black hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
                   >
                     Initialize Workflow <ArrowRight size={14} />
                   </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}

        {/* --- STEP 3: RESULT VIEW (CHAT STYLE) --- */}
        {step === 'result' && (
          <motion.div 
            key="result"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="flex flex-col w-full h-full bg-[#000]"
          >
            {/* Top Bar */}
            <header className="h-16 border-b border-white/[0.06] bg-[#050505]/95 backdrop-blur-xl px-12 flex items-center justify-between relative z-10">
              <div className="flex items-center gap-5">
                <button onClick={() => setStep('library')} className="p-2 rounded-full hover:bg-white/5 text-[#52525B] hover:text-white transition-colors">
                   <RefreshCw size={16} />
                </button>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[10px] text-[#52525B] tracking-tight">{targetApp.id}</span>
                  <span className="w-px h-3 bg-white/10" />
                  <span className="text-sm font-semibold text-white tracking-tight">{targetApp.name}</span>
                </div>
              </div>
              <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-[#818CF8]/20 bg-[#818CF8]/10 text-[#818CF8] text-[10px] font-black uppercase tracking-widest shadow-[0_0_15px_rgba(129,140,248,0.15)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#818CF8] shadow-[0_0_6px_#818CF8] animate-pulse" />
                    Executing
                  </div>
              </div>
            </header>

            {/* Event Feed */}
            <div className="flex-grow overflow-hidden px-24 py-12 max-w-4xl mx-auto w-full relative">
              <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#818CF8]/05 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />
              
              {/* User Input Callout */}
              <div className="flex flex-col items-end gap-3 mb-10">
                <div className="max-w-[80%] bg-white rounded-[24px] rounded-tr-[4px] px-7 py-4.5 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
                  <p className="text-[14px] text-black font-semibold leading-relaxed tracking-tight">Run autonomous SEO deployment for: <span className="p-1 px-2 rounded bg-black/5 text-[#4F46E5]">Multi-Agent Orchestration</span>.</p>
                </div>
                <div className="flex items-center gap-2 px-3">
                   <span className="text-[10px] font-black text-[#52525B] uppercase tracking-[0.2em]">Deployer_Root</span>
                </div>
              </div>

              {/* Agent Logs */}
              <div className="space-y-4">
                {MOCK_APP_RESULT_LOGS.slice(0, 3).map((log, i) => (
                  <motion.div 
                    key={log.message_id}
                    initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.4, ease: "easeOut" }}
                  >
                    <EventCard event={log} />
                  </motion.div>
                ))}
              </div>

              {/* Completion CTA */}
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 1.6 }}
                className="mt-10 p-8 rounded-[32px] border border-white/[0.08] bg-[#0E0E0E] flex items-center justify-between shadow-2xl relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-[#818CF8]/10 to-transparent pointer-events-none opacity-40" />
                <div className="flex items-center gap-5 relative z-10">
                   <div className="w-14 h-14 rounded-2xl bg-[#818CF8]/10 flex items-center justify-center border border-[#818CF8]/20 shadow-inner">
                      <Sparkles size={24} className="text-[#818CF8]" />
                   </div>
                   <div>
                      <p className="text-white text-lg font-bold tracking-tight">Strategy Finalized</p>
                      <p className="text-xs text-[#71717A] font-mono">Parallel Execution: 4 nodes · Cost $0.42</p>
                   </div>
                </div>
                <button className="px-7 py-3 rounded-2xl bg-white text-black text-xs font-black uppercase tracking-widest hover:bg-[#818CF8] transition-all flex items-center gap-2.5 shadow-xl active:scale-95">
                  Inspect Result <ChevronRight size={16} />
                </button>
              </motion.div>

            </div>
          </motion.div>
        )}

      </AnimatePresence>

      {/* Aesthetic Overlays */}
      <div className="absolute inset-0 border-[12px] border-black/50 pointer-events-none z-[100] rounded-2xl" />
      <div className="absolute inset-0 shadow-[inset_0_0_100px_rgba(0,0,0,0.4)] pointer-events-none" />

    </div>
  );
}
