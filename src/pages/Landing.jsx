import { motion } from 'framer-motion';
import { ArrowRight, Briefcase, Zap, Shield, Cpu, Users, Layers, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="flex flex-col items-center overflow-hidden">
      {/* Hero Section */}
      <section className="relative w-full max-w-7xl mx-auto flex flex-col items-center text-center py-32 px-6">
        
        {/* Floating Elements - Abstract shapes representing ephemeral agents */}
        <div className="absolute inset-0 pointer-events-none -z-10">
          <motion.div 
            animate={{ y: [-20, 20, -20], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full bg-white/10 blur-[100px]"
          />
          <motion.div 
            animate={{ y: [20, -20, 20], opacity: [0.2, 0.5, 0.2] }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
            className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-white/5 blur-[120px]"
          />
        </div>

        <div className="mb-6 flex items-center gap-2 px-3 py-1 rounded-full border border-primary/30 bg-primary/10 backdrop-blur-sm">
           <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
           <span className="text-xs font-medium text-primary-light uppercase tracking-widest">Intelligent Orchestration</span>
        </div>

        <motion.h1 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-5xl md:text-7xl font-bold tracking-tight leading-tight max-w-5xl z-10 drop-shadow-2xl mb-8"
        >
          Expert AI Consultants <br/>
          <span className="text-gradient">On Demand.</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-text-secondary text-lg md:text-xl max-w-3xl z-10 leading-relaxed font-sans mb-12"
        >
          N-Agent dynamically assembles and deploys temporary teams of AI agents to execute complex tasks. They appear when needed, complete the job with precision, and dissolve without a trace.
        </motion.p>
        
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="flex flex-col sm:flex-row gap-4 z-10"
        >
          <Link to="/workspace" className="group btn-primary">
            Deploy Agents
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link to="/docs" className="btn-secondary backdrop-blur-sm">
            How it Works
          </Link>
        </motion.div>

        {/* Dashboard Preview / Blackboard visual */}
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 1 }}
          className="mt-20 w-full max-w-5xl glass-panel rounded-2xl border border-white/10 p-2 shadow-2xl shadow-primary/20 relative"
        >
           <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent z-10 pointer-events-none h-full w-full opacity-50"></div>
           <div className="bg-background rounded-xl overflow-hidden aspect-[16/9] relative border border-white/5">
              {/* Mock Interface */}
              <div className="absolute inset-0 p-6 flex flex-col">
                  <div className="flex items-center justify-between mb-8 border-b border-white/5 pb-4">
                      <div className="flex gap-2">
                          <div className="w-3 h-3 rounded-full bg-red-500/20"></div>
                          <div className="w-3 h-3 rounded-full bg-yellow-500/20"></div>
                          <div className="w-3 h-3 rounded-full bg-green-500/20"></div>
                      </div>
                      <div className="text-xs font-mono text-text-tertiary">Mission: Market Analysis - Phase 2</div>
                  </div>
                  <div className="flex-grow grid grid-cols-12 gap-6">
                      <div className="col-span-8 space-y-4">
                          <div className="flex gap-4 items-start animate-pulse">
                              <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center text-primary-light">
                                  <Activity size={16} />
                              </div>
                              <div className="flex-grow space-y-2">
                                  <div className="h-2 w-3/4 bg-white/10 rounded"></div>
                                  <div className="h-2 w-1/2 bg-white/10 rounded"></div>
                              </div>
                          </div>
                          <div className="flex gap-4 items-start opacity-50">
                              <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-text-tertiary">
                                  <Users size={16} />
                              </div>
                              <div className="flex-grow space-y-2">
                                  <div className="h-2 w-full bg-white/5 rounded"></div>
                                  <div className="h-2 w-5/6 bg-white/5 rounded"></div>
                              </div>
                          </div>
                      </div>
                      <div className="col-span-4 space-y-3 border-l border-white/5 pl-6">
                          <div className="p-3 rounded bg-primary/5 border border-primary/10">
                              <div className="text-[10px] uppercase text-primary mb-1 font-bold">Active Agents</div>
                              <div className="text-2xl font-mono text-white">4</div>
                          </div>
                          <div className="p-3 rounded bg-white/5 border border-white/10">
                              <div className="text-[10px] uppercase text-text-tertiary mb-1 font-bold">Time Elapsed</div>
                              <div className="text-2xl font-mono text-text-secondary">00:04:12</div>
                          </div>
                      </div>
                  </div>
              </div>
           </div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-6 py-32 w-full">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            <div className="glass-panel p-8 rounded-3xl relative overflow-hidden group">
                <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center mb-6 text-primary-light group-hover:scale-110 transition-transform">
                    <Zap size={24} />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Instant Deployment</h3>
                <p className="text-text-secondary leading-relaxed">
                    Like summoning a SWAT team for your code. Agents spin up in milliseconds, context-aware and ready to execute.
                </p>
                <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-colors"></div>
            </div>

            <div className="glass-panel p-8 rounded-3xl relative overflow-hidden group">
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center mb-6 text-white group-hover:scale-110 transition-transform">
                    <Layers size={24} />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Zero Footprint</h3>
                <p className="text-text-secondary leading-relaxed">
                    Stateless execution. Once the job is done, agents dissolve completely, leaving only their high-quality work product behind.
                </p>
                <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-white/10 rounded-full blur-2xl group-hover:bg-white/20 transition-colors"></div>
            </div>

            <div className="glass-panel p-8 rounded-3xl relative overflow-hidden group">
                <div className="w-12 h-12 rounded-xl bg-orange/20 flex items-center justify-center mb-6 text-orange group-hover:scale-110 transition-transform">
                    <Briefcase size={24} />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Expert Consultants</h3>
                <p className="text-text-secondary leading-relaxed">
                    Specialized agents for every sub-task. From research to coding to deployment, get the right "expert" for every step.
                </p>
                <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-orange/10 rounded-full blur-2xl group-hover:bg-orange/20 transition-colors"></div>
            </div>

        </div>
      </section>
    </div>
  );
};

export default Landing;
