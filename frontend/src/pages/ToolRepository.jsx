import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Wrench, Search, Plus, Trash2, CheckCircle, XCircle, Power,
  PowerOff, ChevronDown, ChevronUp, Code2, X, AlertTriangle,
  Bot, Box, Layers, RefreshCw, Copy, Check,
} from 'lucide-react';
import { getTools, createTool, deleteTool, approveTool, toggleTool } from '../api';

// ─── Source badge ────────────────────────────────────────────────────────────
const SourceBadge = ({ source }) => {
  const styles = {
    builtin:  'bg-blue-500/10  text-blue-400  border-blue-500/20',
    agent:    'bg-purple-500/10 text-purple-400 border-purple-500/20',
    manual:   'bg-amber-500/10 text-amber-400  border-amber-500/20',
  };
  const icons = {
    builtin: <Box size={10} />,
    agent:   <Bot size={10} />,
    manual:  <Wrench size={10} />,
  };
  const label = { builtin: 'Built-in', agent: 'Agent-created', manual: 'Manual' };
  const s = styles[source] || styles.manual;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${s}`}>
      {icons[source] || icons.manual}
      {label[source] || source}
    </span>
  );
};

// ─── Status badge ─────────────────────────────────────────────────────────────
const StatusBadge = ({ active, approved }) => {
  if (!active) return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-red-500/10 text-red-400 border-red-500/20">
      <PowerOff size={10} /> Disabled
    </span>
  );
  if (!approved) return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-amber-500/10 text-amber-400 border-amber-500/20">
      <AlertTriangle size={10} /> Pending
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
      <CheckCircle size={10} /> Active
    </span>
  );
};

// ─── Code block with copy ─────────────────────────────────────────────────────
const CodeBlock = ({ code }) => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <div className="relative group">
      <pre className="bg-black/40 border border-white/10 rounded-xl p-4 text-xs font-mono text-text-secondary overflow-x-auto whitespace-pre-wrap max-h-64">
        {code}
      </pre>
      <button
        onClick={copy}
        className="absolute top-2 right-2 p-1.5 rounded-lg bg-white/5 border border-white/10 text-text-tertiary hover:text-white opacity-0 group-hover:opacity-100 transition-all"
      >
        {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
      </button>
    </div>
  );
};

// ─── Tool detail drawer ───────────────────────────────────────────────────────
const ToolDrawer = ({ tool, onClose, onApprove, onToggle, onDelete }) => {
  const isBuiltin = tool.source === 'builtin';
  const schema = tool.schema_json;
  const params = schema?.function?.parameters?.properties || {};

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      transition={{ duration: 0.2 }}
      className="fixed right-0 top-0 h-full w-full max-w-xl glass-panel border-l border-white/10 z-50 flex flex-col overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-start justify-between p-6 border-b border-white/10">
        <div className="flex-1 min-w-0 mr-4">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <SourceBadge source={tool.source} />
            <StatusBadge active={tool.is_active} approved={tool.is_approved} />
          </div>
          <h2 className="text-xl font-bold text-white font-mono mt-2 truncate">{tool.name}</h2>
          <p className="text-sm text-text-secondary mt-1 leading-relaxed">{tool.description || '—'}</p>
        </div>
        <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 text-text-tertiary hover:text-white transition-colors flex-shrink-0">
          <X size={18} />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Parameters */}
        {Object.keys(params).length > 0 && (
          <div>
            <h3 className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-3">Parameters</h3>
            <div className="space-y-2">
              {Object.entries(params).map(([pname, pinfo]) => (
                <div key={pname} className="flex items-center gap-3 glass-panel rounded-lg px-3 py-2">
                  <span className="font-mono text-sm text-white">{pname}</span>
                  <span className="text-xs text-text-tertiary bg-white/5 px-2 py-0.5 rounded font-mono">{pinfo?.type || 'any'}</span>
                  {schema?.function?.parameters?.required?.includes(pname) && (
                    <span className="text-[10px] text-red-400 font-semibold ml-auto">required</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Source code */}
        {tool.python_code && (
          <div>
            <h3 className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-3">Source Code</h3>
            <CodeBlock code={tool.python_code} />
          </div>
        )}

        {/* Raw schema */}
        {schema && (
          <div>
            <h3 className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-3">JSON Schema</h3>
            <CodeBlock code={JSON.stringify(schema, null, 2)} />
          </div>
        )}

        {tool.created_at && (
          <p className="text-xs text-text-tertiary">
            Created: {new Date(tool.created_at).toLocaleString()}
          </p>
        )}
      </div>

      {/* Actions footer */}
      {!isBuiltin && (
        <div className="p-4 border-t border-white/10 flex gap-2 flex-wrap">
          <button
            onClick={() => onApprove(tool.id, !tool.is_approved)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition-all ${
              tool.is_approved
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20'
            }`}
          >
            {tool.is_approved ? <XCircle size={14} /> : <CheckCircle size={14} />}
            {tool.is_approved ? 'Revoke' : 'Approve'}
          </button>
          <button
            onClick={() => onToggle(tool.id, !tool.is_active)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition-all ${
              tool.is_active
                ? 'bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20'
                : 'bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20'
            }`}
          >
            {tool.is_active ? <PowerOff size={14} /> : <Power size={14} />}
            {tool.is_active ? 'Disable' : 'Enable'}
          </button>
          <button
            onClick={() => onDelete(tool.id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 transition-all ml-auto"
          >
            <Trash2 size={14} /> Delete
          </button>
        </div>
      )}
    </motion.div>
  );
};

// ─── Create tool modal ────────────────────────────────────────────────────────
const CreateToolModal = ({ onClose, onCreated }) => {
  const [form, setForm] = useState({ name: '', description: '', code: '', test_kwargs: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      let test_kwargs = null;
      if (form.test_kwargs.trim()) {
        try { test_kwargs = JSON.parse(form.test_kwargs); }
        catch { setError('test_kwargs must be valid JSON'); setLoading(false); return; }
      }
      await createTool({ name: form.name, description: form.description, code: form.code, test_kwargs });
      onCreated();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="glass-panel border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Plus size={18} /> New Tool
          </h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 text-text-tertiary hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">Function name *</label>
            <input
              className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-text-tertiary focus:outline-none focus:border-white/30"
              placeholder="my_tool_name"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">Description *</label>
            <input
              className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-text-tertiary focus:outline-none focus:border-white/30"
              placeholder="What this tool does and when agents should use it"
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">Python code *</label>
            <textarea
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-text-tertiary focus:outline-none focus:border-white/30 resize-none"
              rows={10}
              placeholder={`def my_tool_name(query: str) -> str:\n    \"\"\"Fetch something useful.\"\"\"\n    import requests\n    return requests.get(f"https://api.example.com?q={query}").text`}
              value={form.code}
              onChange={e => setForm(f => ({ ...f, code: e.target.value }))}
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-text-secondary mb-1.5">
              Smoke-test kwargs <span className="font-normal text-text-tertiary">(optional JSON)</span>
            </label>
            <input
              className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-text-tertiary focus:outline-none focus:border-white/30"
              placeholder='{"query": "hello"}'
              value={form.test_kwargs}
              onChange={e => setForm(f => ({ ...f, test_kwargs: e.target.value }))}
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 px-4 py-2 rounded-lg border border-white/10 text-text-secondary hover:text-white hover:bg-white/5 transition-all text-sm">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg bg-white text-black font-semibold text-sm hover:bg-white/90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Plus size={14} />}
              {loading ? 'Creating…' : 'Create Tool'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
};

// ─── Tool card ────────────────────────────────────────────────────────────────
const ToolCard = ({ tool, onClick }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    onClick={onClick}
    className="glass-panel border border-white/10 rounded-xl p-4 cursor-pointer hover:border-white/20 hover:bg-white/[0.03] transition-all group"
  >
    <div className="flex items-start justify-between gap-3 mb-2">
      <div className="flex items-center gap-2 min-w-0">
        <div className="p-1.5 rounded-lg bg-white/5 border border-white/10 flex-shrink-0">
          <Code2 size={13} className="text-text-tertiary" />
        </div>
        <span className="font-mono text-sm font-semibold text-white truncate">{tool.name}</span>
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <SourceBadge source={tool.source} />
        <StatusBadge active={tool.is_active} approved={tool.is_approved} />
      </div>
    </div>
    <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed pl-8">
      {tool.description || <span className="italic text-text-tertiary">No description</span>}
    </p>
    {tool.schema_json?.function?.parameters?.properties && (
      <div className="flex flex-wrap gap-1 mt-2 pl-8">
        {Object.keys(tool.schema_json.function.parameters.properties).slice(0, 4).map(p => (
          <span key={p} className="text-[10px] font-mono text-text-tertiary bg-white/5 px-1.5 py-0.5 rounded">
            {p}
          </span>
        ))}
        {Object.keys(tool.schema_json.function.parameters.properties).length > 4 && (
          <span className="text-[10px] text-text-tertiary">+more</span>
        )}
      </div>
    )}
  </motion.div>
);

// ─── Main page ────────────────────────────────────────────────────────────────
const FILTERS = ['all', 'builtin', 'agent', 'manual'];

const ToolRepository = () => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  const fetchTools = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getTools();
      setTools(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTools(); }, [fetchTools]);

  const handleApprove = async (id, approved) => {
    await approveTool(id, approved);
    setTools(ts => ts.map(t => t.id === id ? { ...t, is_approved: approved } : t));
    setSelected(s => s?.id === id ? { ...s, is_approved: approved } : s);
  };

  const handleToggle = async (id, active) => {
    await toggleTool(id, active);
    setTools(ts => ts.map(t => t.id === id ? { ...t, is_active: active } : t));
    setSelected(s => s?.id === id ? { ...s, is_active: active } : s);
  };

  const handleDelete = async (id) => {
    await deleteTool(id);
    setTools(ts => ts.filter(t => t.id !== id));
    setSelected(null);
  };

  const visible = tools.filter(t => {
    const matchFilter = filter === 'all' || t.source === filter;
    const matchSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) ||
      (t.description || '').toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const counts = {
    all: tools.length,
    builtin: tools.filter(t => t.source === 'builtin').length,
    agent: tools.filter(t => t.source === 'agent').length,
    manual: tools.filter(t => t.source === 'manual').length,
  };

  const activeCount = tools.filter(t => t.is_active && t.is_approved).length;
  const pendingCount = tools.filter(t => !t.is_approved && t.source !== 'builtin').length;

  return (
    <div className="min-h-screen pb-20 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end mb-8 gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-2 text-white flex items-center gap-3">
            <Layers size={32} className="text-text-tertiary" />
            Tool Repository
          </h1>
          <p className="text-text-secondary text-sm sm:text-base">
            All tools available to agents — built-in, agent-created, and manually defined.
          </p>
        </div>

        <div className="flex gap-3 items-center flex-wrap">
          {/* Stats */}
          <div className="glass-panel px-4 py-2 rounded-lg flex flex-col items-center">
            <span className="text-xs text-text-tertiary uppercase tracking-wider">Total</span>
            <span className="text-xl font-bold text-white">{tools.length}</span>
          </div>
          <div className="glass-panel px-4 py-2 rounded-lg flex flex-col items-center">
            <span className="text-xs text-text-tertiary uppercase tracking-wider">Active</span>
            <span className="text-xl font-bold text-emerald-400">{activeCount}</span>
          </div>
          {pendingCount > 0 && (
            <div className="glass-panel px-4 py-2 rounded-lg flex flex-col items-center">
              <span className="text-xs text-text-tertiary uppercase tracking-wider">Pending</span>
              <span className="text-xl font-bold text-amber-400">{pendingCount}</span>
            </div>
          )}

          <button
            onClick={fetchTools}
            className="p-2.5 rounded-lg glass-panel border border-white/10 text-text-secondary hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>

          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white text-black text-sm font-semibold hover:bg-white/90 active:scale-95 transition-all shadow-lg shadow-white/10"
          >
            <Plus size={15} /> New Tool
          </button>
        </div>
      </div>

      {/* Filter + search bar */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex items-center gap-1 glass-panel rounded-xl p-1 border border-white/10">
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all capitalize flex items-center gap-1.5 ${
                filter === f ? 'bg-white text-black shadow' : 'text-text-secondary hover:text-white'
              }`}
            >
              {f === 'all' && <Layers size={12} />}
              {f === 'builtin' && <Box size={12} />}
              {f === 'agent' && <Bot size={12} />}
              {f === 'manual' && <Wrench size={12} />}
              {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${filter === f ? 'bg-black/20' : 'bg-white/10'}`}>
                {counts[f]}
              </span>
            </button>
          ))}
        </div>

        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          <input
            className="w-full bg-black/20 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-sm text-white placeholder-text-tertiary focus:outline-none focus:border-white/30 transition-colors"
            placeholder="Search tools…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-white">
              <X size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-panel border border-white/10 rounded-xl p-4 animate-pulse h-24" />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Wrench size={40} className="text-text-tertiary mb-4" />
          <p className="text-text-secondary text-lg font-medium mb-1">No tools found</p>
          <p className="text-text-tertiary text-sm">
            {search ? 'Try a different search term.' : 'Create your first tool to get started.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {visible.map(tool => (
            <ToolCard key={tool.id} tool={tool} onClick={() => setSelected(tool)} />
          ))}
        </div>
      )}

      {/* Drawer overlay */}
      <AnimatePresence>
        {selected && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
              onClick={() => setSelected(null)}
            />
            <ToolDrawer
              tool={selected}
              onClose={() => setSelected(null)}
              onApprove={handleApprove}
              onToggle={handleToggle}
              onDelete={handleDelete}
            />
          </>
        )}
      </AnimatePresence>

      {/* Create modal */}
      <AnimatePresence>
        {showCreate && (
          <CreateToolModal
            onClose={() => setShowCreate(false)}
            onCreated={fetchTools}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default ToolRepository;
