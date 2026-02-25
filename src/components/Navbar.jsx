import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Terminal, CreditCard, Box, BookOpen, Clock, MessageCircle } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  const links = [
    { name: 'Features', path: '/features', icon: Box },
    { name: 'Pricing', path: '/pricing', icon: CreditCard },
    { name: 'Docs', path: '/docs', icon: BookOpen },
    { name: 'History', path: '/history', icon: Clock },
    { name: 'Workspace', path: '/workspace', icon: Terminal },
    { name: 'Chat', path: '/chat', icon: MessageCircle },
  ];

  return (
    <nav className="fixed top-0 w-full z-[100] px-6 py-4">
      <div className="max-w-7xl mx-auto glass-panel rounded-full px-6 py-3 flex justify-between items-center shadow-lg shadow-white/10">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-white/20">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-black"><path d="M12 2L2 22h20L12 2z" fill="currentColor"/></svg>
          </div>
          <span className="font-bold tracking-tight text-lg text-white transition-colors">N-Agent</span>
        </Link>

        <div className="hidden md:flex items-center gap-1 bg-black/20 rounded-full p-1 border border-white/5">
          {links.map((link) => (
            <Link 
              key={link.path} 
              to={link.path}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 relative ${isActive(link.path) ? 'text-black' : 'text-text-secondary hover:text-white'}`}
            >
              {isActive(link.path) && (
                <motion.div
                  layoutId="navbar-indicator"
                  className="absolute inset-0 bg-white rounded-full shadow-lg shadow-white/30"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <link.icon size={14} />
                {link.name}
              </span>
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/10 shadow-inner">
          <div className="w-2 h-2 rounded-full bg-success animate-pulse shadow-[0_0_8px_rgba(255,255,255,0.5)]"></div>
          <span className="text-[10px] font-medium text-success uppercase tracking-widest hidden sm:inline">System Active</span>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
