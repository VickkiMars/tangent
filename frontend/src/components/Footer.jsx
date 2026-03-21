import { Github, Twitter, MessageCircle } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="border-t border-white/10 py-8 sm:py-10 px-4 sm:px-6 bg-black/50 backdrop-blur-sm mt-10 sm:mt-20">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-3 sm:gap-4 text-sm text-text-tertiary">
        <div className="flex items-center gap-2 text-white">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M12 2L2 22h20L12 2z" fill="currentColor"/></svg>
          <span className="font-bold">Tangent</span>
        </div>
        <p>© 2026 Tangent All Rights Reserved.</p>
        <div className="flex gap-4">
          <a href="#" className="hover:text-white transition-colors"><Twitter size={18} /></a>
          <a href="#" className="hover:text-white transition-colors"><MessageCircle size={18} /></a>
          <a href="#" className="hover:text-white transition-colors"><Github size={18} /></a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
