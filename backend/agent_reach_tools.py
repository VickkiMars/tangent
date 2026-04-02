import sys
import os
import subprocess
import json
import asyncio
import http.client
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

# Add Agent-Reach to sys.path
AGENT_REACH_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Agent-Reach"))
if AGENT_REACH_PATH not in sys.path:
    sys.path.append(AGENT_REACH_PATH)

def run_cli_command(cmd: List[str], timeout: int = 30) -> str:
    """Helper to run CLI commands and return output or error."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error ({result.returncode}): {result.stderr or result.stdout}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error: {str(e)}"

def format_serper_results(data_str: str) -> str:
    """Format Serper.dev JSON response into a clean string for the agent."""
    try:
        data = json.loads(data_str)
        results = []
        
        # Knowledge Graph
        if "knowledgeGraph" in data:
            kg = data["knowledgeGraph"]
            title = kg.get("title", "Unknown")
            description = kg.get("description", "")
            results.append(f"### KNOWLEDGE GRAPH: {title}\n{description}\n")
            if "attributes" in kg:
                attrs = kg["attributes"]
                for k, v in attrs.items():
                    results.append(f"- {k}: {v}")
                results.append("")

        # Organic Results
        if "organic" in data:
            results.append("### ORGANIC SEARCH RESULTS:")
            for item in data["organic"][:10]: # Limit to top 10
                title = item.get("title", "No Title")
                link = item.get("link", "#")
                snippet = item.get("snippet", "")
                position = item.get("position", "?")
                results.append(f"{position}. [{title}]({link})\n   {snippet}\n")

        # People Also Ask
        if "peopleAlsoAsk" in data:
            results.append("### PEOPLE ALSO ASK:")
            for paa in data["peopleAlsoAsk"]:
                results.append(f"- {paa.get('question')}")
            results.append("")

        return "\n".join(results) if results else "No significant results found."
    except Exception as e:
        return f"Error parsing Serper results: {str(e)}\nRaw: {data_str[:500]}..."

# --- Web Tools ---

async def web_read(url: str) -> str:
    """Read any web page as Markdown using Jina Reader."""
    # Use jina.ai reader via curl
    return await asyncio.to_thread(run_cli_command, ["curl", "-s", f"https://r.jina.ai/{url}"])

async def web_search(query: str, num_results: int = 10) -> str:
    """Search the web using Google via Serper.dev. Returns rich formatted results."""
    key = os.environ.get("SERPER_DEV_KEY")
    if not key:
        return "Error: SERPER_DEV_KEY not found in environment. Please configure it in .env."

    def _do_search():
        try:
            conn = http.client.HTTPSConnection("google.serper.dev")
            payload = json.dumps({"q": query, "num": num_results})
            headers = {
                'X-API-KEY': key,
                'Content-Type': 'application/json'
            }
            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            return format_serper_results(data)
        except Exception as e:
            return f"Error connecting to Serper.dev: {str(e)}"

    return await asyncio.to_thread(_do_search)

async def web_search_batch(queries: List[str], num_results: int = 5) -> str:
    """Search the web for multiple queries in parallel using Serper.dev."""
    async def _search_one(q: str) -> str:
        result = await web_search(q, num_results=num_results)
        return f"## Results for: {q}\n{result}"

    results = await asyncio.gather(*[_search_one(q) for q in queries])
    return "\n\n---\n\n".join(results)

# --- ArXiv Tools ---

async def arxiv_search(query: str, limit: int = 5) -> str:
    """Search for academic papers on ArXiv using their Atom API."""
    def _do_arxiv_search():
        try:
            # ArXiv API uses Atom XML format
            base_url = "http://export.arxiv.org/api/query?"
            search_query = f"search_query=all:{urllib.parse.quote(query)}"
            params = f"&start=0&max_results={limit}"
            url = base_url + search_query + params
            
            with urllib.request.urlopen(url) as response:
                xml_data = response.read().decode('utf-8')
                
            # Parse XML
            root = ET.fromstring(xml_data)
            
            # Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            if not entries:
                return "No papers found on ArXiv for this query."
            
            formatted_results = []
            for entry in entries:
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None and title_elem.text else "No Title"
                
                published_elem = entry.find('atom:published', ns)
                published = published_elem.text[:10] if published_elem is not None and published_elem.text else "Unknown Date"
                
                summary_elem = entry.find('atom:summary', ns)
                summary = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None and summary_elem.text else "No Abstract"
                
                authors = []
                for author_elem in entry.findall('atom:author', ns):
                    name_elem = author_elem.find('atom:name', ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                
                author_str = ", ".join(authors) if authors else "Unknown Authors"
                
                # Links: look for alternate (abstract page) and related (PDF)
                links = entry.findall('atom:link', ns)
                abs_url = ""
                pdf_url = ""
                for link in links:
                    if link.get('rel') == 'alternate':
                        abs_url = link.get('href')
                    elif link.get('title') == 'pdf':
                        pdf_url = link.get('href')
                
                # Categories
                categories = [c.get('term') for c in entry.findall('atom:category', ns)]
                
                res = [
                    f"### [{title}]({abs_url})",
                    f"**Authors**: {', '.join(authors)}",
                    f"**Published**: {published} | **Categories**: {', '.join(categories)}",
                ]
                if pdf_url:
                    res.append(f"[PDF Link]({pdf_url})")
                
                res.append(f"\n{summary[:500]}..." if len(summary) > 500 else f"\n{summary}")
                formatted_results.append("\n".join(res))
                
            return "\n\n---\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Error querying ArXiv: {str(e)}"

    return await asyncio.to_thread(_do_arxiv_search)

# --- Wikipedia Tools ---

async def wikipedia_search(query: str, limit: int = 5) -> str:
    """Search for relevant Wikipedia page titles and links."""
    def _do_wp_search():
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit={limit}&namespace=0&format=json"
            headers = {"User-Agent": "TangentResearchTool/1.0 (contact: support@example.com)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # OpenSearch format: [query, [titles], [descriptions], [links]]
            titles = data[1]
            links = data[3]
            
            if not titles:
                return "No Wikipedia pages found for this query."
            
            results = []
            for t, l in zip(titles, links):
                results.append(f"- [{t}]({l})")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error searching Wikipedia: {str(e)}"

    return await asyncio.to_thread(_do_wp_search)

async def wikipedia_read(title: str) -> str:
    """Read the full plain text content of a specific Wikipedia page."""
    def _do_wp_read():
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&titles={urllib.parse.quote(title)}&format=json"
            headers = {"User-Agent": "TangentResearchTool/1.0 (contact: support@example.com)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return f"Error: Could not find page '{title}'."
            
            # The page ID is the key
            page_id = list(pages.keys())[0]
            if page_id == "-1":
                return f"Error: Page '{title}' does not exist."
                
            extract = pages[page_id].get("extract", "")
            return extract if extract else "This page has no text content."
        except Exception as e:
            return f"Error reading Wikipedia page: {str(e)}"

    return await asyncio.to_thread(_do_wp_read)

# --- Reddit Tools ---

async def reddit_search(query: str, limit: int = 5) -> str:
    """Search Reddit for relevant posts using the public JSON API."""
    def _do_reddit_search():
        try:
            url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(query)}&limit={limit}&sort=relevance"
            headers = {"User-Agent": "TangentResearchTool/1.0 (contact: support@example.com)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            posts = data.get("data", {}).get("children", [])
            if not posts:
                return "No Reddit posts found for this query."
            
            results = []
            for p in posts:
                d = p.get("data", {})
                title = d.get("title", "No Title")
                permalink = d.get("permalink", "")
                url = f"https://www.reddit.com{permalink}"
                subreddit = d.get("subreddit_name_prefixed", "r/?")
                score = d.get("score", 0)
                num_comments = d.get("num_comments", 0)
                results.append(f"- [{title}]({url}) | {subreddit} | {score} votes | {num_comments} comments")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error searching Reddit: {str(e)}"

    return await asyncio.to_thread(_do_reddit_search)

async def reddit_read(url: str) -> str:
    """Read a specific Reddit post and its top comments. URL should end with .json or be the normal post URL."""
    def _do_reddit_read():
        try:
            if not url.endswith(".json"):
                api_url = url.rstrip("/") + ".json"
            else:
                api_url = url
                
            headers = {"User-Agent": "TangentResearchTool/1.0 (contact: support@example.com)"}
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Reddit comments JSON is a list: [post_data, comments_data]
            if not isinstance(data, list) or len(data) < 1:
                return f"Error: Unexpected Reddit API response for {url}"
            
            post_info = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
            title = post_info.get("title", "No Title")
            author = post_info.get("author", "unknown")
            subreddit = post_info.get("subreddit_name_prefixed", "r/?")
            selftext = post_info.get("selftext", "")
            
            output = [f"# {title}", f"By u/{author} in {subreddit}", "\n" + selftext + "\n", "## Top Comments\n"]
            
            comments = data[1].get("data", {}).get("children", [])
            for c in comments[:10]: # Top 10 comments
                cd = c.get("data", {})
                c_body = cd.get("body", "")
                c_author = cd.get("author", "[deleted]")
                c_score = cd.get("score", 0)
                if c_body:
                    output.append(f"**u/{c_author}** ({c_score} votes):\n{c_body}\n")
            
            return "\n".join(output)
        except Exception as e:
            return f"Error reading Reddit post: {str(e)}"

    return await asyncio.to_thread(_do_reddit_read)

# --- Twitter/X Tools ---

async def twitter_search(query: str, count: int = 10) -> str:
    """Search Twitter/X for the given query."""
    return await asyncio.to_thread(run_cli_command, ["bird", "search", query, "-n", str(count)])

async def twitter_read(url_or_id: str) -> str:
    """Read a specific tweet or article from Twitter/X."""
    return await asyncio.to_thread(run_cli_command, ["bird", "read", url_or_id])

async def twitter_user_tweets(username: str, count: int = 20) -> str:
    """Get the latest tweets from a specific Twitter user."""
    if not username.startswith("@"):
        username = f"@{username}"
    return await asyncio.to_thread(run_cli_command, ["bird", "user-tweets", username, "-n", str(count)])

async def twitter_thread(url_or_id: str) -> str:
    """Get the full thread for a specific tweet."""
    return await asyncio.to_thread(run_cli_command, ["bird", "thread", url_or_id])

# --- YouTube Tools ---

async def youtube_metadata(url: str) -> str:
    """Get metadata for a YouTube video."""
    return await asyncio.to_thread(run_cli_command, ["yt-dlp", "--dump-json", url])

async def youtube_search(query: str, count: int = 5) -> str:
    """Search for YouTube videos."""
    return await asyncio.to_thread(run_cli_command, ["yt-dlp", "--dump-json", f"ytsearch{count}:{query}"])

async def youtube_transcript(url: str, lang: str = "en,zh-Hans") -> str:
    """Extract subtitles/transcript from a YouTube video."""
    # This is a bit complex as it involves writing a file and then reading it.
    # For now, we'll use the --get-subs command if possible, but yt-dlp usually writes them.
    # We follow the SKILL.md advice: write to /tmp/ then read.
    video_id_cmd = ["yt-dlp", "--get-id", url]
    video_id = run_cli_command(video_id_cmd).strip()
    if video_id.startswith("Error"):
        return video_id
    
    output_base = f"/tmp/{video_id}"
    dl_cmd = ["yt-dlp", "--write-sub", "--write-auto-sub", "--sub-lang", lang, "--skip-download", "-o", output_base, url]
    run_cli_command(dl_cmd)
    
    # Try to find the transcript file
    possible_files = [f"{output_base}.{l}.vtt" for l in lang.split(",")] + [f"{output_base}.vtt"]
    for f in possible_files:
        if os.path.exists(f):
            with open(f, "r") as fh:
                return fh.read()
    
    return "Error: Could not find transcript file."

# --- GitHub Tools ---

async def github_repo_view(repo: str) -> str:
    """View details of a GitHub repository (owner/repo)."""
    return await asyncio.to_thread(run_cli_command, ["gh", "repo", "view", repo])

async def github_search_repos(query: str, limit: int = 10) -> str:
    """Search for GitHub repositories."""
    return await asyncio.to_thread(run_cli_command, ["gh", "search", "repos", query, "--limit", str(limit)])

# --- V2EX Tools ---

async def v2ex_hot_topics(limit: int = 20) -> List[Dict[str, Any]]:
    """Get hot topics from V2EX."""
    from agent_reach.channels.v2ex import V2EXChannel
    ch = V2EXChannel()
    return await asyncio.to_thread(ch.get_hot_topics, limit)

async def v2ex_topic(topic_id: int) -> Dict[str, Any]:
    """Get a specific V2EX topic and its replies."""
    from agent_reach.channels.v2ex import V2EXChannel
    ch = V2EXChannel()
    return await asyncio.to_thread(ch.get_topic, topic_id)

# --- Xueqiu Tools ---

async def xueqiu_quote(symbol: str) -> Dict[str, Any]:
    """Get stock quote from Xueqiu (e.g., SH600519, AAPL)."""
    from agent_reach.channels.xueqiu import XueqiuChannel
    ch = XueqiuChannel()
    return await asyncio.to_thread(ch.get_stock_quote, symbol)

async def xueqiu_hot_posts(limit: int = 20) -> List[Dict[str, Any]]:
    """Get hot posts from Xueqiu community."""
    from agent_reach.channels.xueqiu import XueqiuChannel
    ch = XueqiuChannel()
    return await asyncio.to_thread(ch.get_hot_posts, limit)

# --- Bilibili Tools ---

async def bilibili_metadata(url: str) -> str:
    """Get metadata for a Bilibili video."""
    return await asyncio.to_thread(run_cli_command, ["yt-dlp", "--dump-json", url])

async def bilibili_transcript(url: str) -> str:
    """Extract subtitles/transcript from a Bilibili video."""
    video_id_cmd = ["yt-dlp", "--get-id", url]
    video_id = run_cli_command(video_id_cmd).strip()
    if video_id.startswith("Error"):
        return video_id
    
    output_base = f"/tmp/{video_id}"
    dl_cmd = ["yt-dlp", "--write-sub", "--write-auto-sub", "--convert-subs", "vtt", "--skip-download", "-o", output_base, url]
    run_cli_command(dl_cmd)
    
    if os.path.exists(f"{output_base}.vtt"):
        with open(f"{output_base}.vtt", "r") as fh:
            return fh.read()
    return "Error: Could not find transcript file."

# --- XiaoHongShu Tools ---

async def xhs_search(query: str) -> str:
    """Search for notes on XiaoHongShu."""
    return await asyncio.to_thread(run_cli_command, ["mcporter", "call", f"xiaohongshu.search_feeds(keyword: \"{query}\")"])

async def xhs_detail(feed_id: str, xsec_token: str) -> str:
    """Get detail of a specific XiaoHongShu note."""
    return await asyncio.to_thread(run_cli_command, ["mcporter", "call", f"xiaohongshu.get_feed_detail(feed_id: \"{feed_id}\", xsec_token: \"{xsec_token}\")"])

# --- Douyin Tools ---

async def douyin_parse(url: str) -> str:
    """Parse video info from a Douyin share link."""
    return await asyncio.to_thread(run_cli_command, ["mcporter", "call", f"douyin.parse_douyin_video_info(share_link: \"{url}\")"])

# --- Weibo Tools ---

async def weibo_trendings(limit: int = 20) -> str:
    """Get trending topics from Weibo."""
    return await asyncio.to_thread(run_cli_command, ["mcporter", "call", f"weibo.get_trendings(limit: {limit})"])

async def weibo_search(query: str, limit: int = 20) -> str:
    """Search for content on Weibo."""
    return await asyncio.to_thread(run_cli_command, ["mcporter", "call", f"weibo.search_content(keyword: \"{query}\", limit: {limit})"])

# --- WeChat Tools ---

async def wechat_search(query: str, limit: int = 5) -> str:
    """Search for WeChat articles."""
    # This uses the miku_ai snippet from SKILL.md
    python_cmd = f"""
