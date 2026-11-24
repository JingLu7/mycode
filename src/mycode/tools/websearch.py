"""WebSearch 工具 — 网页搜索

双搜索源：Bing CN（国内可达）+ DuckDuckGo（海外 fallback）。
底层用 curl 子进程发起请求（沙箱内 python socket 的 DNS 间歇失败，curl 更健壮）。
解析 HTML 结果页返回标题+URL+摘要，支持 allowed_domains / blocked_domains 过滤。
"""
from __future__ import annotations
import re
import time
import subprocess
import html as htmlmod
from urllib.parse import urlencode

_DDG_URL = "https://html.duckduckgo.com/html/"
_BING_URL = "https://cn.bing.com/search"
_MAX_RESULTS = 10
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Bing CN 反爬降级：约 1/5 请求返回真实结果页，其余返回无结果块（84KB 空 b_results）。
# 故重试直到拿到非空结果。
_BING_ATTEMPTS = 8
_BING_RETRY_INTERVAL = 0.6


def _curl_get(url: str, params: dict | None = None, timeout: int = 20) -> str:
    """curl GET，返回响应体；任何失败返回空串。"""
    if params:
        url = f"{url}?{urlencode(params)}"
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "-H", f"User-Agent: {_UA}", url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        return r.stdout or ""
    except Exception:
        return ""


def _curl_post(url: str, data: dict, timeout: int = 20) -> str:
    """curl POST（表单），返回响应体；任何失败返回空串。"""
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "-X", "POST", "-H", f"User-Agent: {_UA}",
             "--data", urlencode(data), url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        return r.stdout or ""
    except Exception:
        return ""


def _parse_ddg_results(html: str) -> list[dict[str, str]]:
    """解析 DuckDuckGo HTML 结果页"""
    results = []
    # DuckDuckGo HTML 结果块
    blocks = re.findall(r'<div class="result[^"]*">(.*?)</div>\s*(?=<div class="result|</div>\s*</div>)', html, re.DOTALL)
    if not blocks:
        # 备用解析：找所有 result__a 链接
        links = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
        snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        for i, (href, title) in enumerate(links):
            # DuckDuckGo 的 href 是 redirect 链接，需要提取真实 URL
            real_url = _extract_real_url(href)
            clean_title = re.sub(r"<[^>]+>", "", title).strip()
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
            if real_url and clean_title:
                results.append({"title": clean_title, "url": real_url, "snippet": snippet})
    else:
        for block in blocks:
            link_match = re.search(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if not link_match:
                continue
            href = link_match.group(1)
            title = re.sub(r"<[^>]+>", "", link_match.group(2)).strip()
            real_url = _extract_real_url(href)
            snippet_match = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip() if snippet_match else ""
            if real_url and title:
                results.append({"title": title, "url": real_url, "snippet": snippet})
    return results


def _extract_real_url(href: str) -> str:
    """从 DuckDuckGo redirect URL 中提取真实 URL"""
    # 格式: //duckduckgo.com/l/?uddg=ENCODED_URL&rut=...
    if "uddg=" in href:
        match = re.search(r"uddg=([^&]+)", href)
        if match:
            from urllib.parse import unquote

            return unquote(match.group(1))
    if href.startswith("//"):
        href = "https:" + href
    return href


def _parse_bing_results(html_text: str) -> list[dict[str, str]]:
    """解析 Bing CN HTML 结果页"""
    results = []
    # Bing 结果在 <li class="b_algo" ...> 中，标题在 <h2><a href>标题</a></h2>
    blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html_text, re.DOTALL)
    for block in blocks:
        title_match = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not title_match:
            continue
        url = title_match.group(1)
        title = re.sub(r"<[^>]+>", "", title_match.group(2)).strip()
        title = htmlmod.unescape(title)
        # 摘要在 <div class="b_caption"> <p> 中
        snippet_match = re.search(r'<div class="b_caption">.*?<p[^>]*>(.*?)</p>', block, re.DOTALL)
        snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip() if snippet_match else ""
        snippet = htmlmod.unescape(snippet)
        if url and title:
            results.append({"title": title, "url": url, "snippet": snippet})
    return results


def _domain_of(url: str) -> str:
    """提取 URL 的域名"""
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower()



def execute(
    query: str,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
) -> str:
    """执行网页搜索，返回结果列表"""
    results: list[dict[str, str]] = []

    # 搜索源 1: Bing CN。Bing 对无 cookie 请求常返回 200 但无结果块（反爬降级），
    # 实测约 1/5 概率返回真实结果页，故重试直到拿到非空结果。
    for _ in range(_BING_ATTEMPTS):
        parsed = _parse_bing_results(_curl_get(_BING_URL, {"q": query, "count": "20"}))
        if parsed:
            results = parsed
            break
        time.sleep(_BING_RETRY_INTERVAL)

    # 搜索源 2: DuckDuckGo（fallback，海外可达时用）
    if not results:
        results = _parse_ddg_results(_curl_post(_DDG_URL, {"q": query}))

    # 两个搜索源都无结果：可能是网络不可达或被反爬拦截
    if not results:
        return (
            "Error: WebSearch returned no results "
            "(Bing CN and DuckDuckGo both failed or were blocked).\n"
            "This may be a network issue or anti-bot blocking — "
            "do not fabricate search results; state this limitation to the user."
        )

    # 域名过滤
    if allowed_domains:
        allowed = {d.lower() for d in allowed_domains}
        results = [r for r in results if _domain_of(r["url"]) in allowed]
    if blocked_domains:
        blocked = {d.lower() for d in blocked_domains}
        results = [r for r in results if _domain_of(r["url"]) not in blocked]

    if not results:
        return (
            f"No results found for: {query}\n"
            "If this is unexpected, the search may have failed silently — "
            "do not fabricate results."
        )

    # 格式化输出
    lines = [f"[WebSearch] query: {query}", f"Found {len(results)} results:\n"]
    for i, r in enumerate(results[:_MAX_RESULTS], 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        if r["snippet"]:
            lines.append(f"   {r['snippet'][:200]}")
        lines.append("")
    return "\n".join(lines)


TOOL_SCHEMA = {
    "name": "WebSearch",
    "description": (
        "Search the web using Bing CN (primary) or DuckDuckGo (fallback). "
        "Returns result blocks with titles, URLs, and snippets. "
        "Use allowed_domains / blocked_domains to filter results."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query.", "minLength": 2},
            "allowed_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Only include results from these domains.",
            },
            "blocked_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Never include results from these domains.",
            },
        },
        "required": ["query"],
    },
    "execute": execute,
}