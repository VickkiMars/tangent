export const MOCK_COMPLEX_TASKS = [
  {
    task_id: "market:research_trends",
    status: "completed",
    dependencies: [],
    required_capabilities: ["web_search", "news_api"],
    model: "gpt-4o"
  },
  {
    task_id: "market:competitor_analysis",
    status: "completed",
    dependencies: ["market:research_trends"],
    required_capabilities: ["web_search", "semantic_scholar"],
    model: "gpt-4o"
  },
  {
    task_id: "market:price_scraping",
    status: "completed",
    dependencies: ["market:research_trends"],
    required_capabilities: ["browser_tool", "data_extraction"],
    model: "gpt-4o-mini"
  },
  {
    task_id: "market:sentiment_analysis",
    status: "running",
    dependencies: ["market:competitor_analysis"],
    required_capabilities: ["text_analysis", "twitter_api"],
    model: "gpt-4o"
  },
  {
    task_id: "market:synthesis_report",
    status: "pending",
    dependencies: ["market:sentiment_analysis", "market:price_scraping"],
    required_capabilities: ["report_generator", "math_tool"],
    model: "o1-preview"
  },
  {
    task_id: "market:human_review",
    status: "hibernate",
    dependencies: ["market:synthesis_report"],
    required_capabilities: ["interaction_tool"],
    model: "gpt-4o"
  }
];

export const MOCK_COMPLEX_ANALYTICS = [
  { target_task_id: "market:research_trends", cost_usd: 0.1245, tokens_prompt: 1540, tokens_completion: 890, lifetime_seconds: 45.2 },
  { target_task_id: "market:competitor_analysis", cost_usd: 0.0892, tokens_prompt: 1200, tokens_completion: 650, lifetime_seconds: 32.8 },
  { target_task_id: "market:price_scraping", cost_usd: 0.0150, tokens_prompt: 800, tokens_completion: 400, lifetime_seconds: 12.5 }
];

export const MOCK_MY_APPS = [
  {
    id: "app_1a2b3c4d",
    name: "Recursive Market Analyzer",
    parameters: [{ key: "INDUSTRY" }, { key: "COMPETITORS" }],
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: "app_9f8e7d6c",
    name: "Automated Blog SEO Strategy",
    parameters: [{ key: "TOPIC" }],
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1).toISOString(),
  },
  {
    id: "app_5d4c3b2a",
    name: "Daily Code Review Audit",
    parameters: [],
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 10).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
  },
  {
    id: "app_11223344",
    name: "Social Media Campaign Drafter",
    parameters: [{ key: "PRODUCT_NAME" }, { key: "PLATFORM" }],
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 15).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 4).toISOString(),
  },
  {
    id: "app_55667788",
    name: "Quarterly Financial Synthesizer",
    parameters: [{ key: "QUARTER" }, { key: "DATA_FILE" }],
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 20).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
  },
  {
    id: "app_99aabbcc",
    name: "Support Analytics Reporter",
    parameters: [{ key: "DATE_RANGE" }],
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 25).toISOString(),
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 6).toISOString(),
  }
];

export const MOCK_APP_RESULT_LOGS = [
  {
    message_id: "msg_1",
    sender_id: "meta_agent",
    thread_id: "main",
    performative: "request",
    payload: { natural_language: "Initializing **Automated Blog SEO Strategy**. Parameters detected: `TOPIC: Multi-Agent Orchestration`. Parsing user objective..." },
    timestamp: Date.now() / 1000 - 45
  },
  {
    message_id: "msg_2",
    sender_id: "seo_expert-bp",
    thread_id: "research",
    performative: "inform",
    payload: { natural_language: "Spawned **SEO Context Agent**. Scanning Google SERP for high-intent keywords related to 'Multi-Agent Orchestration'..." },
    timestamp: Date.now() / 1000 - 38
  },
  {
    message_id: "msg_3",
    sender_id: "browser_agent-bp",
    thread_id: "research",
    performative: "inform",
    payload: { natural_language: "Using `bird` automation. Extracted 12 competitors. Top volume keywords: 'LLM orchestration frameworks', 'JIT agent teams', 'Tangent vs LangGraph'." },
    timestamp: Date.now() / 1000 - 25
  },
  {
    message_id: "msg_4",
    sender_id: "writing_agent-bp",
    thread_id: "synthesis",
    performative: "inform",
    payload: { natural_language: "Drafting **Content Pillar Strategy**. Recommended H1: 'The Future of Scale: Implementing JIT Multi-Agent Architectures'. Total estimated monthly volume: 14.5k." },
    timestamp: Date.now() / 1000 - 12
  },
  {
    message_id: "msg_5",
    sender_id: "meta_agent",
    thread_id: "main",
    performative: "inform",
    payload: { natural_language: "### Deployment Complete\n\nYour SEO Strategy for **Multi-Agent Orchestration** is ready. The workflow executed 4 autonomous threads in parallel using Gemini-3.1-Flash.\n\n[Open Strategy Document](https://tangent.ai/results/seo_report_123)" },
    timestamp: Date.now() / 1000
  }
];