import asyncio
from miku_ai import get_wexin_article
async def s():
    for a in await get_wexin_article('{query}', {limit}):
        print(f'{{a["title"]}} | {{a["url"]}}')
asyncio.run(s())
"""
    return await asyncio.to_thread(run_cli_command, ["python3", "-c", python_cmd])

async def wechat_read(url: str) -> str:
    """Read a WeChat article using Camoufox (bypasses anti-bot)."""
    # Uses the local script path from SKILL.md
    script_path = os.path.expanduser("~/.agent-reach/tools/wechat-article-for-ai/main.py")
    if os.path.exists(script_path):
        return await asyncio.to_thread(run_cli_command, ["python3", script_path, url])
    return "Error: WeChat read tool not installed. Run 'agent-reach install'."

# --- LinkedIn Tools ---

async def linkedin_profile(url: str) -> str:
    """Get a person's LinkedIn profile details."""
    return await asyncio.to_thread(run_cli_command, ["mcporter", "call", f"linkedin.get_person_profile(linkedin_url: \"{url}\")"])

# --- Xiaoyuzhou Tools ---

async def xiaoyuzhou_transcribe(url: str) -> str:
    """Transcribe a Xiaoyuzhou podcast episode to text."""
    script_path = os.path.expanduser("~/.agent-reach/tools/xiaoyuzhou/transcribe.sh")
    if os.path.exists(script_path):
        # Result is saved to /tmp/, we need to capture or return guidance
        return await asyncio.to_thread(run_cli_command, [script_path, url])
    return "Error: Xiaoyuzhou transcribe tool not installed."

