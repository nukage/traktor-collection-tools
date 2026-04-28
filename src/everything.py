"""Everything search integration via HTTP API."""

import re
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional


EVERYTHING_HTTP_URL = "http://localhost:80"


@dataclass
class EverythingResult:
    name: str
    path: str
    size: Optional[int] = None
    modified: Optional[str] = None


class EverythingClient:
    """Client for Everything HTTP API."""

    def __init__(self, base_url: str = EVERYTHING_HTTP_URL, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _build_url(self, search: str, max_results: int = 100, offset: int = 0) -> str:
        params = urllib.parse.urlencode({
            "search": search,
            "path_info": 1,
            "max_results": max_results,
            "offset": offset,
        })
        return f"{self.base_url}/?{params}"

    def _parse_html_results(self, html: str) -> list[EverythingResult]:
        results = []

        file_tds = re.findall(r'<td class="file">(.*?)</td>', html, re.DOTALL)
        for td in file_tds:
            name_match = re.search(r'<img[^>]*alt="[^"]*">([^<]+)</a>', td)
            if not name_match:
                continue
            name = urllib.parse.unquote(name_match.group(1))

            href_match = re.search(r'href="(/[^"]+)"', td)
            if not href_match:
                continue
            path = urllib.parse.unquote(href_match.group(1))
            if path.startswith("/"):
                path = path[1:]
            path = path.replace("/", "\\")

            results.append(EverythingResult(name=name, path=path))

        for result, size_str in zip(results, re.findall(r'<td class="sizedata">.*?<span[^>]*><nobr>([^<]+)</nobr>', html)):
            size_str = size_str.strip().replace(",", "")
            try:
                if "KB" in size_str:
                    result.size = int(size_str.replace("KB", "").strip()) * 1024
                elif "MB" in size_str:
                    result.size = int(size_str.replace("MB", "").strip()) * 1024 * 1024
                elif "GB" in size_str:
                    result.size = int(size_str.replace("GB", "").strip()) * 1024 * 1024 * 1024
                else:
                    result.size = int(size_str)
            except ValueError:
                result.size = None

        return results

    def search(self, query: str, max_results: int = 100, offset: int = 0) -> list[EverythingResult]:
        """Search Everything for files matching query."""
        url = self._build_url(query, max_results, offset)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                html = response.read().decode("utf-8", errors="replace")
            return self._parse_html_results(html)
        except urllib.error.URLError:
            return []
        except Exception:
            return []

    def search_files_by_name(self, filename: str, max_results: int = 50) -> list[EverythingResult]:
        """Search for files by exact filename match."""
        escaped = re.sub(r'["<>|]', "", filename)
        return self.search(f'"{escaped}"', max_results)

    def is_available(self) -> bool:
        """Check if Everything HTTP server is running."""
        try:
            req = urllib.request.Request(self.base_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False


_client: Optional[EverythingClient] = None


def get_client() -> Optional[EverythingClient]:
    """Get or create the global Everything client."""
    global _client
    if _client is None:
        _client = EverythingClient()
    return _client


def is_everything_available() -> bool:
    """Check if Everything is available."""
    client = get_client()
    return client.is_available() if client else False
