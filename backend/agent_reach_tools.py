import sys
import os
import subprocess
import json
import asyncio
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

# --- Web Tools ---

async def web_read(url: str) -> str:
    """Read any web page as Markdown using Jina Reader."""
    # Use jina.ai reader via curl
    return await asyncio.to_thread(run_cli_command, ["curl", "-s", f"https://r.jina.ai/{url}"])

async def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using Exa via mcporter. Returns AI-optimized search results."""
    # The user asked to replace ddg with the one library offers. Exa is the library's choice.
    cmd = ["mcporter", "call", f"exa.web_search_exa(query: \"{query}\", numResults: {num_results})"]
    return await asyncio.to_thread(run_cli_command, cmd)

async def web_search_batch(queries: List[str], num_results: int = 5) -> str:
    """Search the web for multiple queries in parallel using Exa. All queries execute simultaneously and results are returned together."""
    async def _search_one(q: str) -> str:
        cmd = ["mcporter", "call", f"exa.web_search_exa(query: \"{q}\", numResults: {num_results})"]
        result = await asyncio.to_thread(run_cli_command, cmd)
        return f"### Query: {q}\n{result}"

    results = await asyncio.gather(*[_search_one(q) for q in queries])
    return "\n\n---\n\n".join(results)

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
                "description": "Powerful semantic web search (Exa). Unlike keyword search, this finds pages that are relevant to the *meaning* of your query. Returns AI-optimized snippets. Use for general research, finding specific data points, and current events.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query or research objective."},
                        "num_results": {"type": "integer", "description": "Number of high-quality results to return (default 5).", "default": 5}
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
                "description": "Run multiple semantic web searches (Exa) in parallel in a single call. All queries execute simultaneously, making this dramatically faster than sequential web_search calls. Always prefer this over calling web_search multiple times. Use when researching multiple topics, angles, or data points at once. IMPORTANT: Exa is a neural semantic search engine — write each query as a complete natural-language sentence or question describing the content you want to find, NOT as keyword strings. Example good query: 'What are the performance benchmarks and architectural improvements of NVIDIA Blackwell GPUs?'. Example bad query: 'NVIDIA Blackwell GPU benchmark specs'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of search queries to execute in parallel. Send all related queries at once (e.g. 10-20 queries covering different angles of your research objective)."
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
    }
]
