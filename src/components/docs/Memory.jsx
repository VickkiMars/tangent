const Memory = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Memory</h1>
    <p className="text-text-secondary text-lg mb-8 leading-relaxed">
      Agents in nagent are strictly stateless. All memory and state are persisted to a central, immutable Event Blackboard.
    </p>
    <p className="text-text-secondary text-lg leading-relaxed">
      Every interaction is an immutable event, enabling replayability, auditability, and long-running workflows. The blackboard currently supports in-memory storage, with Redis-backed persistence planned for the roadmap.
    </p>
  </div>
);

export default Memory;
