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
