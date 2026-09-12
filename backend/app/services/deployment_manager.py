import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..models.schemas import (
    DeploymentRequest,
    DeploymentStatusResponse,
    LogEntry,
    ErrorDiagnosis,
    RetryRequest
)
from ..config import settings
from .github_service import GitHubService
from .analyzer_service import AnalyzerService
from .agent_service import AIAgentService
from .providers.vercel_provider import VercelProvider
from .providers.render_provider import RenderProvider

class DeploymentManager:
    """Coordinates deployment lifecycles, real-time logging, and self-healing retries."""

    def __init__(self):
        # In-memory deployment store
        self._deployments: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def _get_timestamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def _add_log(self, deployment_id: str, stage: str, level: str, message: str):
        if deployment_id not in self._deployments:
            return
        entry = {
            "timestamp": self._get_timestamp(),
            "stage": stage,
            "level": level,
            "message": message
        }
        self._deployments[deployment_id]["logs"].append(entry)
        self._deployments[deployment_id]["updated_at"] = self._get_timestamp()

    def get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        return self._deployments.get(deployment_id)

    def get_status_response(self, deployment_id: str) -> Optional[DeploymentStatusResponse]:
        dep = self._deployments.get(deployment_id)
        if not dep:
            return None

        diagnosis_obj = None
        if dep.get("diagnosis"):
            diagnosis_obj = ErrorDiagnosis(**dep["diagnosis"])

        return DeploymentStatusResponse(
            deployment_id=dep["deployment_id"],
            repo_url=dep["repo_url"],
            platform=dep["platform"],
            stage=dep["stage"],
            status=dep["status"],
            progress=dep["progress"],
            deployment_url=dep.get("deployment_url"),
            frontend_url=dep.get("frontend_url"),
            backend_url=dep.get("backend_url"),
            error=dep.get("error"),
            diagnosis=diagnosis_obj,
            created_at=dep["created_at"],
            updated_at=dep["updated_at"],
            logs_count=len(dep.get("logs", []))
        )

    def get_logs(self, deployment_id: str) -> List[LogEntry]:
        dep = self._deployments.get(deployment_id)
        if not dep:
            return []
        return [LogEntry(**l) for l in dep.get("logs", [])]

    async def initiate_deployment(self, req: DeploymentRequest) -> str:
        """Initializes a new deployment job and launches the asynchronous pipeline."""
        deployment_id = str(uuid.uuid4())
        now = self._get_timestamp()

        self._deployments[deployment_id] = {
            "deployment_id": deployment_id,
            "repo_url": req.repo_url,
            "platform": req.platform,
            "branch": req.branch or "main",
            "build_command": req.build_command,
            "start_command": req.start_command,
            "environment_variables": req.environment_variables or {},
            "project_name": req.project_name,
            "custom_tokens": req.custom_tokens or {},
            "stage": "Preparing deployment",
            "status": "queued",
            "progress": 5,
            "logs": [],
            "deployment_url": None,
            "frontend_url": None,
            "backend_url": None,
            "error": None,
            "diagnosis": None,
            "retry_count": 0,
            "created_at": now,
            "updated_at": now
        }

        # Launch async execution loop
        task = asyncio.create_task(self._run_pipeline(deployment_id))
        self._tasks[deployment_id] = task

        return deployment_id

    async def retry_deployment(self, req: RetryRequest) -> DeploymentStatusResponse:
        """Applies user-approved changes and restarts the deployment pipeline safely."""
        dep = self._deployments.get(req.deployment_id)
        if not dep:
            raise ValueError("Deployment ID not found.")

        if dep.get("retry_count", 0) >= 3:
            raise ValueError("Maximum self-healing retry limit (3) reached to prevent uncontrolled loops.")

        # Apply approved modifications
        changes = req.approved_changes
        if "build_command" in changes:
            dep["build_command"] = changes["build_command"]
            self._add_log(req.deployment_id, "Retry Approval", "info", f"User approved new build command: {dep['build_command']}")

        if "start_command" in changes:
            dep["start_command"] = changes["start_command"]
            self._add_log(req.deployment_id, "Retry Approval", "info", f"User approved new start command: {dep['start_command']}")

        if "environment_variables" in changes and isinstance(changes["environment_variables"], dict):
            dep["environment_variables"].update(changes["environment_variables"])
            self._add_log(req.deployment_id, "Retry Approval", "info", f"User approved environment variable updates.")

        dep["retry_count"] += 1
        dep["status"] = "queued"
        dep["stage"] = "Preparing deployment (Retry)"
        dep["progress"] = 10
        dep["error"] = None
        dep["diagnosis"] = None

        task = asyncio.create_task(self._run_pipeline(req.deployment_id))
        self._tasks[req.deployment_id] = task

        return self.get_status_response(req.deployment_id)

    async def _run_pipeline(self, deployment_id: str):
        dep = self._deployments[deployment_id]
        stage = "Preparing deployment"

        try:
            dep["status"] = "in_progress"
            dep["stage"] = stage
            dep["progress"] = 15
            self._add_log(deployment_id, stage, "info", f"Starting deployment pipeline for {dep['repo_url']}")

            # 1. Safety check
            if not AIAgentService.validate_command_safety(dep.get("build_command")):
                raise ValueError(f"Build command failed security validation: {dep.get('build_command')}")
            if not AIAgentService.validate_command_safety(dep.get("start_command")):
                raise ValueError(f"Start command failed security validation: {dep.get('start_command')}")

            self._add_log(deployment_id, stage, "success", "Security check passed: Safe commands verified against allowlist.")

            # 2. Inspect GitHub repository
            gh_token = dep["custom_tokens"].get("github") or settings.GITHUB_TOKEN
            gh_service = GitHubService(token=gh_token)
            self._add_log(deployment_id, stage, "info", "Fetching repository manifest from GitHub...")
            repo_data = await gh_service.inspect_repository(dep["repo_url"])
            analysis = AnalyzerService.analyze_repository_data(repo_data)
            self._add_log(deployment_id, stage, "info", f"Repository analyzed: {analysis.framework} ({analysis.language})")

            # 3. Select Provider
            platform_target = dep["platform"].lower()
            if platform_target == "auto":
                platform_target = "vercel" if analysis.project_type in ("frontend", "static", "full_stack") else "render"

            # Determine provider instance
            provider_instance = None
            if platform_target == "vercel":
                v_token = dep["custom_tokens"].get("vercel") or settings.VERCEL_TOKEN
                provider_instance = VercelProvider(token=v_token)
                active_stage = "Deploying frontend"
            elif platform_target == "render":
                r_token = dep["custom_tokens"].get("render") or settings.RENDER_API_KEY
                provider_instance = RenderProvider(token=r_token)
                active_stage = "Deploying backend"
            else:
                raise ValueError(f"Unsupported deployment platform target: {platform_target}")

            dep["stage"] = active_stage
            dep["progress"] = 35
            self._add_log(deployment_id, active_stage, "info", f"Authenticating with {provider_instance.get_provider_name()} API...")

            # Validate provider credentials
            await provider_instance.prepare(repo_data, {})
            self._add_log(deployment_id, active_stage, "success", f"Authenticated successfully with {provider_instance.get_provider_name()}")

            # 4. Trigger Deployment
            dep["progress"] = 50
            self._add_log(deployment_id, active_stage, "info", f"Dispatching deployment request with build command: '{dep['build_command'] or 'default'}'...")

            deploy_result = await provider_instance.deploy(
                repo_info=repo_data,
                build_command=dep["build_command"],
                start_command=dep["start_command"],
                environment_variables=dep["environment_variables"],
                project_name=dep["project_name"]
            )

            external_id = deploy_result.get("external_id")
            preview_url = deploy_result.get("url")
            self._add_log(deployment_id, active_stage, "info", f"Deployment registered on {provider_instance.get_provider_name()} (ID: {external_id})")

            # 5. Monitor and check deployment
            dep["stage"] = "Checking deployment"
            dep["progress"] = 70
            self._add_log(deployment_id, "Checking deployment", "info", "Monitoring live build logs and provisioning status...")

            # Polling loop
            max_checks = 25
            final_status = "BUILDING"
            final_url = preview_url

            for check_idx in range(max_checks):
                await asyncio.sleep(4)
                status_info = await provider_instance.get_status(external_id)
                current_state = status_info.get("status", "").upper()
                if status_info.get("url"):
                    final_url = status_info["url"]

                if current_state in ("READY", "LIVE"):
                    final_status = "READY"
                    break
                elif current_state in ("ERROR", "CANCELED", "BUILD_FAILED"):
                    final_status = "ERROR"
                    err_detail = status_info.get("error") or "Provider reported build/deployment failure."
                    raise RuntimeError(err_detail)
                else:
                    self._add_log(deployment_id, "Checking deployment", "info", f"Deployment state: {current_state} (check {check_idx+1}/{max_checks})")

            # 6. Complete
            dep["stage"] = "Deployment complete"
            dep["status"] = "ready"
            dep["progress"] = 100
            dep["deployment_url"] = final_url
            if platform_target == "vercel":
                dep["frontend_url"] = final_url
            else:
                dep["backend_url"] = final_url

            self._add_log(deployment_id, "Deployment complete", "success", f"Deployment live and reachable at: {final_url}")

        except Exception as exc:
            error_message = str(exc)
            dep["stage"] = "Failed"
            dep["status"] = "failed"
            dep["progress"] = 100
            dep["error"] = error_message
            self._add_log(deployment_id, "Failed", "error", f"Deployment aborted: {error_message}")

            # AI Diagnosis
            try:
                self._add_log(deployment_id, "Failed", "info", "Invoking AI Diagnosis Agent to analyze failure cause...")
                diagnosis = await AIAgentService.diagnose_error(
                    error_message, 
                    {"platform": dep["platform"], "repo_url": dep["repo_url"]}
                )
                dep["diagnosis"] = diagnosis.model_dump()
                self._add_log(deployment_id, "Failed", "warn", f"AI Diagnosis: {diagnosis.root_cause}. Recommendation: {diagnosis.suggested_fix}")
            except Exception as diag_err:
                self._add_log(deployment_id, "Failed", "warn", f"AI Diagnosis failed: {str(diag_err)}")

deployment_manager = DeploymentManager()
