import { useState } from 'react';
import { ChevronRight } from 'lucide-react';
import Installation from '../components/docs/Installation';
import QuickStart from '../components/docs/QuickStart';
import Architecture from '../components/docs/Architecture';
import Providers from '../components/docs/Providers';
import Memory from '../components/docs/Memory';
import Tools from '../components/docs/Tools';
import RateLimiting from '../components/docs/RateLimiting';

const Docs = () => {
  const [activeSection, setActiveSection] = useState('installation');

  const menu = [
    { 
      id: 'getting-started', 
      title: 'Getting Started', 
      items: [
        { id: 'installation', label: 'Installation' },
        { id: 'quick-start', label: 'Quick Start' },
        { id: 'architecture', label: 'Architecture' }
      ] 
    },
    { 
      id: 'core-concepts', 
      title: 'Core Concepts', 
      items: [
        { id: 'providers', label: 'Providers' },
        { id: 'memory', label: 'Memory' },
        { id: 'tools', label: 'Tools' }
      ] 
    },
    { 
      id: 'guides', 
      title: 'Guides', 
      items: [
        { id: 'rate-limiting', label: 'Rate Limiting' }
      ] 
    },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'installation':
        return <Installation />;
      case 'quick-start':
        return <QuickStart />;
      case 'architecture':
        return <Architecture />;
      case 'providers':
        return <Providers />;
      case 'memory':
        return <Memory />;
      case 'tools':
        return <Tools />;
      case 'rate-limiting':
        return <RateLimiting />;
      default:
        return <Installation />;
    }
  };

  const getBreadcrumbs = () => {
    for (const section of menu) {
      const item = section.items.find((i) => i.id === activeSection);
      if (item) {
        return (
          <>
            {section.title} <ChevronRight size={12} /> {item.label}
          </>
        );
      }
    }
    return null;
  };

  return (
    <div className="max-w-7xl mx-auto py-8 sm:py-10 flex flex-col md:flex-row gap-8 md:gap-12 min-h-screen">
      {/* Mobile section picker */}
      <div className="md:hidden">
        <select
          value={activeSection}
          onChange={e => setActiveSection(e.target.value)}
          className="w-full bg-card border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-white/30 appearance-none"
          style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2371717A' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E\")", backgroundRepeat: 'no-repeat', backgroundPosition: 'right 1rem center' }}
        >
          {menu.map(section => (
            <optgroup key={section.id} label={section.title}>
              {section.items.map(item => (
                <option key={item.id} value={item.id}>{item.label}</option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Desktop sidebar */}
      <aside className="w-56 hidden md:block flex-shrink-0 sticky top-32 h-fit">
        {menu.map((section) => (
          <div key={section.id} className="mb-8">
            <h4 className="text-xs font-bold text-text-tertiary uppercase tracking-wider mb-4">{section.title}</h4>
            <ul className="space-y-2">
              {section.items.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => setActiveSection(item.id)}
                    className={`text-sm transition-colors text-left w-full ${activeSection === item.id ? 'text-white font-semibold' : 'text-text-secondary hover:text-white'}`}
                  >
                    {item.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </aside>

      {/* Main Content */}
      <div className="flex-grow min-w-0 max-w-3xl">
        <div className="mb-6 text-text-tertiary text-sm font-mono flex items-center gap-2 flex-wrap">
          Docs <ChevronRight size={12} /> {getBreadcrumbs()}
        </div>
        {renderContent()}
      </div>
    </div>
  );
};

export default Docs;
