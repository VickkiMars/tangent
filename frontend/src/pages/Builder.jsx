import React, { useState, useCallback, useRef } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  BackgroundVariant,
  Panel,
  Handle,
  Position,
  useReactFlow
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Bot, Layers, CheckCircle, Trash2 } from 'lucide-react';

const STATUS_DRAFT = { border: '#0066FF', glow: 'rgba(0,102,255,0.25)', dot: '#0066FF', label: 'Draft' };

const EditableAgentNode = ({ id, data }) => {
  const { updateNodeData, setNodes } = useReactFlow();
  const s = STATUS_DRAFT;

  const handleChange = (e) => {
    updateNodeData(id, { [e.target.name]: e.target.value });
  };

  const handleToolChange = (e) => {
    const rawVal = e.target.value;
    const toolsArr = rawVal.split(',').map(t => t.trim()).filter(Boolean);
    updateNodeData(id, { tools: toolsArr, _toolsInput: rawVal });
  };

  const deleteNode = () => {
    setNodes((nds) => nds.filter((n) => n.id !== id));
  };

  return (
    <div
      style={{
        background: '#0E0E0E',
        border: `1px solid ${s.border}`,
        boxShadow: `0 0 20px ${s.glow}, inset 0 0 0 1px rgba(255,255,255,0.03)`,
        borderRadius: 16,
        padding: '16px 18px',
        minWidth: 260,
        maxWidth: 320,
        position: 'relative',
        fontFamily: 'Inter, sans-serif',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: s.border, border: 'none', width: 8, height: 8 }} />
      <Handle type="source" position={Position.Right} style={{ background: s.border, border: 'none', width: 8, height: 8 }} />

      {/* Delete Button */}
      <button onClick={deleteNode} style={{ position: 'absolute', top: 12, right: 12, color: '#EF4444', backgroundColor: 'transparent', border: 'none', cursor: 'pointer' }} title="Delete Agent">
        <Trash2 size={13} />
      </button>

      {/* Agent ID */}
      <input
        name="agent_id"
        value={data.agent_id || ''}
        placeholder="Agent ID"
        onChange={handleChange}
        style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 9, color: s.border,
          marginBottom: 6, marginRight: 24,
          background: 'transparent', border: 'none', outline: 'none', width: '100%'
        }}
      />

      {/* Task label */}
      <input
        name="label"
        value={data.label || ''}
        placeholder="Task Label"
        onChange={handleChange}
        style={{ color: '#FFFFFF', fontSize: 13, fontWeight: 600, marginBottom: 10, lineHeight: 1.35, background: 'transparent', border: 'none', outline: 'none', borderBottom: '1px solid rgba(255,255,255,0.2)', width: '100%' }}
      />

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

      {/* Persona Prompt */}
      <textarea
        name="persona_prompt"
        value={data.persona_prompt || ''}
        placeholder="System Persona / Prompt..."
        onChange={handleChange}
        rows={3}
        className="nodrag"
        style={{
          width: '100%', background: 'rgba(255,255,255,0.05)', color: '#A1A1AA', fontSize: 10,
          padding: '6px 8px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', outline: 'none', marginBottom: 8,
          resize: 'vertical', fontFamily: "'JetBrains Mono', monospace"
        }}
      />

      {/* Tools Input */}
      <input
        name="_toolsInput"
        value={data._toolsInput !== undefined ? data._toolsInput : (data.tools || []).join(', ')}
        placeholder="Tools (comma separated)"
        onChange={handleToolChange}
        className="nodrag"
        style={{
          width: '100%', background: 'rgba(255,255,255,0.05)', color: '#FF8A00', fontSize: 10,
          padding: '4px 8px', borderRadius: 8, border: '1px solid rgba(255,138,0,0.3)', outline: 'none', marginBottom: 8,
          fontFamily: "'JetBrains Mono', monospace"
        }}
      />

      {/* Model Input */}
      <input
        name="model"
        value={data.model || ''}
        placeholder="Model (e.g. gemini-3.1-flash-lite-preview)"
        onChange={handleChange}
        className="nodrag"
        style={{
          width: '100%', background: 'transparent', color: '#71717A', fontSize: 10,
          border: 'none', borderBottom: '1px dotted rgba(255,255,255,0.2)', outline: 'none',
          fontFamily: "'JetBrains Mono', monospace"
        }}
      />
    </div>
  );
};

