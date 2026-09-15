import json
import re
from typing import Dict, Any, List, Optional
from ..models.schemas import (
    ProjectAnalysis,
    ReadinessCheckItem,
    ReadinessReport,
    IaCFile
)

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

        # Audit readiness
        readiness = AnalyzerService._audit_readiness(
            files=files,
            file_contents=file_contents,
            pkg_data=pkg_data,
            detected_env_vars=detected_env_vars,
            has_pkg_json=has_pkg_json,
            has_req_txt=has_req_txt,
            has_pyproject=has_pyproject,
            has_dockerfile=has_dockerfile,
            has_vercel_json=has_vercel_json,
            has_render_yaml=has_render_yaml,
            package_manager=package_manager,
            project_type=project_type
        )

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
            readme_snippet=readme_snippet,
            readiness_report=readiness
        )

    @staticmethod
    def _audit_readiness(
        files: List[str],
        file_contents: Dict[str, str],
        pkg_data: Dict[str, Any],
        detected_env_vars: List[str],
        has_pkg_json: bool,
        has_req_txt: bool,
        has_pyproject: bool,
        has_dockerfile: bool,
        has_vercel_json: bool,
        has_render_yaml: bool,
        package_manager: Optional[str],
        project_type: str
    ) -> ReadinessReport:
        score = 100
        checks: List[ReadinessCheckItem] = []
        recommendations: List[str] = []

        # 1. Manifest verification
        if has_pkg_json or has_req_txt or has_pyproject or "index.html" in files:
            checks.append(ReadinessCheckItem(
                name="Project Manifest",
                status="pass",
                message=f"Verified root manifest ({'package.json' if has_pkg_json else 'requirements.txt' if has_req_txt else 'pyproject.toml' if has_pyproject else 'index.html'})."
            ))
        else:
            score -= 30
            checks.append(ReadinessCheckItem(
                name="Project Manifest",
                status="fail",
                message="No standard application manifest found in root or common subdirectories."
            ))
            recommendations.append("Add a package.json, requirements.txt, or Dockerfile to the project root.")

        # 2. Build script audit (for JS/TS)
        if has_pkg_json:
            scripts = pkg_data.get("scripts", {})
            if "build" in scripts:
                checks.append(ReadinessCheckItem(
                    name="Build Script",
                    status="pass",
                    message=f"Build script configured in package.json: 'npm run {scripts['build']}'."
                ))
            else:
                score -= 15
                checks.append(ReadinessCheckItem(
                    name="Build Script",
                    status="warn",
                    message="No explicit 'build' script in package.json. Platform will attempt default zero-config build."
                ))
                recommendations.append("Define a 'build' script inside package.json to ensure predictable output.")

        # 3. Lockfile reproducibility
        has_lock = any(f in files for f in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "Pipfile.lock"))
        if has_lock:
            checks.append(ReadinessCheckItem(
                name="Lockfile Integrity",
                status="pass",
                message="Lockfile detected. Dependencies are pinned for deterministic deployment."
            ))
        else:
            score -= 10
            checks.append(ReadinessCheckItem(
                name="Lockfile Integrity",
                status="warn",
                message="No lockfile detected. Deployments will resolve latest matching dependencies."
            ))
            recommendations.append("Commit a lockfile (package-lock.json, pnpm-lock.yaml, or poetry.lock) to guarantee build consistency.")

        # 4. Environment Variables audit
        has_env_example = ".env.example" in files or ".env.sample" in files
        if has_env_example:
            checks.append(ReadinessCheckItem(
                name="Environment Specification",
                status="pass",
                message=f".env.example found specifying {len(detected_env_vars)} potential environment keys."
            ))
        elif detected_env_vars:
            score -= 10
            checks.append(ReadinessCheckItem(
                name="Environment Specification",
                status="warn",
                message=f"{len(detected_env_vars)} environment variables detected in code without a .env.example template."
            ))
            recommendations.append("Create a .env.example file to document required API keys and runtime variables.")
        else:
            checks.append(ReadinessCheckItem(
                name="Environment Specification",
                status="info",
                message="No mandatory environment variables detected for basic standalone execution."
            ))

        # 5. Production Containerization / Config
        if has_dockerfile:
            checks.append(ReadinessCheckItem(
                name="Container Portability",
                status="pass",
                message="Production Dockerfile present. Project supports multi-cloud container deployment."
            ))
        elif has_vercel_json or has_render_yaml:
            checks.append(ReadinessCheckItem(
                name="Cloud Manifest",
                status="pass",
                message="Pre-configured cloud deployment manifest detected."
            ))
        else:
            checks.append(ReadinessCheckItem(
                name="Deployment Config",
                status="info",
                message="Zero-config deployment mode will be orchestrated automatically by AI planner."
            ))

        # Grade calculation
        score = max(30, min(100, score))
        if score >= 90:
            grade = "A"
        elif score >= 75:
            grade = "B"
        elif score >= 60:
            grade = "C"
        else:
            grade = "D"

        return ReadinessReport(
            score=score,
            grade=grade,
            checks=checks,
            recommendations=recommendations
        )

    @staticmethod
    def generate_iac_files(
        analysis: ProjectAnalysis,
        preferred_target: str = "vercel",
        build_command: Optional[str] = None,
        start_command: Optional[str] = None,
        env_vars: Optional[List[str]] = None
    ) -> List[IaCFile]:
        """Generates production-grade GitHub Actions CI/CD workflow, Dockerfile, and platform manifests."""
        target = (preferred_target or "vercel").lower()
        files: List[IaCFile] = []
        repo_name = analysis.repo_name or "app"

        # 1. GitHub Actions CI/CD Workflow
        if target == "vercel":
            ci_yaml = f"""name: Deploy to Vercel

on:
  push:
    branches: [ {analysis.default_branch or 'main'} ]
  workflow_dispatch:

jobs:
  deploy:
    name: Build & Deploy to Vercel
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: '{analysis.package_manager if analysis.package_manager in ("npm", "pnpm", "yarn") else "npm"}'

      - name: Install dependencies
        run: |
          {analysis.package_manager or 'npm'} install

      - name: Build project
        run: |
          {build_command or 'npm run build'}

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{{{ secrets.VERCEL_TOKEN }}}}
          vercel-org-id: ${{{{ secrets.VERCEL_ORG_ID }}}}
          vercel-project-id: ${{{{ secrets.VERCEL_PROJECT_ID }}}}
          vercel-args: '--prod'
"""
        else:
            ci_yaml = f"""name: Deploy to Render

on:
  push:
    branches: [ {analysis.default_branch or 'main'} ]
  workflow_dispatch:

jobs:
  deploy:
    name: Trigger Render Deploy Hook
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Invoke Render Deploy Hook
        run: |
          curl -X POST "${{{{ secrets.RENDER_DEPLOY_HOOK_URL }}}}"
"""
        files.append(IaCFile(
            filename=".github/workflows/deploy.yml",
            content=ci_yaml.strip(),
            description=f"Automated GitHub Actions CI/CD pipeline targeting {target.capitalize()}",
            language="yaml"
        ))

        # 2. Optimized Dockerfile
        if analysis.language.lower() == "python":
            dockerfile = f"""# Multi-stage optimized Python container
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH \\
    PORT=8000

COPY --from=builder /root/.local /root/.local
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        else:
            dockerfile = f"""# Multi-stage production container for {analysis.framework}
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN {build_command or 'npm run build'}

FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
        files.append(IaCFile(
            filename="Dockerfile",
            content=dockerfile.strip(),
            description="Production multi-stage Dockerfile with security & caching best practices",
            language="dockerfile"
        ))

        # 3. Cloud Manifest (vercel.json or render.yaml)
        if target == "vercel":
            vercel_manifest = {
                "version": 2,
                "framework": "vite" if "vite" in analysis.framework.lower() else "nextjs" if "next" in analysis.framework.lower() else None,
                "buildCommand": build_command or "npm run build",
                "outputDirectory": "dist" if "vite" in analysis.framework.lower() else ".next" if "next" in analysis.framework.lower() else "public",
                "rewrites": [
                    { "source": "/(.*)", "destination": "/index.html" }
                ]
            }
            manifest_content = json.dumps({k: v for k, v in vercel_manifest.items() if v is not None}, indent=2)
            files.append(IaCFile(
                filename="vercel.json",
                content=manifest_content,
                description="Vercel single-page application & routing configuration manifest",
                language="json"
            ))
        else:
            render_yaml = f"""services:
  - type: web
    name: {repo_name}-service
    env: python
    buildCommand: {build_command or 'pip install -r requirements.txt'}
    startCommand: {start_command or 'uvicorn main:app --host 0.0.0.0 --port $PORT'}
    plan: free
    autoDeploy: true
    envVars:
"""
            for ev in (env_vars or analysis.detected_env_vars or ["PORT"]):
                render_yaml += f"      - key: {ev}\n        sync: false\n"
            files.append(IaCFile(
                filename="render.yaml",
                content=render_yaml.strip(),
                description="Render Infrastructure-As-Code blueprint specification",
                language="yaml"
            ))

        return files

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
