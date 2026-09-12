import re
import base64
import json
from typing import Dict, Any, List, Optional
import httpx
from ..config import settings

class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Deployment-Agent/1.0",
        }
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    @staticmethod
    def parse_repo_url(url: str) -> Dict[str, str]:
        """Extracts owner and repo name from various GitHub URL formats."""
        url = url.strip().rstrip("/")
        # Matches https://github.com/owner/repo or git@github.com:owner/repo
        pattern = r"(?:https?://github\.com/|git@github\.com:)([\w\-\.]+)/([\w\-\.]+?)(?:\.git|/tree/([\w\-\./]+)|/?)$"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(f"Invalid GitHub repository URL: {url}. Please provide a valid GitHub link.")
        
        owner = match.group(1)
        repo = match.group(2)
        branch = match.group(3) if match.group(3) else None
        return {
            "owner": owner,
            "repo": repo,
            "branch": branch or "main",
            "clean_url": f"https://github.com/{owner}/{repo}"
        }

    async def fetch_repo_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetches basic repo information from GitHub API."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 404:
                raise ValueError(f"Repository {owner}/{repo} not found on GitHub or is private.")
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                raise PermissionError("GitHub API rate limit exceeded. Please configure GITHUB_TOKEN in settings.")
            resp.raise_for_status()
            return resp.json()

    async def fetch_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Fetches and decodes the content of a file from GitHub."""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self._get_headers(), params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and data.get("encoding") == "base64" and "content" in data:
                        raw_content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                        return raw_content
                return None
        except Exception:
            return None

    async def fetch_repo_tree(self, owner: str, repo: str, default_branch: str) -> List[str]:
        """Fetches recursive file paths for the repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    tree = data.get("tree", [])
                    return [item["path"] for item in tree if item.get("type") in ("blob", "tree")]
        except Exception:
            pass

        # Fallback: query root contents if git tree fails
        url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self._get_headers(), params={"ref": default_branch})
                if resp.status_code == 200:
                    items = resp.json()
                    return [item["name"] for item in items if isinstance(item, dict) and "name" in item]
        except Exception:
            pass
        return []

    async def inspect_repository(self, repo_url: str) -> Dict[str, Any]:
        """Full inspection returning metadata, detected files, and key file contents."""
        parsed = self.parse_repo_url(repo_url)
        owner = parsed["owner"]
        repo = parsed["repo"]

        repo_meta = await self.fetch_repo_details(owner, repo)
        default_branch = repo_meta.get("default_branch") or parsed.get("branch") or "main"

        files = await self.fetch_repo_tree(owner, repo, default_branch)

        # Candidate files to read
        candidate_files = [
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "requirements.txt",
            "pyproject.toml",
            "Dockerfile",
            "docker-compose.yml",
            "vercel.json",
            "render.yaml",
            ".env.example",
            "README.md",
            "vite.config.js",
            "vite.config.ts",
            "next.config.js",
            "next.config.mjs",
            "nuxt.config.js",
            "nuxt.config.ts",
            "index.html",
            "main.py",
            "app.py",
            "server.js",
            "server.ts"
        ]

        # Also inspect subdirectories if it's a monorepo (e.g. frontend/package.json, backend/requirements.txt)
        sub_candidates = [
            "frontend/package.json",
            "client/package.json",
            "backend/requirements.txt",
            "backend/pyproject.toml",
            "backend/package.json",
            "api/package.json",
            "api/requirements.txt",
            "server/package.json"
        ]

        all_candidates = candidate_files + sub_candidates
        file_contents = {}

        # Fetch candidate files that exist in the tree or attempt fetch
        for candidate in all_candidates:
            if not files or candidate in files:
                content = await self.fetch_file_content(owner, repo, candidate, default_branch)
                if content is not None:
                    file_contents[candidate] = content

        return {
            "owner": owner,
            "repo": repo,
            "clean_url": parsed["clean_url"],
            "default_branch": default_branch,
            "description": repo_meta.get("description") or "",
            "primary_language": repo_meta.get("language") or "Unknown",
            "files": files,
            "file_contents": file_contents
        }
