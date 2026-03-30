import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Copy, Clock, DollarSign, Cpu } from 'lucide-react';

// ─── Status palette ────────────────────────────────────────────────────────────
const STATUS = {
  completed: { border: '#10B981', glow: 'rgba(16,185,129,0.25)',  dot: '#10B981', label: 'Completed' },
  running:   { border: '#0066FF', glow: 'rgba(0,102,255,0.25)',   dot: '#0066FF', label: 'Running'   },
  pending:   { border: '#71717A', glow: 'rgba(113,113,122,0.10)', dot: '#71717A', label: 'Pending'   },
  hibernate: { border: '#FF8A00', glow: 'rgba(255,138,0,0.25)',   dot: '#FF8A00', label: 'Waiting'   },
  failed:    { border: '#EF4444', glow: 'rgba(239,68,68,0.25)',   dot: '#EF4444', label: 'Failed'    },
};

// ─── Custom Agent Node styling ────────────────────────────────────────────────
export const AgentNode = ({ data }) => {
  const s = STATUS[data.status] || STATUS.pending;

  return (
    <div
      style={{
        background: '#0E0E0E',
        border: `1px solid ${s.border}`,
        boxShadow: `0 0 20px ${s.glow}, inset 0 0 0 1px rgba(255,255,255,0.03)`,
        borderRadius: 16,
        padding: '16px 18px',
        minWidth: 220,
        maxWidth: 260,
        position: 'relative',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: s.border, border: 'none', width: 8, height: 8, boxShadow: `0 0 6px ${s.border}` }}
      />

      {/* Status dot */}
      <span
        style={{
          position: 'absolute', top: 14, right: 14,
          width: 8, height: 8, borderRadius: '50%',
          background: s.dot, boxShadow: `0 0 8px ${s.dot}`,
          display: 'inline-block',
        }}
      />

      {/* Agent ID */}
      <p
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 9, color: s.border,
          marginBottom: 6, marginRight: 18,
          letterSpacing: '0.04em', wordBreak: 'break-all',
        }}
      >
        {data.agent_id}
      </p>

      {/* Task label */}
      <p style={{ color: '#FFFFFF', fontSize: 13, fontWeight: 600, marginBottom: 10, lineHeight: 1.35 }}>
        {data.label}
      </p>

      {/* Status badge */}
      <span
        style={{
          display: 'inline-block',
          fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
          letterSpacing: '0.1em', padding: '2px 8px',
          borderRadius: 999, marginBottom: 10,
          color: s.dot,
          border: `1px solid ${s.border}40`,
          background: `${s.border}10`,
        }}
      >
        {s.label}
      </span>

      {/* Tool badges */}
      {data.tools && data.tools.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
          {data.tools.slice(0, 3).map((t) => (
            <span
              key={t}
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 8, padding: '2px 7px', borderRadius: 999,
                color: '#FF8A00',
                border: '1px solid rgba(255,138,0,0.30)',
                background: 'rgba(255,138,0,0.08)',
              }}
            >
              {t}
            </span>
          ))}
          {data.tools.length > 3 && (
            <span style={{ fontSize: 9, color: '#71717A', alignSelf: 'center' }}>
              +{data.tools.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Analytics Bar */}
      {data.analytics && (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#A1A1AA', fontFamily: "'JetBrains Mono', monospace" }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 3 }} title="Cost (USD)">
            <DollarSign size={10} color="#10B981" /> ${data.analytics.cost_usd?.toFixed(4) || '0.0000'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 3 }} title="Tokens (Prompt+Completion)">
            <Cpu size={10} color="#0066FF" /> {(data.analytics.tokens_prompt || 0) + (data.analytics.tokens_completion || 0)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 3 }} title="Execution Time (Seconds)">
            <Clock size={10} color="#FF8A00" /> {data.analytics.lifetime_seconds?.toFixed(1) || '0.0'}s
          </div>
        </div>
      )}

      {/* Copy as LangChain Code Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          const code = `
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="${data.model || 'gpt-4o'}")
tools = [${(data.tools || []).map(t => `"${t}"`).join(', ')}]

agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, 
    verbose=True,
    agent_kwargs={"system_message": """${data.persona_prompt || 'You are an autonomous agent.'}"""}
)
`.trim();
          navigator.clipboard.writeText(code);
          alert("Copied LangChain code to clipboard!");
        }}
        title="Copy as LangChain Code"
        style={{
          position: 'absolute', bottom: 12, right: 12,
          background: 'transparent', border: 'none', cursor: 'pointer',
          color: '#71717A', padding: '4px',
        }}
        onMouseEnter={(e) => e.currentTarget.style.color = '#FFFFFF'}
        onMouseLeave={(e) => e.currentTarget.style.color = '#71717A'}
      >
        <Copy size={12} />
      </button>

      <Handle
        type="source"
        position={Position.Right}
        style={{ background: s.border, border: 'none', width: 8, height: 8, boxShadow: `0 0 6px ${s.border}` }}
      />
    </div>
  );
}

const nodeTypes = { agent: AgentNode };

// ─── Edge style ────────────────────────────────────────────────────────────────
const defaultEdgeOptions = {
  style: { stroke: 'rgba(255,255,255,0.15)', strokeWidth: 1.5, strokeDasharray: '5 4' },
  animated: false,
};

const activeEdgeOptions = {
  style: { stroke: '#FFFFFF', strokeWidth: 1.5, strokeDasharray: '5 4' },
  animated: true,
};

// ─── Layout helper: assign positions by dependency depth ──────────────────────
function layoutNodes(rawNodes, rawEdges) {
  const HGAP = 300, VGAP = 140;

  // Build in-degree and children maps
  const childrenOf  = {};
  const parentsOf   = {};
  rawNodes.forEach(n => { childrenOf[n.id] = []; parentsOf[n.id] = []; });
  rawEdges.forEach(e => {
    childrenOf[e.source]?.push(e.target);
    parentsOf[e.target]?.push(e.source);
  });

  // Topological BFS (Kahn's algorithm) to assign column (depth)
  const depth = {};
  const queue = rawNodes.filter(n => parentsOf[n.id].length === 0).map(n => n.id);
  queue.forEach(id => { depth[id] = 0; });

  while (queue.length) {
    const id = queue.shift();
    for (const child of (childrenOf[id] || [])) {
      depth[child] = Math.max(depth[child] ?? 0, (depth[id] ?? 0) + 1);
      queue.push(child);
    }
  }

  // Group by depth
  const cols = {};
  rawNodes.forEach(n => {
    const d = depth[n.id] ?? 0;
    if (!cols[d]) cols[d] = [];
    cols[d].push(n.id);
  });

  // Assign positions
  const posMap = {};
  Object.entries(cols).forEach(([col, ids]) => {
    const x = parseInt(col) * HGAP;
    const totalH = ids.length * VGAP;
    ids.forEach((id, row) => {
      posMap[id] = { x, y: row * VGAP - totalH / 2 };
    });
  });

  return rawNodes.map(n => ({ ...n, position: posMap[n.id] || { x: 0, y: 0 } }));
}

// ─── Mock manifest (shown when no real data is passed) ────────────────────────
const MOCK_NODES_RAW = [
  { id: 'task_lookup', type: 'agent', data: { agent_id: 'order_lookup.47a9f3', label: 'Order Lookup', status: 'completed', tools: ['get_order', 'validate_return'] } },
  { id: 'task_refund', type: 'agent', data: { agent_id: 'refund_processor.b8e4d1', label: 'Process Refund', status: 'running', tools: ['process_refund', 'send_receipt'] } },
  { id: 'task_notify', type: 'agent', data: { agent_id: 'notification_sender.c2f5a7', label: 'Send Notification', status: 'pending', tools: ['send_email', 'send_sms'] } },
];

const MOCK_EDGES_RAW = [
  { id: 'e1', source: 'task_lookup', target: 'task_refund' },
  { id: 'e2', source: 'task_refund', target: 'task_notify' },
];

// ─── Convert WorkflowState → ReactFlow nodes+edges ────────────────────────────
function workflowToGraph(tasks, manifest, analytics) {
  if (!tasks || tasks.length === 0) return { nodes: MOCK_NODES_RAW, edges: MOCK_EDGES_RAW };

  const blueprintMap = {};
  manifest?.blueprints?.forEach(bp => { blueprintMap[bp.target_task_id] = bp; });

  const analyticsMap = {};
  analytics?.forEach(a => { analyticsMap[a.target_task_id] = a; });

  const nodes = tasks.map(t => {
    const bp = blueprintMap[t.task_id] || {};
    const a = analyticsMap[t.task_id];
    return {
      id: t.task_id,
      type: 'agent',
      data: {
        agent_id: bp.agent_id || t.task_id.split(':').slice(1).join(':') || t.task_id,
        label: (bp.target_task_id || t.task_id).split(':').slice(1).join(':') || (bp.target_task_id || t.task_id),
        status: a ? 'completed' : (t.status || 'pending'),
        tools: bp.injected_tools || t.required_capabilities || [],
        persona_prompt: bp.persona_prompt || "",
        model: bp.model || t.model || "gpt-4o",
        analytics: a || null,
      },
    };
  });

  const edges = [];
  tasks.forEach(t => {
    (t.dependencies || []).forEach((depId, i) => {
      edges.push({ id: `e_${depId}_${t.task_id}_${i}`, source: depId, target: t.task_id });
    });
  });

  return { nodes, edges };
}

// ─── GraphView ─────────────────────────────────────────────────────────────────
/**
 * Props:
 *   tasks    – SubTask[]   (from WorkflowState.tasks, optional – uses mock data if absent)
 *   manifest – SynthesisManifest (optional)
 *   analytics - Array of Agent Analytics objects
 */
export default function GraphView({ tasks, manifest, analytics }) {
  const { nodes: rawNodes, edges: rawEdges } = useMemo(
    () => workflowToGraph(tasks, manifest, analytics),
    [tasks, manifest, analytics]
  );

  const nodes = useMemo(() => layoutNodes(rawNodes, rawEdges), [rawNodes, rawEdges]);

  // Edges: animate those that connect a completed source to a non-completed target
  const completedIds = new Set(rawNodes.filter(n => n.data?.status === 'completed').map(n => n.id));
  const edges = rawEdges.map(e => ({
    ...e,
    ...(completedIds.has(e.source) ? activeEdgeOptions : defaultEdgeOptions),
  }));

  return (
    <div className="w-full h-full" style={{ background: '#000' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.3}
        maxZoom={1.6}
        proOptions={{ hideAttribution: true }}
        style={{ background: '#000' }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="rgba(255,255,255,0.06)"
          style={{ background: '#000' }}
        />
        <Controls
          style={{
            background: '#0E0E0E',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 12,
            overflow: 'hidden',
          }}
          showInteractive={false}
        />
      </ReactFlow>

      {/* Legend */}
      <div
        className="absolute bottom-4 left-4 flex flex-wrap gap-3 px-4 py-3 rounded-[14px] border border-white/[0.07]"
        style={{ background: 'rgba(14,14,14,0.85)', backdropFilter: 'blur(12px)' }}
      >
        {Object.entries(STATUS).filter(([k]) => ['completed','running','pending','hibernate','failed'].includes(k)).map(([key, s]) => (
          <div key={key} className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ background: s.dot, boxShadow: `0 0 5px ${s.dot}` }} />
            <span className="text-[9px] text-[#71717A] uppercase font-bold tracking-widest">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
