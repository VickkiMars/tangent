const Providers = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Providers</h1>
    <p className="text-text-secondary text-lg mb-8 leading-relaxed">
      nagent supports multiple LLM providers out of the box. You can configure which provider the Meta-Agent and JIT Compiler use for orchestration and execution.
    </p>
    <ul className="list-disc pl-6 space-y-2 text-text-secondary text-lg">
      <li><strong>OpenAI</strong>: GPT-4o, GPT-3.5-Turbo</li>
      <li><strong>Anthropic</strong>: Claude 3.5 Sonnet, Opus</li>
      <li><strong>Local Models</strong>: Llama, Mistral (via Ollama or vLLM)</li>
    </ul>
  </div>
);

export default Providers;
