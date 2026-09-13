import json
import re
from typing import Dict, Any, List, Optional
from ..models.schemas import ProjectAnalysis

class AnalyzerService:
    @staticmethod
    def analyze_repository_data(repo_info: Dict[str, Any]) -> ProjectAnalysis:
        files: List[str] = repo_info.get("files", [])
        file_contents: Dict[str, str] = repo_info.get("file_contents", {})
        primary_lang = repo_info.get("primary_language", "Unknown")

        # Config files presence check across root and monorepo folders
        has_pkg_json = any(f in files or f in file_contents for f in ("package.json", "frontend/package.json", "client/package.json"))
        has_req_txt = any(f in files or f in file_contents for f in ("requirements.txt", "backend/requirements.txt", "api/requirements.txt", "server/requirements.txt"))
        has_pyproject = any(f in files or f in file_contents for f in ("pyproject.toml", "backend/pyproject.toml", "api/pyproject.toml"))
        has_dockerfile = any(f in files or f in file_contents for f in ("Dockerfile", "backend/Dockerfile", "docker/Dockerfile"))
        has_vercel_json = any(f in files or f in file_contents for f in ("vercel.json", "frontend/vercel.json"))
        has_render_yaml = any(f in files or f in file_contents for f in ("render.yaml", "backend/render.yaml"))

        # Detect package managers
        package_manager = None
        if "pnpm-lock.yaml" in files or "frontend/pnpm-lock.yaml" in files:
            package_manager = "pnpm"
        elif "yarn.lock" in files or "frontend/yarn.lock" in files:
            package_manager = "yarn"
        elif "package-lock.json" in files or "frontend/package-lock.json" in files or has_pkg_json:
            package_manager = "npm"
        elif has_pyproject and ("poetry.lock" in files or "[tool.poetry]" in file_contents.get("pyproject.toml", "") or "[tool.poetry]" in file_contents.get("backend/pyproject.toml", "")):
            package_manager = "poetry"
        elif has_req_txt:
            package_manager = "pip"
        elif "Cargo.toml" in files:
            package_manager = "cargo"
        elif "go.mod" in files:
            package_manager = "go"

        # Framework and language detection
        detected_lang = primary_lang
        frontend_fw = None
        backend_fw = None

        # Inspect package.json
        pkg_json_content = file_contents.get("package.json") or file_contents.get("frontend/package.json")
        pkg_data = {}
        if pkg_json_content:
            try:
                pkg_data = json.loads(pkg_json_content)
            except Exception:
                pass

        deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
        
        # Check JavaScript / TypeScript frameworks
        if "next" in deps:
            frontend_fw = "Next.js"
            if detected_lang in ("Unknown", "HTML", "CSS"):
                detected_lang = "TypeScript" if "typescript" in deps else "JavaScript"
        elif "react" in deps:
            frontend_fw = "React" + (" (Vite)" if "vite" in deps else "")
            if detected_lang in ("Unknown", "HTML", "CSS"):
                detected_lang = "TypeScript" if "typescript" in deps else "JavaScript"
        elif "vue" in deps or "nuxt" in deps:
            frontend_fw = "Nuxt" if "nuxt" in deps else "Vue"
            if detected_lang in ("Unknown", "HTML", "CSS"):
                detected_lang = "JavaScript"
        elif "svelte" in deps or "@sveltejs/kit" in deps:
            frontend_fw = "SvelteKit" if "@sveltejs/kit" in deps else "Svelte"
        elif "@angular/core" in deps:
            frontend_fw = "Angular"
        elif "vite" in deps:
            frontend_fw = "Vite"

        if "express" in deps:
            backend_fw = "Express"
        elif "fastify" in deps:
            backend_fw = "Fastify"
        elif "koa" in deps:
            backend_fw = "Koa"
        elif "@nestjs/core" in deps:
            backend_fw = "NestJS"

        # Check Python backend frameworks
        req_content = file_contents.get("requirements.txt") or file_contents.get("backend/requirements.txt") or ""
        pyproject_content = file_contents.get("pyproject.toml") or file_contents.get("backend/pyproject.toml") or ""
        python_text = (req_content + "\n" + pyproject_content).lower()

        if "fastapi" in python_text:
            backend_fw = "FastAPI"
            detected_lang = "Python"
        elif "flask" in python_text:
            backend_fw = "Flask"
            detected_lang = "Python"
        elif "django" in python_text:
            backend_fw = "Django"
            detected_lang = "Python"
        elif has_req_txt or has_pyproject or "main.py" in files or "app.py" in files:
            if not backend_fw and not frontend_fw:
                backend_fw = "Python Service"
            if detected_lang == "Unknown":
                detected_lang = "Python"

        # Check for static HTML/CSS
        if not frontend_fw and not backend_fw:
            if "index.html" in files:
                frontend_fw = "Static HTML/JS"
                if detected_lang == "Unknown":
                    detected_lang = "HTML/CSS"

        # Determine overall project type
        if frontend_fw and backend_fw:
            project_type = "full_stack"
            framework_label = f"{frontend_fw} + {backend_fw}"
        elif frontend_fw:
            project_type = "frontend"
            framework_label = frontend_fw
        elif backend_fw:
            project_type = "backend"
            framework_label = backend_fw
        else:
            project_type = "static" if "index.html" in files else "custom"
            framework_label = primary_lang

        # Detect environment variables from .env.example, README, code
        detected_env_vars = AnalyzerService._extract_env_vars(file_contents)

        # Truncate README snippet for context
        readme = file_contents.get("README.md", "")
        readme_snippet = readme[:600] if readme else None

        # Build list of key detected files for UI display
        key_detected = [f for f in [
            "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
            "requirements.txt", "pyproject.toml", "Dockerfile", "vercel.json",
            "render.yaml", ".env.example", "README.md", "vite.config.js",
            "vite.config.ts", "next.config.js", "next.config.mjs"
        ] if f in files or f in file_contents]

        return ProjectAnalysis(
            repo_name=repo_info.get("repo", "unknown"),
            repo_owner=repo_info.get("owner", "unknown"),
            repo_url=repo_info.get("clean_url", ""),
            default_branch=repo_info.get("default_branch", "main"),
            language=detected_lang,
            framework=framework_label,
            project_type=project_type,
            frontend=frontend_fw,
            backend=backend_fw,
            package_manager=package_manager,
            has_package_json=has_pkg_json,
            has_requirements_txt=has_req_txt,
            has_pyproject_toml=has_pyproject,
            has_dockerfile=has_dockerfile,
            has_vercel_json=has_vercel_json,
            has_render_yaml=has_render_yaml,
            detected_files=key_detected,
            detected_env_vars=detected_env_vars,
            readme_snippet=readme_snippet
        )

    @staticmethod
    def _extract_env_vars(file_contents: Dict[str, str]) -> List[str]:
        """Extracts declared environment variables from .env.example and files."""
        env_vars = set()
        
        # From .env.example
        env_example = file_contents.get(".env.example", "")
        for line in env_example.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key = line.split("=")[0].strip()
                if re.match(r"^[A-Z0-9_]+$", key):
                    env_vars.add(key)

        # Common heuristics if empty
        if not env_vars:
            combined = "\n".join(file_contents.values())
            matches = re.findall(r"(?:process\.env\.|os\.(?:environ|getenv)\([\"'])([A-Z0-9_]{3,})", combined)
            for m in matches[:6]:
                if m not in ("PATH", "NODE_ENV", "HOME", "USER"):
                    env_vars.add(m)

        return sorted(list(env_vars))