# --- RSS Tools ---

async def rss_read(url: str, limit: int = 5) -> str:
    """Read and parse an RSS feed."""
    # Simple Python implementation using feedparser which is a dependency of Agent-Reach
    import feedparser
    feed = await asyncio.to_thread(feedparser.parse, url)
    results = []
    for entry in feed.entries[:limit]:
        results.append(f"{entry.title} - {entry.link}")
    return "\n".join(results) if results else "No entries found."

# --- Registry Helper ---

AGENT_REACH_TOOLS = [
    {
        "name": "web_read",
        "func": web_read,
        "schema": {
            "type": "function",
            "function": {
                "name": "web_read",
                "description": "Read any web page and convert it to clean Markdown. This tool bypasses clutter and paywalls, making it ideal for reading long articles, technical documentation, or breaking news once you have a URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The full URL of the web page to read (including https://)."}
                    },
                    "required": ["url"]
                }
            }
        }
    },
    {
        "name": "web_search",
        "func": web_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Comprehensive web search (powered by Google via Serper.dev). Returns rich results including organic snippets, knowledge graph data, and related questions. Use for accurate, up-to-date information on any topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query (e.g., 'latest Nvidia earnings' or 'best open source LLMs 2025')."},
                        "num_results": {"type": "integer", "description": "Number of high-quality results to return (default 10, max 20).", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "web_search_batch",
        "func": web_search_batch,
        "schema": {
            "type": "function",
            "function": {
                "name": "web_search_batch",
                "description": "Run multiple web searches in parallel in a single call. Dramatically faster than sequential calls. Use when researching multiple angles or comparative data points simultaneously.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of search queries to execute in parallel."
                        },
                        "num_results": {"type": "integer", "description": "Number of results per query (default 5).", "default": 5}
                    },
                    "required": ["queries"]
                }
            }
        }
    },
    {
        "name": "twitter_search",
        "func": twitter_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "twitter_search",
                "description": "Search Twitter/X for real-time discussions, trending topics, and direct user feedback. Useful for gauging public sentiment or finding breaking news not yet on major websites.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query or hashtag."},
                        "count": {"type": "integer", "description": "Number of tweets to return.", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "twitter_read",
        "func": twitter_read,
        "schema": {
            "type": "function",
            "function": {
                "name": "twitter_read",
                "description": "Read the full content of a specific tweet or a linked article within a tweet. Use this when you have a specific Twitter URL or ID from a search result.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url_or_id": {"type": "string", "description": "The full Tweet URL or the numeric Tweet ID."}
                    },
                    "required": ["url_or_id"]
                }
            }
        }
    },
    {
        "name": "twitter_user_tweets",
        "func": twitter_user_tweets,
        "schema": {
            "type": "function",
            "function": {
                "name": "twitter_user_tweets",
                "description": "Fetch the timeline of a specific user. Use this to track updates from influencers, official company accounts, or experts in a field.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Twitter handle (e.g. '@elonmusk' or 'elonmusk')."},
                        "count": {"type": "integer", "description": "Number of recent tweets to fetch.", "default": 20}
                    },
                    "required": ["username"]
                }
            }
        }
    },
    {
        "name": "twitter_thread",
        "func": twitter_thread,
        "schema": {
            "type": "function",
            "function": {
                "name": "twitter_thread",
                "description": "Retrieve an entire Twitter thread (a sequence of related tweets) starting from a specific tweet. Use this to get the context of a long explanation or narrative.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url_or_id": {"type": "string", "description": "The URL or ID of any tweet in the thread (usually the first one)."}
                    },
                    "required": ["url_or_id"]
                }
            }
        }
    },
    {
        "name": "youtube_metadata",
        "func": youtube_metadata,
        "schema": {
            "type": "function",
            "function": {
                "name": "youtube_metadata",
                "description": "Get detailed metadata for a YouTube video (description, view count, tags, upload date). Useful for assessing video quality/relevance before transcribing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL."}
                    },
                    "required": ["url"]
                }
            }
        }
    },
    {
        "name": "youtube_search",
        "func": youtube_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "youtube_search",
                "description": "Search for videos on YouTube. Use this to find tutorials, reviews, or news coverage on a topic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                        "count": {"type": "integer", "description": "Number of results to return.", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "youtube_transcript",
        "func": youtube_transcript,
        "schema": {
            "type": "function",
            "function": {
                "name": "youtube_transcript",
                "description": "Extract the transcript or subtitles from a YouTube video as text. Essential for 'reading' a video's content without watching it. Supports multiple languages.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "YouTube video URL."},
                        "lang": {"type": "string", "description": "Comma-separated language codes (e.g. 'en,zh-Hans').", "default": "en,zh-Hans"}
                    },
                    "required": ["url"]
                }
            }
        }
    },
    {
        "name": "github_repo_view",
        "func": github_repo_view,
        "schema": {
            "type": "function",
            "function": {
                "name": "github_repo_view",
                "description": "View details of a GitHub repository, including its README, stars, and open issues. Use for technical research on libraries or frameworks.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo": {"type": "string", "description": "Repository identifier (e.g. 'owner/repo')."}
                    },
                    "required": ["repo"]
                }
            }
        }
    },
    {
        "name": "github_search_repos",
        "func": github_search_repos,
        "schema": {
            "type": "function",
            "function": {
                "name": "github_search_repos",
                "description": "Search for repositories on GitHub. Use this to find codebases, libraries, or projects related to a technology or problem.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                        "limit": {"type": "integer", "description": "Max results to return.", "default": 10}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "v2ex_hot_topics",
        "func": v2ex_hot_topics,
        "schema": {
            "type": "function",
            "function": {
                "name": "v2ex_hot_topics",
                "description": "Fetch the current trending discussions from the V2EX developer community. Useful for gathering tech community sentiment in Asia/China.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of topics to fetch.", "default": 20}
                    }
                }
            }
        }
    },
    {
        "name": "v2ex_topic",
        "func": v2ex_topic,
        "schema": {
            "type": "function",
            "function": {
                "name": "v2ex_topic",
                "description": "Get the full content and replies of a specific V2EX discussion thread using its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic_id": {"type": "integer", "description": "The numeric ID of the topic."}
                    },
                    "required": ["topic_id"]
                }
            }
        }
    },
    {
        "name": "xueqiu_quote",
        "func": xueqiu_quote,
        "schema": {
            "type": "function",
            "function": {
                "name": "xueqiu_quote",
                "description": "Get real-time stock quotes, price changes, and fundamentals from Xueqiu. Supports global markets (CN, US, HK).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker/symbol (e.g. 'AAPL' or 'SH600519')."}
                    },
                    "required": ["symbol"]
                }
            }
        }
    },
    {
        "name": "xueqiu_hot_posts",
        "func": xueqiu_hot_posts,
        "schema": {
            "type": "function",
            "function": {
                "name": "xueqiu_hot_posts",
                "description": "Get trending financial discussions and investor sentiment from the Xueqiu community.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of posts to return.", "default": 20}
                    }
                }
            }
        }
    },
    {
        "name": "bilibili_metadata",
        "func": bilibili_metadata,
        "schema": {
            "type": "function",
            "function": {
                "name": "bilibili_metadata",
                "description": "Get metadata for a Bilibili video (titles, tags, stats). Useful for researching technical and creative content in the Bilibili community.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Bilibili video URL."}
                    },
                    "required": ["url"]
                }
            }
        }
    },
    {
        "name": "xhs_search",
        "func": xhs_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "xhs_search",
                "description": "Search for notes and product reviews on XiaoHongShu (Red). Ideal for consumer products, lifestyle trends, and visual research.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword or topic."}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "weibo_trendings",
        "func": weibo_trendings,
        "schema": {
            "type": "function",
            "function": {
                "name": "weibo_trendings",
                "description": "Get the current top search trends on Weibo. Best for monitoring breaking news and viral topics in China.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of trending items to return.", "default": 20}
                    }
                }
            }
        }
    },
    {
        "name": "rss_read",
        "func": rss_read,
        "schema": {
            "type": "function",
            "function": {
                "name": "rss_read",
                "description": "Read and parse an RSS feed URL into clean text. Use this for monitoring blogs, news feeds, or podcasts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Full RSS URL."},
                        "limit": {"type": "integer", "description": "Number of recent entries to fetch.", "default": 5}
                    },
                    "required": ["url"]
                }
            }
        }
    },
    {
        "name": "wechat_search",
        "func": wechat_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "wechat_search",
                "description": "Search for deep-dive articles and official account posts on WeChat.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                        "limit": {"type": "integer", "description": "Number of articles to return.", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "linkedin_profile",
        "func": linkedin_profile,
        "schema": {
            "type": "function",
            "function": {
                "name": "linkedin_profile",
                "description": "Get profile details for a specific LinkedIn user. Use for professional backgrounds, hiring, or corporate research.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "LinkedIn profile URL."}
                    },
                    "required": ["url"]
                }
            }
        }
    },
    {
        "name": "arxiv_search",
        "func": arxiv_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "arxiv_search",
                "description": "Powerful academic research tool. Search ArXiv for scientific papers, preprints, and deep technical literature. Returns titles, authors, full abstracts, and direct PDF links. Essential for staying current on AI, physics, math, and CS research.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Technical search query (e.g. 'Self-Attention Transformers' or 'Quantum Error Correction')."},
                        "limit": {"type": "integer", "description": "Number of relevant papers to return (default 5, max 10).", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "wikipedia_search",
        "func": wikipedia_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "wikipedia_search",
                "description": "Find relevant Wikipedia page titles and URLs for a given topic. Use this as a first step to identify the exact page name before reading its content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "General topic or entity to search for (e.g. 'Large Language Model' or 'Marie Curie')."}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "wikipedia_read",
        "func": wikipedia_read,
        "schema": {
            "type": "function",
            "function": {
                "name": "wikipedia_read",
                "description": "Fetch the full, clean plain-text content of a specific Wikipedia page. Requires a precise page title (best obtained from wikipedia_search). Ideal for deep-dives into verified general knowledge.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "The exact title of the Wikipedia page (e.g. 'Artificial intelligence' or 'Alan Turing')."}
                    },
                    "required": ["title"]
                }
            }
        }
    },
    {
        "name": "reddit_search",
        "func": reddit_search,
        "schema": {
            "type": "function",
            "function": {
                "name": "reddit_search",
                "description": "Search Reddit for posts, discussions, and community opinions on a topic. Returns titles, links, vote counts, and subreddit info. Ideal for subjective, experience-based, or recent casual information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query or topic."}
                    },
                    "required": ["query"]
                }
            }
        }
    },
    {
        "name": "reddit_read",
        "func": reddit_read,
        "schema": {
            "type": "function",
            "function": {
                "name": "reddit_read",
                "description": "Read the full text of a specific Reddit post along with its top comments. Use this to dive deep into a specific thread or discussion found via reddit_search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The full URL of the Reddit post to read."}
                    },
                    "required": ["url"]
                }
            }
        }
    }
]
