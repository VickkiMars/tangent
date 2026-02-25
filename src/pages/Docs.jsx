import { useState } from 'react';
import { ChevronRight, FileText, Code } from 'lucide-react';

const Docs = () => {
  const [activeSection, setActiveSection] = useState('getting-started');

  const menu = [
    { id: 'getting-started', title: 'Getting Started', items: ['Installation', 'Quick Start', 'Architecture'] },
    { id: 'core-concepts', title: 'Core Concepts', items: ['Agents', 'Providers', 'Memory', 'Tools'] },
    { id: 'guides', title: 'Guides', items: ['Building a Chatbot', 'Rate Limiting', 'Deploying'] },
    { id: 'api', title: 'API Reference', items: ['Client', 'Types', 'Errors'] },
  ];

  return (
    <div className="max-w-7xl mx-auto py-10 px-6 flex gap-12 min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 hidden md:block sticky top-32 h-fit">
        {menu.map((section) => (
          <div key={section.id} className="mb-8">
            <h4 className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-4">{section.title}</h4>
            <ul className="space-y-2">
              {section.items.map((item) => (
                <li key={item}>
                  <button className="text-sm text-text-secondary hover:text-white transition-colors text-left w-full">
                    {item}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </aside>

      {/* Main Content */}
      <div className="flex-grow max-w-3xl">
        <div className="mb-4 text-white text-sm font-mono flex items-center gap-2">
          Docs <ChevronRight size={12} /> Getting Started <ChevronRight size={12} /> Installation
        </div>
        <h1 className="text-4xl font-bold text-white mb-6">Installation</h1>
        <p className="text-text-secondary text-lg mb-8 leading-relaxed">
          Get started with Spectrum by installing the core SDK. We support Node.js v18 and above.
        </p>

        <div className="bg-card border border-white/10 rounded-xl p-6 mb-8 relative group">
          <div className="absolute top-4 right-4 text-xs text-text-tertiary font-mono">bash</div>
          <code className="text-white font-mono text-sm">
            npm install @spectrum/sdk
          </code>
        </div>

        <h2 className="text-2xl font-bold text-white mb-4 mt-12">Configuration</h2>
        <p className="text-text-secondary mb-6">
          Create a <code className="bg-white/10 px-1.5 py-0.5 rounded text-white text-sm">spectrum.config.ts</code> file in your project root.
        </p>

        <div className="bg-card border border-white/10 rounded-xl p-6 mb-8 relative">
           <div className="absolute top-4 right-4 text-xs text-text-tertiary font-mono">typescript</div>
           <pre className="text-sm font-mono text-text-secondary overflow-x-auto">
             <span className="text-orange">import</span> &#123; defineConfig &#125; <span className="text-orange">from</span> <span className="text-success">'@spectrum/sdk'</span>;<br/><br/>
             <span className="text-orange">export</span> <span className="text-orange">default</span> <span className="text-blue-400">defineConfig</span>(&#123;<br/>
             &nbsp;&nbsp;projectId: <span className="text-success">'proj_123xyz'</span>,<br/>
             &nbsp;&nbsp;region: <span className="text-success">'us-east-1'</span>,<br/>
             &nbsp;&nbsp;providers: &#91;<span className="text-success">'openai'</span>, <span className="text-success">'anthropic'</span>&#93;<br/>
             &#125;);
           </pre>
        </div>
      </div>
    </div>
  );
};

export default Docs;
