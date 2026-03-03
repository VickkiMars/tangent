const Tools = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Tools</h1>
    <p className="text-text-secondary text-lg mb-8 leading-relaxed">
      The Universal Tool Registry is a facade over various tool ecosystems, allowing the Meta-Agent to select the best tool for the job.
    </p>
    <p className="text-text-secondary text-lg leading-relaxed">
      You can integrate tools from multiple providers (Composio, LangChain, CrewAI, Custom) into a strictly scoped toolkit for each ephemeral agent.
    </p>
  </div>
);

export default Tools;
