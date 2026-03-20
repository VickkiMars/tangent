import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, CreditCard, Box, BookOpen, Clock, MessageCircle, Menu, X, PenTool, LogOut, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const isActive = (path) => location.pathname === path;

  const links = [
    { name: 'Chat', path: '/chat', icon: MessageCircle },
    { name: 'Pricing', path: '/pricing', icon: CreditCard },
    { name: 'Docs', path: '/docs', icon: BookOpen },
  ];

  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] px-4 whitespace-nowrap">
      <div className="glass-panel rounded-full px-6 py-3 flex items-center gap-8 shadow-2xl shadow-white/5 border border-white/10">
        <Link to="/" onClick={() => setMenuOpen(false)} className="flex items-center gap-2 group border-r border-white/10 pr-6 mr-2">
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-white/20">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-black"><path d="M12 2L2 22h20L12 2z" fill="currentColor"/></svg>
          </div>
          <span className="font-bold tracking-tight text-lg text-white transition-colors">Tangent</span>
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

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3 pl-4 border-l border-white/10">
              <div className="flex flex-col items-end hidden lg:flex">
                <span className="text-[10px] font-bold text-white uppercase tracking-tight">{user.first_name} {user.last_name}</span>
                <span className="text-[8px] text-text-tertiary font-mono">{user.email}</span>
              </div>
              <button 
                onClick={logout}
                className="p-2 rounded-full bg-white/5 border border-white/10 hover:bg-red-500/10 hover:border-red-500/20 text-text-secondary hover:text-red-400 transition-all"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <Link 
              to="/signup" 
              className="px-5 py-2 rounded-full bg-white text-black text-sm font-bold shadow-lg shadow-white/10 hover:shadow-white/20 hover:scale-105 active:scale-95 transition-all"
            >
              Join Tangent
            </Link>
          )}
          
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="md:hidden p-2 rounded-full hover:bg-white/10 text-white transition-colors"
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="md:hidden mt-2 mx-auto max-w-7xl glass-panel rounded-2xl px-3 py-3 shadow-xl border border-white/10"
          >
            {links.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive(link.path) ? 'bg-white text-black' : 'text-text-secondary hover:text-white hover:bg-white/5'
                }`}
              >
                <link.icon size={16} />
                {link.name}
              </Link>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
