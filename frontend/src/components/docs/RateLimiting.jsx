const RateLimiting = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Rate Limiting</h1>
    <p className="text-text-secondary text-lg mb-8 leading-relaxed">
      Learn how to handle rate limits effectively when your ephemeral agents interact with external LLM providers and APIs.
    </p>
    <p className="text-text-secondary text-lg leading-relaxed">
      The JIT Compiler intelligently manages rate limits by pausing agent execution and re-queuing events on the Event Blackboard when limits are reached, ensuring robust long-running workflows.
    </p>
  </div>
);

export default RateLimiting;
