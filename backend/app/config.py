import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Search for .env in current directory and workspace root
env_paths = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env",
    Path(__file__).resolve().parent.parent / ".env"
]
for p in env_paths:
    if p.exists():
        load_dotenv(dotenv_path=p, override=True)


class Settings:
    # API tokens & secrets
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN", "")
    VERCEL_TOKEN: Optional[str] = os.getenv("VERCEL_TOKEN", "")
    RENDER_API_KEY: Optional[str] = os.getenv("RENDER_API_KEY", "")
    
    # LLM keys (supports generic LLM_API_KEY or provider-specific keys)
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY", "")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Command security allowlist
    # Any command intended for execution must match allowlisted base prefixes
    SAFE_COMMAND_PREFIXES: List[str] = [
        "npm",
        "pnpm",
        "yarn",
        "npx",
        "pip",
        "poetry",
        "uvicorn",
        "gunicorn",
        "python",
        "python3",
        "node",
        "cargo",
        "go",
        "docker"
    ]

    # Blocked dangerous tokens
    BLOCKED_SHELL_PATTERNS: List[str] = [
        ";", "||", "|", "`", "$(", "${", ">", ">>", "<",
        "rm -rf", "sudo", "chmod", "curl", "wget", "eval", "exec", "shutdown", "reboot"
    ]

    @classmethod
    def get_configured_providers(cls) -> dict:
        """Returns provider availability status without revealing secret keys."""
        return {
            "github": bool(cls.GITHUB_TOKEN.strip()) if cls.GITHUB_TOKEN else False,
            "vercel": bool(cls.VERCEL_TOKEN.strip()) if cls.VERCEL_TOKEN else False,
            "render": bool(cls.RENDER_API_KEY.strip()) if cls.RENDER_API_KEY else False,
            "llm": bool((cls.LLM_API_KEY or cls.GEMINI_API_KEY or cls.OPENAI_API_KEY or "").strip())
        }

settings = Settings()
