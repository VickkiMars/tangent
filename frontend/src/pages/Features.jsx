import { motion } from 'framer-motion';
import { Zap, Shield, Cpu, Cloud, Globe, Lock, Activity, Layers } from 'lucide-react';

const Features = () => {
  const features = [
    { icon: Zap, title: "Lightning Fast", desc: "Edge-deployed infrastructure ensures <100ms latency worldwide." },
    { icon: Shield, title: "Enterprise Security", desc: "SOC2 Type II compliant with end-to-end encryption by default." },
    { icon: Cpu, title: "AI Native", desc: "Built from the ground up for LLM agent architectures." },
    { icon: Globe, title: "Multi-Platform", desc: "Write once, deploy to WhatsApp, Discord, Slack, and Web." },
    { icon: Activity, title: "Real-time Analytics", desc: "Monitor agent performance and user engagement in real-time." },
    { icon: Layers, title: "Modular Design", desc: "Compose complex behaviors from simple, reusable blocks." },
  ];

  return (
    <div className="max-w-7xl mx-auto py-12 sm:py-20 px-0 sm:px-6">
      <div className="text-center mb-10 sm:mb-20">
        <h1 className="text-3xl sm:text-4xl md:text-6xl font-bold mb-4 sm:mb-6 text-white">
          Everything you need to{' '}
          <span className="hidden sm:inline"><br/></span>
          <span className="text-gradient">build world-class agents.</span>
        </h1>
        <p className="text-text-secondary text-base sm:text-lg max-w-2xl mx-auto px-2">
          Tangent provides the primitives, infrastructure, and tooling to build reliable AI agents at scale.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {features.map((f, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -5 }}
            className="p-6 sm:p-8 rounded-2xl bg-card border border-white/10 hover:border-white/30 transition-colors group"
          >
            <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-5 sm:mb-6 group-hover:bg-white/10 transition-colors">
              <f.icon className="text-white group-hover:text-white transition-colors" size={24} />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">{f.title}</h3>
            <p className="text-text-secondary leading-relaxed text-sm sm:text-base">
              {f.desc}
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Features;
