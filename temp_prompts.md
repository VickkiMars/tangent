# Tangent Testing Prompts

Use these natural language prompts in the Tangent UI to test the newly integrated research and filesystem tools. The system will automatically select the best tools to fulfill your request.

### 1. Research & Synthesis
> "I want to know everything about the 'NVIDIA Blackwell GPUs'. Check the news, see what people are saying on Twitter and V2EX, find some video reviews on YouTube or Bilibili (and summarize them if they are long), and give me the current stock price of NVIDIA."

### 2. Social Media & Trends
> "What's trending on Weibo right now? Also, see if you can find some honest user reviews for the 'Apple Vision Pro' on XiaoHongShu."

### 3. Technical Exploration
> "Find the GitHub repository for the 'Agent-Reach' project. Tell me what it's about based on its README and check how many stars it has."

### 4. Filesystem & Organization
> "Create a new folder called 'reports'. Then, search for 'latest AI trends 2024' on the web and save a 3-paragraph summary of your findings into a file named 'ai_trends.md' inside that reports folder."

### 5. Financial Analysis
> "Compare the current stock prices of Tesla and BYD. Look for recent investor discussions on Xueqiu to explain any recent price movements."

---
### Maintenance & Troubleshooting
- **Natural Language**: You don't need to specify tool names like `web_search` or `write_file`. Just describe what you want, and the meta-orchestrator will handle the rest.
- **Credentials**: Some tools (like Twitter or LinkedIn) may require prior configuration. Run `agent-reach configure` in a terminal if you encounter auth errors.
- **System Health**: Run `python3 -m agent_reach.cli doctor` to verify that all upstream dependencies (bird, yt-dlp, etc.) are installed and ready.
