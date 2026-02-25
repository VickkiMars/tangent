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
    <div className="max-w-7xl mx-auto py-20 px-6">
      <div className="text-center mb-20">
        <h1 className="text-4xl md:text-6xl font-bold mb-6 text-white">
          Everything you need to <br/>
          <span className="text-gradient">build world-class agents.</span>
        </h1>
        <p className="text-text-secondary text-lg max-w-2xl mx-auto">
          Spectrum provides the primitives, infrastructure, and tooling to build reliable AI agents at scale.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((f, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -5 }}
            className="p-8 rounded-2xl bg-card border border-white/10 hover:border-white/30 transition-colors group"
          >
            <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-6 group-hover:bg-white/10 transition-colors">
              <f.icon className="text-white group-hover:text-white transition-colors" size={24} />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">{f.title}</h3>
            <p className="text-text-secondary leading-relaxed">
              {f.desc}
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Features;