const nodeTypes = { agent: EditableAgentNode };

export default function Builder() {
  const reactFlowWrapper = useRef(null);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  const onNodesChange = useCallback((changes) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((params) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#71717A', strokeWidth: 1.5 } }, eds)), []);

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (typeof type === 'undefined' || !type) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: `agent_${nodes.length + 1}`,
        type,
        position,
        data: { 
          agent_id: `CustomAgent_${nodes.length + 1}`, 
          label: 'New Node', 
          tools: ['search_internet'],
          persona_prompt: 'System prompt goes here',
          model: 'gemini-3.1-flash-lite-preview',
          status: 'running' // Just for preview styles
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance, nodes]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const exportBlueprint = () => {
    const payload = JSON.stringify({ nodes, edges }, null, 2);
    navigator.clipboard.writeText(payload);
    alert('Blueprint exported to clipboard!');
  };

  return (
    <div className="h-[calc(100dvh-5rem)] sm:h-[calc(100vh-6rem)] w-full max-w-[1920px] mx-auto flex flex-col lg:flex-row gap-4 lg:gap-6 p-4 lg:p-6 font-sans text-sm bg-black" style={{ color: '#A1A1AA' }}>
      
      {/* Node Palette Sidebar */}
      <div className="w-full lg:w-72 bg-[#0E0E0E] rounded-[24px] border border-white/[0.07] p-6 flex flex-col gap-6 shadow-2xl flex-shrink-0">
        <div>
          <h2 className="text-white font-semibold text-lg flex items-center gap-2 mb-1">
            <Layers className="text-[#FF8A00]" size={18} /> Node Palette
          </h2>
          <p className="text-xs text-[#71717A]">Drag components onto the canvas to construct your workflow.</p>
        </div>

        <div className="flex flex-col gap-3">
          <div 
            className="flex items-center gap-3 p-4 bg-[#1A1A1A] border border-white/10 rounded-[16px] cursor-grab hover:bg-[#252525] hover:border-white/20 transition-all shadow-inner"
            onDragStart={(event) => onDragStart(event, 'agent')} 
            draggable
          >
            <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
              <Bot className="text-white" size={16} />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Ephemeral Agent</p>
              <p className="text-[10px] text-[#71717A]">Isolated execution container</p>
            </div>
          </div>
        </div>

        <div className="mt-auto space-y-3">
          <button 
            onClick={exportBlueprint}
            className="w-full py-3 rounded-full bg-white text-black font-bold text-[13px] tracking-wide hover:bg-[#E2E8F0] transition-colors shadow-[0_0_15px_rgba(255,255,255,0.25)] flex items-center justify-center gap-2"
          >
            <CheckCircle size={15} /> Export Blueprint
          </button>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-grow relative bg-[#0E0E0E] rounded-[24px] border border-white/[0.07] shadow-2xl overflow-hidden" ref={reactFlowWrapper}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
            className="react-flow-dark"
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="rgba(255,255,255,0.06)" />
            <Controls title="Controls" className="!bg-[#1A1A1A] !border-white/10 !fill-white shadow-xl" />
            <Panel position="top-right" className="bg-[#1A1A1A] border border-white/10 px-4 py-2 rounded-full shadow-xl">
              <span className="text-[10px] font-mono text-[#71717A] tracking-widest uppercase">Visual Builder Active</span>
            </Panel>
          </ReactFlow>
        </ReactFlowProvider>
      </div>
    </div>
  );
}
