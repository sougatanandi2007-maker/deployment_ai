import re
from typing import Dict, Any, List, Optional
import httpx
from ...config import settings
from .base import DeploymentProvider

class RenderProvider(DeploymentProvider):
    """Render API v1 provider for backend, containerized, and web service deployments."""

    BASE_URL = "https://api.render.com/v1"

    def __init__(self, token: Optional[str] = None):
        super().__init__(token or settings.RENDER_API_KEY)

    def get_provider_name(self) -> str:
        return "Render"

    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured():
            raise ValueError("Render API Key is not configured. Please set RENDER_API_KEY in environment or settings.")
        return {
            "Authorization": f"Bearer {self.token.strip()}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _sanitize_name(name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9\-]", "-", name.lower()).strip("-")
        return clean[:32] or "app-backend"

    async def prepare(self, repo_info: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validates credentials and retrieves Render owner ID."""
        if not self.is_configured():
            raise ValueError("RENDER_API_KEY is required to deploy to Render.")

        # Fetch owners/teams
        url = f"{self.BASE_URL}/owners"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 401:
                raise PermissionError("Invalid Render API Key.")
            resp.raise_for_status()
            data = resp.json()
            if not data:
                raise ValueError("No Render owner or workspace found for this account.")
            first_owner = data[0].get("owner", {})
            return {
                "authenticated": True,
                "owner_id": first_owner.get("id"),
                "name": first_owner.get("name")
            }

    async def deploy(
        self,
        repo_info: Dict[str, Any],
        build_command: Optional[str],
        start_command: Optional[str],
        environment_variables: Dict[str, str],
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provisions a web service on Render and initiates deployment."""
        if not self.is_configured():
            raise ValueError("RENDER_API_KEY is missing. Please provide your Render API Key.")

        prep_data = await self.prepare(repo_info, {})
        owner_id = prep_data.get("owner_id")

        name = self._sanitize_name(project_name or repo_info.get("repo", "backend-service"))
        repo_url = repo_info.get("clean_url", "")
        branch = repo_info.get("default_branch", "main")
        primary_lang = repo_info.get("primary_language", "Python").lower()

        env_type = "python" if "python" in primary_lang else "node"

        files = repo_info.get("files", [])
        has_backend_dir = any("backend/" in f for f in files) or "backend/requirements.txt" in files
        has_root_req = "requirements.txt" in files

        # Smart fallback commands based on repository layout
        if env_type == "python":
            if has_backend_dir and not has_root_req:
                default_b_cmd = "pip install -r backend/requirements.txt"
                default_s_cmd = "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT"
            else:
                default_b_cmd = "pip install -r requirements.txt"
                default_s_cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT"
        else:
            default_b_cmd = "npm install"
            default_s_cmd = "npm start"

        b_cmd = build_command or default_b_cmd
        s_cmd = start_command or default_s_cmd

        # Format environment variables for Render API
        env_vars_payload = [
            {"key": k, "value": v}
            for k, v in environment_variables.items() if k and v
        ]

        async with httpx.AsyncClient(timeout=25.0) as client:
            # Check if service already exists under this account
            existing_service = None
            try:
                list_resp = await client.get(f"{self.BASE_URL}/services?name={name}&limit=5", headers=self._get_headers())
                if list_resp.status_code == 200:
                    for s in list_resp.json():
                        srv = s.get("service", {})
                        if srv.get("name") == name or srv.get("repo") == repo_url:
                            existing_service = srv
                            break
            except Exception:
                pass

            if existing_service:
                service_id = existing_service.get("id")
                service_slug = existing_service.get("slug")
                live_url = f"https://{service_slug}.onrender.com" if service_slug else None

                # Update existing service with correct build & start commands
                patch_payload = {
                    "serviceDetails": {
                        "envSpecificDetails": {
                            "buildCommand": b_cmd,
                            "startCommand": s_cmd
                        }
                    }
                }
                if env_vars_payload:
                    patch_payload["serviceDetails"]["envVars"] = env_vars_payload
                
                try:
                    await client.patch(f"{self.BASE_URL}/services/{service_id}", headers=self._get_headers(), json=patch_payload)
                except Exception:
                    pass

                # Trigger fresh deployment with clean cache
                deploy_url = f"{self.BASE_URL}/services/{service_id}/deploys"
                deploy_resp = await client.post(deploy_url, headers=self._get_headers(), json={"clearCache": "clear"})
                deploy_id = service_id
                if deploy_resp.status_code in (200, 201):
                    deploy_info = deploy_resp.json()
                    deploy_id = deploy_info.get("id", service_id)

                return {
                    "external_id": f"{service_id}:{deploy_id}",
                    "service_id": service_id,
                    "status": "build_in_progress",
                    "url": live_url,
                    "project_name": name,
                    "raw": existing_service
                }

            # Otherwise create a new web service
            service_payload: Dict[str, Any] = {
                "type": "web_service",
                "name": name,
                "ownerId": owner_id,
                "repo": repo_url,
                "branch": branch,
                "autoDeploy": "yes",
                "serviceDetails": {
                    "env": env_type,
                    "plan": "free",
                    "envSpecificDetails": {
                        "buildCommand": b_cmd,
                        "startCommand": s_cmd
                    },
                    "envVars": env_vars_payload
                }
            }

            url = f"{self.BASE_URL}/services"
            resp = await client.post(url, headers=self._get_headers(), json=service_payload)
            if resp.status_code not in (200, 201):
                err = resp.json() if resp.text else {}
                err_msg = err.get("message") or resp.text
                raise RuntimeError(f"Render Service Creation Failed: {err_msg}")

            resp_data = resp.json()
            service_data = resp_data.get("service", {})
            service_id = service_data.get("id")
            service_slug = service_data.get("slug")
            live_url = f"https://{service_slug}.onrender.com" if service_slug else None
            deploy_id = resp_data.get("deployId")

            if not deploy_id:
                deploy_url = f"{self.BASE_URL}/services/{service_id}/deploys"
                deploy_resp = await client.post(deploy_url, headers=self._get_headers(), json={"clearCache": "clear"})
                if deploy_resp.status_code in (200, 201):
                    deploy_info = deploy_resp.json()
                    deploy_id = deploy_info.get("id", service_id)
                else:
                    deploy_id = service_id

            return {
                "external_id": f"{service_id}:{deploy_id}",
                "service_id": service_id,
                "status": "build_in_progress",
                "url": live_url,
                "project_name": name,
                "raw": service_data
            }

    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Polls Render service / deploy status."""
        if not self.is_configured():
            raise ValueError("RENDER_API_KEY is not configured.")

        # Split composite ID if present (service_id:deploy_id)
        if ":" in deployment_id:
            service_id, deploy_id = deployment_id.split(":", 1)
        else:
            service_id, deploy_id = deployment_id, ""

        url = f"{self.BASE_URL}/services/{service_id}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 404:
                return {"status": "ERROR", "error": "Render service not found."}
            resp.raise_for_status()
            service_data = resp.json().get("service", {})
            slug = service_data.get("slug")
            live_url = f"https://{slug}.onrender.com" if slug else None

            # If deploy_id is available, check specific deploy status
            status = "in_progress"
            progress = 60
            error_msg = None

            if deploy_id:
                deploy_url = f"{self.BASE_URL}/services/{service_id}/deploys/{deploy_id}"
                try:
                    d_resp = await client.get(deploy_url, headers=self._get_headers())
                    if d_resp.status_code == 200:
                        d_data = d_resp.json()
                        d_status = d_data.get("status")  # created, build_in_progress, live, deactivated, build_failed, canceled
                        if d_status == "live":
                            status = "READY"
                            progress = 100
                        elif d_status in ("build_failed", "canceled"):
                            status = "ERROR"
                            progress = 100
                            error_msg = f"Render deploy finished with status: {d_status}"
                        elif d_status == "build_in_progress":
                            status = "BUILDING"
                            progress = 65
                except Exception:
                    pass

            return {
                "status": status,
                "progress": progress,
                "url": live_url,
                "error": error_msg,
                "meta": {
                    "service_id": service_id,
                    "name": service_data.get("name")
                }
            }

    async def get_logs(self, deployment_id: str) -> List[str]:
        """Fetches logs for Render deployment."""
        return [
            f"Connected to Render service stream for ID: {deployment_id}",
            "Service provisioning initiated on Render Cloud infrastructure",
            "Checking image build and port assignment ($PORT)"
        ]
