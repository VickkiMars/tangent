import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

const Pricing = () => {
  const plans = [
    {
      name: 'Hobby',
      price: '$0',
      description: 'Perfect for side projects and learning.',
      features: ['Up to 3 Agents', '1,000 Messages/mo', 'Community Support', 'Basic Analytics'],
      highlight: false,
    },
    {
      name: 'Pro',
      price: '$29',
      description: 'For professional developers and small teams.',
      features: ['Unlimited Agents', '50,000 Messages/mo', 'Priority Support', 'Advanced Analytics', 'Custom Integrations'],
      highlight: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      description: 'Scale without limits.',
      features: ['Unlimited Everything', 'SLA Guarantee', 'Dedicated Success Manager', 'On-premise Deployment', 'Audit Logs'],
      highlight: false,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto py-20 flex flex-col items-center">
      <div className="text-center mb-16">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 text-white">Simple, transparent pricing</h1>
        <p className="text-text-secondary text-lg">Choose the plan that fits your needs.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full px-4">
        {plans.map((plan, index) => (
          <motion.div
            key={plan.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`relative p-8 rounded-2xl border ${plan.highlight ? 'border-white bg-card/80 shadow-[0_0_40px_rgba(255,255,255,0.1)]' : 'border-white/10 bg-card'} flex flex-col`}
          >
            {plan.highlight && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-white text-black px-4 py-1 rounded-full text-xs font-bold uppercase tracking-wide">
                Most Popular
              </div>
            )}
            <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
            <div className="text-4xl font-bold text-white mb-4">{plan.price}<span className="text-lg text-text-tertiary font-normal">/mo</span></div>
            <p className="text-text-secondary text-sm mb-8">{plan.description}</p>
            
            <ul className="space-y-4 mb-8 flex-grow">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-center gap-3 text-sm text-text-secondary">
                  <div className={`p-1 rounded-full ${plan.highlight ? 'bg-white/20 text-white' : 'bg-white/10 text-white'}`}>
                    <Check size={12} />
                  </div>
                  {feature}
                </li>
              ))}
            </ul>

            <button className={`w-full py-3 rounded-xl font-semibold transition-all ${plan.highlight ? 'bg-white text-black hover:bg-white/90' : 'bg-white/10 text-white hover:bg-white/20'}`}>
              Get Started
            </button>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Pricing;
