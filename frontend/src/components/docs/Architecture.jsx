const Architecture = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Architecture</h1>
    <p className="text-text-secondary text-base sm:text-lg mb-6 sm:mb-8">nagent adopts a Just-In-Time (JIT) compilation approach for orchestrating ephemeral AI agents.</p>
    
    <div className="space-y-8">
      <div>
        <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">1. Meta-Agent Architect</h3>
        <p className="text-text-secondary text-lg">The system's "brain." It analyzes a user's objective and "compiles" it into a SynthesisManifest. This manifest describes the topology of agents required, their distinct personas, and the precise tools they need.</p>
      </div>

      <div>
        <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">2. JIT Compiler</h3>
        <p className="text-text-secondary text-lg">The execution engine. It resolves dependencies, spawns ephemeral agents, executes the agent loop, and garbage collects the agent instance immediately after task completion.</p>
      </div>
    </div>
  </div>
);

export default Architecture;
