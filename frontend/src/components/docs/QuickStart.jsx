const QuickStart = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Quick Start</h1>
    <p className="text-text-secondary text-lg mb-8 leading-relaxed">
      Initialize core systems and architect your first workflow using the Meta-Agent and JIT Compiler.
    </p>

    <div className="bg-card border border-white/10 rounded-xl p-6 mb-8 relative">
       <div className="absolute top-4 right-4 text-xs text-text-tertiary font-mono">python</div>
       <pre className="text-sm font-mono text-text-secondary overflow-x-auto">
         <span className="text-orange">from</span> nagent.meta <span className="text-orange">import</span> MetaAgent<br/>
         <span className="text-orange">from</span> nagent.compiler <span className="text-orange">import</span> JITCompiler<br/>
         <span className="text-orange">from</span> nagent.blackboard <span className="text-orange">import</span> EventBlackboard<br/><br/>
         # Initialize Core Systems<br/>
         blackboard = <span className="text-blue-400">EventBlackboard</span>()<br/>
         meta = <span className="text-blue-400">MetaAgent</span>()<br/>
         compiler = <span className="text-blue-400">JITCompiler</span>(blackboard=blackboard)<br/><br/>
         # Execute Workflow<br/>
         manifest = meta.<span className="text-blue-400">architect_workflow</span>(<br/>
         &nbsp;&nbsp;user_objective=<span className="text-success">"Research Quantum Computing"</span>,<br/>
         &nbsp;&nbsp;available_tool_names=[<span className="text-success">"web_search"</span>]<br/>
         )<br/>
         <span className="text-orange">await</span> compiler.<span className="text-blue-400">execute_manifest</span>(manifest)
       </pre>
    </div>
  </div>
);

export default QuickStart;
