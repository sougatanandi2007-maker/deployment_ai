import json
import re
from typing import Dict, Any, List, Optional
import httpx
from ..config import settings
from ..models.schemas import ProjectAnalysis, DeploymentPlan, ErrorDiagnosis

class AIAgentService:
    @staticmethod
    def validate_command_safety(command: Optional[str]) -> bool:
        """Validates that a command adheres to security constraints and allowlists."""
        if not command or not command.strip():
            return True
        cmd = command.strip()

        # Split chained commands (&&) and validate each command individually
        sub_commands = [c.strip() for c in cmd.split("&&") if c.strip()]
        if not sub_commands:
            return False

        for sub in sub_commands:
            # Reject dangerous shell injection symbols
            for blocked in settings.BLOCKED_SHELL_PATTERNS:
                if blocked in sub:
                    return False

            tokens = sub.split()
            if not tokens:
                return False

            first_token = tokens[0].lower()
            base_cmd = first_token.split("/")[-1].split("\\")[-1]
            if base_cmd not in settings.SAFE_COMMAND_PREFIXES:
                return False

        return True

    @classmethod
    async def generate_deployment_plan(
        cls, 
        analysis: ProjectAnalysis, 
        user_description: Optional[str] = None, 
        preferred_target: Optional[str] = None
    ) -> DeploymentPlan:
        """Generates a structured deployment plan with deterministic intelligence and optional LLM enrichment."""
        
        # 1. Platform recommendation logic
        pref = (preferred_target or "").lower().strip()
        
        if pref in ("vercel", "render"):
            frontend_platform = pref if analysis.frontend else None
            backend_platform = pref if analysis.backend else None
            if not frontend_platform and not backend_platform:
                frontend_platform = pref
        else:
            if analysis.project_type == "full_stack":
                frontend_platform = "Vercel"
                backend_platform = "Render"
            elif analysis.project_type in ("frontend", "static"):
                frontend_platform = "Vercel"
                backend_platform = None
            elif analysis.project_type == "backend":
                frontend_platform = None
                backend_platform = "Render"
            else:
                frontend_platform = "Vercel"
                backend_platform = None

        # 2. Build & Start command derivation
        pkg_manager = analysis.package_manager or "npm"
        build_command = None
        start_command = None

        has_backend_dir = any("backend/" in f for f in analysis.detected_files)
        has_frontend_dir = any("frontend/" in f or "client/" in f for f in analysis.detected_files)

        # If user explicitly preferred Render or if backend-only deployment:
        if pref == "render" or (not frontend_platform and backend_platform):
            if analysis.backend:
                if "FastAPI" in analysis.backend:
                    if has_backend_dir:
                        build_command = "pip install -r backend/requirements.txt"
                        start_command = "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT"
                    else:
                        build_command = "pip install -r requirements.txt" if analysis.has_requirements_txt else None
                        start_command = "uvicorn main:app --host 0.0.0.0 --port $PORT"
                elif "Flask" in analysis.backend:
                    build_command = "pip install -r backend/requirements.txt" if has_backend_dir else ("pip install -r requirements.txt" if analysis.has_requirements_txt else None)
                    start_command = "gunicorn app:app"
                elif "Express" in analysis.backend:
                    build_command = f"{pkg_manager} install"
                    start_command = "node server.js"
                elif analysis.has_requirements_txt:
                    build_command = "pip install -r backend/requirements.txt" if has_backend_dir else "pip install -r requirements.txt"
                    start_command = "python app.py" if has_backend_dir else "python main.py"
        else:
            if analysis.frontend:
                if "Next.js" in analysis.frontend:
                    build_command = f"{pkg_manager} run build"
                    start_command = f"{pkg_manager} start"
                elif "React" in analysis.frontend or "Vite" in analysis.frontend:
                    build_command = f"{pkg_manager} run build"
                    start_command = f"{pkg_manager} run preview"
                elif "Vue" in analysis.frontend or "Nuxt" in analysis.frontend:
                    build_command = f"{pkg_manager} run build"
                    start_command = f"{pkg_manager} start"
                elif analysis.has_package_json:
                    build_command = f"{pkg_manager} run build"
                    start_command = f"{pkg_manager} start"
            elif analysis.backend:
                if "FastAPI" in analysis.backend:
                    if has_backend_dir:
                        build_command = "pip install -r backend/requirements.txt"
                        start_command = "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT"
                    else:
                        build_command = "pip install -r requirements.txt" if analysis.has_requirements_txt else None
                        start_command = "uvicorn main:app --host 0.0.0.0 --port $PORT"

        # 3. Formulate step-by-step plan
        plan_steps: List[str] = [
            f"Clone and authenticate repository {analysis.repo_owner}/{analysis.repo_name}",
            f"Set up environment dependencies using {analysis.package_manager or 'standard tooling'}",
        ]

        if frontend_platform:
            plan_steps.append(f"Deploy frontend ({analysis.frontend or 'Web UI'}) to {frontend_platform}")
        if backend_platform:
            plan_steps.append(f"Provision and deploy backend ({analysis.backend or 'API Server'}) to {backend_platform}")

        plan_steps.append("Verify public DNS routing and health check endpoints")
        plan_steps.append("Generate secure SSL live URL for user access")

        # 4. Generate Intent Explanation
        explanation = (
            f"The AI Deployment Agent inspected the repository and detected a {analysis.project_type.replace('_', ' ')} application "
            f"built with {analysis.framework} ({analysis.language}). "
        )
        if frontend_platform and backend_platform:
            explanation += (
                f"We recommend deploying the frontend to {frontend_platform} (optimized for edge delivery & static assets) "
                f"and hosting the backend API on {backend_platform} (supporting long-lived processes and database connectivity). "
            )
        elif frontend_platform:
            explanation += f"We recommend deploying to {frontend_platform} with automated CDN routing and serverless function support. "
        else:
            explanation += f"We recommend deploying the backend service to {backend_platform}. "

        explanation += (
            f"Before starting deployment, review the build command (`{build_command or 'default'}`) "
            f"and configure any necessary environment variables."
        )

        # 5. Optional LLM enhancement if key is available
        llm_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
        if llm_key and llm_key.strip():
            try:
                enhanced_explanation = await cls._query_llm_for_plan(analysis, user_description, llm_key)
                if enhanced_explanation:
                    explanation = enhanced_explanation
            except Exception:
                pass  # Graceful fallback to deterministic explanation

        # Validate security of commands
        is_safe = cls.validate_command_safety(build_command) and cls.validate_command_safety(start_command)

        return DeploymentPlan(
            project_type=analysis.project_type,
            frontend=analysis.frontend,
            backend=analysis.backend,
            frontend_platform=frontend_platform,
            backend_platform=backend_platform,
            build_command=build_command,
            start_command=start_command,
            environment_variables=analysis.detected_env_vars,
            deployment_plan=plan_steps,
            intent_explanation=explanation,
            is_safe_command=is_safe
        )

    @classmethod
    async def diagnose_error(cls, error_log: str, context: Dict[str, Any]) -> ErrorDiagnosis:
        """Analyzes a deployment failure, diagnosing root cause and proposing user-approved remediations."""
        error_lower = error_log.lower()
        root_cause = "General deployment or build failure"
        explanation = "The deployment provider reported an error during the build or run cycle."
        suggested_fix = "Check the logs below and ensure all required environment variables and build commands are correct."
        recommended_changes: Dict[str, Any] = {}

        if "missing secret" in error_lower or "env" in error_lower or "unauthorized" in error_lower:
            root_cause = "Missing or Invalid Environment Variables"
            explanation = "The application build or initialization requires specific environment secrets or API tokens."
            suggested_fix = "Provide the missing environment variables in the configuration panel."
            recommended_changes["environment_variables"] = {"ENV_VAR_REQUIRED": "VALUE"}

        elif "command not found" in error_lower or "elfformat" in error_lower or "npm err!" in error_lower or "vite: not found" in error_lower:
            root_cause = "Build Command Failure / Missing Dependency"
            explanation = "The project build script failed to locate a required dependency or the package manager build script exited with an error."
            suggested_fix = "Update the build command to ensure dependencies are installed first (e.g. npm install && npm run build)."
            recommended_changes["build_command"] = "npm install && npm run build"

        elif "port" in error_lower or "address already in use" in error_lower:
            root_cause = "Port Binding Mismatch"
            explanation = "Cloud platforms assign a dynamic $PORT environment variable. The server attempted to bind to a hardcoded port."
            suggested_fix = "Configure the start command to bind to 0.0.0.0 and listen on the platform provided $PORT."
            recommended_changes["start_command"] = "uvicorn main:app --host 0.0.0.0 --port $PORT"

        elif "token" in error_lower or "401" in error_lower or "403" in error_lower:
            root_cause = "Provider Authentication Failure"
            explanation = "The deployment platform API rejected the request due to an invalid or missing API Token."
            suggested_fix = "Verify that your VERCEL_TOKEN or RENDER_API_KEY is configured correctly in your environment or settings."

        # Optional LLM diagnosis if key is provided
        llm_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY or settings.OPENAI_API_KEY
        if llm_key and llm_key.strip():
            try:
                llm_diag = await cls._query_llm_for_diagnosis(error_log, context, llm_key)
                if llm_diag:
                    return llm_diag
            except Exception:
                pass

        return ErrorDiagnosis(
            error_summary=error_log[:200] if len(error_log) > 200 else error_log,
            root_cause=root_cause,
            explanation=explanation,
            suggested_fix=suggested_fix,
            recommended_changes=recommended_changes,
            retry_allowed=True
        )

    @staticmethod
    async def _query_llm_for_plan(analysis: ProjectAnalysis, user_desc: Optional[str], api_key: str) -> Optional[str]:
        """Queries LLM API for an enriched intent explanation."""
        prompt = (
            f"You are an expert AI DevOps deployment agent. "
            f"A user wants to deploy GitHub repository {analysis.repo_name} ({analysis.framework}, {analysis.language}). "
            f"User notes: {user_desc or 'None'}. "
            f"Briefly explain in 2-3 sentences the deployment strategy and recommendations for this repository."
        )
        
        # Support OpenAI or Gemini endpoint
        is_gemini = api_key.startswith("AIza") or bool(settings.GEMINI_API_KEY and api_key == settings.GEMINI_API_KEY)
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" if is_gemini else "https://api.openai.com/v1/chat/completions"
        model = "gemini-1.5-flash" if is_gemini else "gpt-4o-mini"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        return None

    @staticmethod
    async def _query_llm_for_diagnosis(error_log: str, context: Dict[str, Any], api_key: str) -> Optional[ErrorDiagnosis]:
        """Queries LLM API for error diagnosis and structured remediation."""
        prompt = (
            f"Analyze this cloud deployment error for a {context.get('framework', 'web')} project on {context.get('platform', 'cloud')}:\n\n"
            f"Error Log:\n{error_log}\n\n"
            f"Respond in valid JSON only with keys:\n"
            f"root_cause (short string), explanation (string), suggested_fix (string), recommended_changes (object)."
        )
        is_gemini = api_key.startswith("AIza") or bool(settings.GEMINI_API_KEY and api_key == settings.GEMINI_API_KEY)
        url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" if is_gemini else "https://api.openai.com/v1/chat/completions"
        model = "gemini-1.5-flash" if is_gemini else "gpt-4o-mini"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "max_tokens": 300
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                res = json.loads(data["choices"][0]["message"]["content"])
                return ErrorDiagnosis(
                    error_summary=error_log[:200],
                    root_cause=res.get("root_cause", "Build Failure"),
                    explanation=res.get("explanation", ""),
                    suggested_fix=res.get("suggested_fix", ""),
                    recommended_changes=res.get("recommended_changes", {}),
                    retry_allowed=True
                )
        return None
