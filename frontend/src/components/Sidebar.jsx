import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Terminal, PenTool, Clock } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  const links = [
    { name: 'Workspace', path: '/workspace', icon: Terminal },
    { name: 'Builder', path: '/builder', icon: PenTool },
    { name: 'History', path: '/history', icon: Clock },
  ];

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="peer fixed left-6 top-6 bottom-6 w-20 hover:w-64
        bg-white/[0.04] backdrop-blur-3xl
        border border-white/[0.08] hover:border-white/[0.12]
        z-[110] pt-24 hidden md:flex flex-col items-center hover:items-stretch
        px-3 gap-2 transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]
        rounded-[32px] group overflow-hidden
        shadow-[0_8px_40px_rgba(0,0,0,0.7),0_2px_8px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.07),inset_0_-1px_0_rgba(0,0,0,0.3)]">

        {/* Top gloss highlight */}
        <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-white/[0.06] via-white/[0.02] to-transparent pointer-events-none rounded-t-[32px]" />

        {/* Side edge shimmer */}
        <div className="absolute inset-y-0 left-0 w-px bg-gradient-to-b from-transparent via-white/10 to-transparent pointer-events-none" />

        {/* Bottom vignette */}
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black/50 via-black/10 to-transparent pointer-events-none rounded-b-[32px]" />

        {/* Inner ring */}
        <div className="absolute inset-0 rounded-[32px] ring-1 ring-inset ring-white/[0.04] pointer-events-none" />

        <div className="mb-8 px-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 whitespace-nowrap">
          <h3 className="text-[10px] font-bold text-white/25 uppercase tracking-[0.2em]">Platform</h3>
        </div>

        {links.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            className={`flex items-center gap-4 px-3 py-4 rounded-2xl text-sm font-medium transition-all duration-300 group/link relative w-full ${
              isActive(link.path)
                ? 'bg-white/90 text-black shadow-[0_4px_24px_rgba(255,255,255,0.15),inset_0_1px_0_rgba(255,255,255,0.9)]'
                : 'text-white/40 hover:text-white hover:bg-white/[0.07] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]'
            }`}
          >
            <div className="min-w-[32px] flex justify-center">
              <link.icon
                size={22}
                className={isActive(link.path) ? 'text-black' : 'group-hover/link:scale-110 transition-transform'}
              />
            </div>
            <span className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 truncate font-semibold">
              {link.name}
            </span>

            {/* Tooltip when collapsed */}
            <div className="group-hover:hidden absolute left-full ml-4 px-2.5 py-1.5 bg-white/10 backdrop-blur-2xl text-white text-[10px] font-bold rounded-xl border border-white/10 opacity-0 group-hover/link:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50 shadow-[0_4px_16px_rgba(0,0,0,0.5)]">
              {link.name}
            </div>
          </Link>
        ))}

        <div className="mt-auto pb-8 px-4 opacity-0 group-hover:opacity-100 transition-opacity duration-500 text-center whitespace-nowrap">
          <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06] backdrop-blur-sm shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
            <p className="text-[10px] text-white/25 mb-1 uppercase tracking-tight font-bold">Secure</p>
            <p className="text-[11px] font-mono text-white/25 italic">v0.8.2-α</p>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-[110]
        bg-black/30 backdrop-blur-3xl
        border-t border-white/[0.08]
        shadow-[0_-8px_40px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.06)]">

        {/* Top edge shimmer */}
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent pointer-events-none" />
        {/* Gloss overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />

        <div className="relative flex items-center justify-around px-2 pt-2 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))]">
          {links.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`flex flex-col items-center gap-1 px-5 py-2 rounded-2xl transition-all duration-200 ${
                isActive(link.path) ? 'text-white' : 'text-white/35'
              }`}
            >
              <div className={`p-2 rounded-xl transition-all duration-200 ${
                isActive(link.path)
                  ? 'bg-white/[0.12] shadow-[0_2px_12px_rgba(255,255,255,0.08),inset_0_1px_0_rgba(255,255,255,0.08)]'
                  : ''
              }`}>
                <link.icon size={20} />
              </div>
              <span className="text-[10px] font-semibold tracking-wide">{link.name}</span>
            </Link>
          ))}
        </div>
      </nav>
    </>
  );
};

export default Sidebar;
