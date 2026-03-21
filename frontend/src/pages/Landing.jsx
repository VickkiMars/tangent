import { motion } from 'framer-motion';
import { ArrowRight, Bug, Lightbulb } from 'lucide-react';
import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="flex flex-col items-center overflow-hidden">
      {/* Hero Section */}
      <section className="relative w-full max-w-7xl mx-auto flex flex-col items-center text-center py-5 sm:py-7 md:py-15 px-2 sm:px-4">

        {/* Floating ambient blobs */}
        <div className="absolute inset-0 pointer-events-none -z-10">
          <motion.div
            animate={{ y: [-20, 20, -20], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-1/4 left-1/4 w-48 sm:w-64 h-48 sm:h-64 rounded-full bg-white/10 blur-[100px]"
          />
          <motion.div
            animate={{ y: [20, -20, 20], opacity: [0.2, 0.5, 0.2] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
            className="absolute bottom-1/4 right-1/4 w-64 sm:w-96 h-64 sm:h-96 rounded-full bg-white/5 blur-[120px]"
          />
        </div>

        <div className="mb-5 sm:mb-6 flex flex-wrap justify-center items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-primary/30 bg-primary/10 backdrop-blur-sm">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span className="text-[10px] sm:text-xs font-medium text-primary-light uppercase tracking-widest">Intelligent Orchestration</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-orange/40 bg-orange/10 backdrop-blur-sm text-orange">
            <span className="text-[10px] sm:text-xs font-medium uppercase tracking-widest">Beta</span>
          </div>
        </div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-4xl sm:text-5xl md:text-7xl font-bold tracking-tight leading-tight max-w-5xl z-10 drop-shadow-2xl mb-6 sm:mb-8"
        >
          Spin!<br/>
          <span className="text-gradient">Tangent!</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-text-secondary text-sm sm:text-base max-w-2xl z-10 leading-relaxed font-sans mb-8 sm:mb-12 px-2"
        >
          Tangent dynamically assembles and deploys temporary teams of AI agents to execute complex tasks. They appear when needed, complete the job with precision, and dissolve <b className='text-white'>without a trace</b>.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex flex-col sm:flex-row gap-3 sm:gap-4 z-10 w-full max-w-xs sm:max-w-none sm:w-auto"
        >
          <Link to="/chat" className="group btn-primary justify-center">
            Get Started
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link to="/docs" className="btn-secondary backdrop-blur-sm text-center">
            Docs
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-8 text-center z-10"
        >
          <p className="text-xs text-text-tertiary mb-3">This is a beta release. You may encounter bugs. Your feedback is appreciated!</p>
          <div className="flex justify-center gap-4">
            <a href="mailto:victorumoreng@gmail.com?subject=Tangent%20Feature%20Request" className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-white transition-colors px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10">
              <Lightbulb size={14} /> Request a feature
            </a>
            <a href="mailto:victorumoreng@gmail.com?subject=Tangent%20Bug%20Report" className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-white transition-colors px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10">
              <Bug size={14} /> Report a bug
            </a>
          </div>
        </motion.div>
      </section>
    </div>
  );
};

export default Landing;
