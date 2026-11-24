"""WebFetch 工具 — 抓取 URL 并转为文本返回

与 claude-code 的差异：claude-code 用小模型对页面内容跑 prompt，
mycode 直接返回页面文本（截断），由主 agent 处理 prompt。
保留 url/prompt/offset 接口契约。
"""
from __future__ import annotations
import re
import time
import urllib.parse as urlparse

import requests

# 简单内存缓存：(url, timestamp)
_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 900  # 15 分钟

# 返回内容上限（字符数）
_MAX_CHARS = 30000


def _html_to_text(html: str) -> str:
    """简易 HTML → 文本转换（非完整 markdown，够用即可）"""
    # 移除 script/style
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # 标题
    for tag in ("h1", "h2", "h3", "h4"):
        html = re.sub(rf"<{tag}[^>]*>(.*?)</{tag}>", r"\n\n## \1\n", html, flags=re.DOTALL | re.IGNORECASE)
    # 段落、换行
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", html, flags=re.DOTALL | re.IGNORECASE)
    # 链接：保留文本和 href
    html = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", html, flags=re.DOTALL | re.IGNORECASE)
    # 列表项
    html = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", html, flags=re.DOTALL | re.IGNORECASE)
    # 代码块
    html = re.sub(r"<pre[^>]*>(.*?)</pre>", r"\n```\n\1\n```\n", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", html, flags=re.DOTALL | re.IGNORECASE)
    # 移除所有剩余标签
    html = re.sub(r"<[^>]+>", "", html)
    # HTML 实体
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # 压缩空白
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def _is_local_host(hostname: str) -> bool:
    """检查是否是本地地址（无点或 localhost）"""
    if hostname == "localhost":
        return True
    if "." not in hostname:
        return True
    return False


def execute(url: str, prompt: str, offset: int = 0) -> str:
    """抓取 URL，转为文本，返回内容片段"""
    # HTTP → HTTPS
    if url.startswith("http://"):
        url = "https://" + url[7:]

    parsed = urlparse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return f"Error: invalid URL: {url}"
    if _is_local_host(parsed.hostname or ""):
        return "Error: localhost and hostnames without a dot are not supported. Use curl via Bash for local servers."

    # 检查缓存
    now = time.time()
    if url in _cache:
        cached_time, cached_text = _cache[url]
        if now - cached_time < _CACHE_TTL:
            text = cached_text
        else:
            del _cache[url]
            text = None
    else:
        text = None

    if text is None:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "mycode/0.1"})
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "html" in content_type or "<html" in resp.text[:500].lower():
                text = _html_to_text(resp.text)
            else:
                text = resp.text
            _cache[url] = (now, text)
        except requests.RequestException as e:
            return f"Error: fetch failed: {type(e).__name__}: {e}"

    # 分页
    total = len(text)
    chunk = text[offset : offset + _MAX_CHARS]
    result = chunk
    if offset + _MAX_CHARS < total:
        next_offset = offset + _MAX_CHARS
        result += f"\n\n[... truncated, {total - next_offset} chars remaining, use offset={next_offset} to continue]"
    result = f"[WebFetch] {url}\n(prompt: {prompt})\n\n{result}"
    return result


TOOL_SCHEMA = {
    "name": "WebFetch",
    "description": (
        "Fetch a URL, convert HTML to text, and return the content. "
        "The `prompt` parameter is stored but content is returned directly for the agent to process. "
        "HTTP is upgraded to HTTPS. Fails on localhost. Content is cached for 15 minutes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch content from.", "format": "uri"},
            "prompt": {"type": "string", "description": "The prompt to run on the fetched content."},
            "offset": {
                "type": "integer",
                "description": "Character position to start reading from for pagination.",
                "minimum": 0,
            },
        },
        "required": ["url", "prompt"],
    },
    "execute": execute,
}