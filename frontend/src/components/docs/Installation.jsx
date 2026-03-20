const CodeBlock = ({ lang = 'bash', children }) => (
  <div className="bg-card border border-white/10 rounded-xl p-6 mb-6 relative group overflow-x-auto">
    <div className="absolute top-4 right-4 text-xs text-text-tertiary font-mono">{lang}</div>
    <pre className="text-white font-mono text-sm whitespace-pre">{children}</pre>
  </div>
);

const Step = ({ number, title, children }) => (
  <div className="mb-10">
    <div className="flex items-center gap-3 mb-4">
      <span className="w-7 h-7 rounded-full bg-white/10 text-white text-xs font-bold flex items-center justify-center flex-shrink-0">{number}</span>
      <h3 className="text-white font-semibold text-lg">{title}</h3>
    </div>
    {children}
  </div>
);

const Installation = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Installation</h1>
    <p className="text-text-secondary text-lg mb-10 leading-relaxed">
      Get tangent running locally in a few minutes. You'll need Python 3.10+, Docker, and an API key for at least one LLM provider.
    </p>

    <Step number="1" title="Clone the repository">
      <CodeBlock>git clone https://github.com/your-org/tangent.git{'\n'}cd tangent</CodeBlock>
    </Step>

    <Step number="2" title="Configure environment variables">
      <p className="text-text-secondary text-sm mb-4">
        Copy the example env file and fill in your API keys:
      </p>
      <CodeBlock>cp backend/.env.example backend/.env</CodeBlock>
      <p className="text-text-secondary text-sm mb-4">
        Edit <code className="text-white bg-white/10 px-1.5 py-0.5 rounded text-xs">backend/.env</code> with your credentials:
      </p>
      <CodeBlock lang="env">{`OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
COMPOSIO_API_KEY=          # optional
API_KEY=nagent-dev-key     # authenticates requests to the backend`}</CodeBlock>
    </Step>

    <Step number="3" title="Start the services">
      <CodeBlock>docker compose up --build</CodeBlock>
      <p className="text-text-secondary text-sm mb-2">This starts three services:</p>
      <ul className="text-text-secondary text-sm space-y-1 mb-4 list-none">
        <li><span className="text-white font-mono text-xs bg-white/10 px-1.5 py-0.5 rounded">app</span> — FastAPI backend on <span className="text-white font-mono text-xs">http://localhost:8000</span></li>
        <li><span className="text-white font-mono text-xs bg-white/10 px-1.5 py-0.5 rounded">redis</span> — Event bus &amp; state on port <span className="text-white font-mono text-xs">6380</span></li>
        <li><span className="text-white font-mono text-xs bg-white/10 px-1.5 py-0.5 rounded">postgres</span> — Persistent storage on port <span className="text-white font-mono text-xs">5433</span></li>
      </ul>
    </Step>

    <Step number="4" title="Verify the installation">
      <CodeBlock>{`curl -H "X-API-Key: nagent-dev-key" http://localhost:8000/health`}</CodeBlock>
      <p className="text-text-secondary text-sm">A successful response confirms the backend is up and connected to Redis and Postgres.</p>
    </Step>

    <div className="border border-white/10 rounded-xl p-6 mb-6">
      <h4 className="text-white font-semibold mb-3 text-sm">Running without Docker</h4>
      <p className="text-text-secondary text-sm mb-4">
        You can run the backend directly if you have Redis and Postgres available separately:
      </p>
      <CodeBlock>{`cd backend\npip install -r requirements.txt\nuvicorn main:app --reload --port 8000`}</CodeBlock>
      <p className="text-text-secondary text-sm">
        Start only the infrastructure with: <code className="text-white bg-white/10 px-1.5 py-0.5 rounded text-xs">docker compose up redis postgres</code>
      </p>
    </div>
  </div>
);

export default Installation;
