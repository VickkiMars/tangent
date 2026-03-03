const Installation = () => (
  <div>
    <h1 className="text-2xl sm:text-4xl font-bold text-white mb-4 sm:mb-6">Installation</h1>
    <p className="text-text-secondary text-lg mb-8 leading-relaxed">
      Get started with nagent by installing the core SDK. We support Python 3.10 and above.
    </p>

    <div className="bg-card border border-white/10 rounded-xl p-6 mb-8 relative group">
      <div className="absolute top-4 right-4 text-xs text-text-tertiary font-mono">bash</div>
      <code className="text-white font-mono text-sm">
        pip install nagent
      </code>
    </div>
  </div>
);

export default Installation;
