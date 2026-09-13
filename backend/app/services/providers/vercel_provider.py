import re
from typing import Dict, Any, List, Optional
import httpx
from ...config import settings
from .base import DeploymentProvider

class VercelProvider(DeploymentProvider):
    """Official Vercel REST API integration for automated deployments."""

    BASE_URL = "https://api.vercel.com"

    def __init__(self, token: Optional[str] = None):
        super().__init__(token or settings.VERCEL_TOKEN)

    def get_provider_name(self) -> str:
        return "Vercel"

    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured():
            raise ValueError("Vercel API Token is not configured. Please set VERCEL_TOKEN in environment or settings.")
        return {
            "Authorization": f"Bearer {self.token.strip()}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitizes project name to comply with Vercel naming restrictions (a-z, 0-9, -)."""
        clean = re.sub(r"[^a-zA-Z0-9\-]", "-", name.lower()).strip("-")
        return clean[:52] or "app-deployment"

    async def prepare(self, repo_info: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validates token authenticity with Vercel API and checks project compatibility."""
        if not self.is_configured():
            raise ValueError("VERCEL_TOKEN is required to deploy to Vercel.")

        # Test token validity by querying current user
        url = f"{self.BASE_URL}/v2/user"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 401:
                raise PermissionError("Invalid Vercel API token. Please check your credentials.")
            resp.raise_for_status()
            user_data = resp.json().get("user", {})
            return {
                "authenticated": True,
                "username": user_data.get("username", "Unknown"),
                "email": user_data.get("email")
            }

    async def deploy(
        self,
        repo_info: Dict[str, Any],
        build_command: Optional[str],
        start_command: Optional[str],
        environment_variables: Dict[str, str],
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a deployment on Vercel via official REST API v13."""
        if not self.is_configured():
            raise ValueError("VERCEL_TOKEN is missing. Please provide your Vercel Token to deploy.")

        name = self._sanitize_name(project_name or repo_info.get("repo", "ai-deployed-app"))
        owner = repo_info.get("owner", "")
        repo = repo_info.get("repo", "")
        branch = repo_info.get("default_branch", "main")

        # Detect root directory and framework
        files = repo_info.get("files", [])
        root_dir = None
        if "frontend/package.json" in files or "frontend/package.json" in repo_info.get("file_contents", {}):
            root_dir = "frontend"
        elif "client/package.json" in files or "client/package.json" in repo_info.get("file_contents", {}):
            root_dir = "client"

        files_str = str(files).lower()
        framework_slug = None
        if "next" in files_str:
            framework_slug = "nextjs"
        elif "vite" in files_str:
            framework_slug = "vite"
        elif "nuxt" in files_str:
            framework_slug = "nuxtjs"
        elif "svelte" in files_str:
            framework_slug = "sveltekit"
        elif "create-react-app" in files_str or "react-scripts" in files_str:
            framework_slug = "create-react-app"

        # Normalize build command when rootDirectory is set
        effective_build_cmd = build_command
        if root_dir and build_command and f"--prefix {root_dir}" in build_command:
            effective_build_cmd = "npm run build"

        # Step 1: Ensure project exists or create it
        project_url = f"{self.BASE_URL}/v10/projects/{name}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=20.0) as client:
            proj_resp = await client.get(project_url, headers=headers)
            
            if proj_resp.status_code == 404:
                # Create project
                create_proj_url = f"{self.BASE_URL}/v10/projects"
                proj_payload: Dict[str, Any] = {
                    "name": name,
                    "framework": framework_slug,
                }
                if root_dir:
                    proj_payload["rootDirectory"] = root_dir
                if effective_build_cmd:
                    proj_payload["buildCommand"] = effective_build_cmd

                create_resp = await client.post(create_proj_url, headers=headers, json=proj_payload)
                if create_resp.status_code not in (200, 201):
                    error_data = create_resp.json() if create_resp.text else {}
                    err_msg = error_data.get("error", {}).get("message") or create_resp.text
                    raise RuntimeError(f"Vercel Project Creation Failed: {err_msg}")
            elif proj_resp.status_code == 200 and (root_dir or framework_slug or build_command):
                # Ensure existing project has correct settings
                patch_payload = {}
                if root_dir:
                    patch_payload["rootDirectory"] = root_dir
                if framework_slug:
                    patch_payload["framework"] = framework_slug
                if build_command:
                    patch_payload["buildCommand"] = build_command
                try:
                    await client.patch(project_url, headers=headers, json=patch_payload)
                except Exception:
                    pass

            # Step 2: Add environment variables if provided
            if environment_variables:
                env_url = f"{self.BASE_URL}/v10/projects/{name}/env"
                for k, v in environment_variables.items():
                    if k and v:
                        env_payload = {
                            "key": k,
                            "value": v,
                            "type": "plain",
                            "target": ["production", "preview", "development"]
                        }
                        try:
                            await client.post(env_url, headers=headers, json=env_payload)
                        except Exception:
                            pass  # Continue even if variable already exists

            # Step 3: Trigger deployment via v13 deployments API
            deploy_url = f"{self.BASE_URL}/v13/deployments"
            repo_id = repo_info.get("repo_id")

            deploy_payload: Dict[str, Any] = {
                "name": name,
                "project": name,
                "target": "production",
            }

            if repo_id:
                deploy_payload["gitSource"] = {
                    "type": "github",
                    "repo": f"{owner}/{repo}",
                    "repoId": str(repo_id),
                    "ref": branch
                }
            elif repo_info.get("file_contents"):
                # Fallback to direct file tree deployment if repoId is unavailable
                deploy_payload["files"] = [
                    {"file": p, "data": content}
                    for p, content in repo_info["file_contents"].items() if content
                ]
            else:
                deploy_payload["gitSource"] = {
                    "type": "github",
                    "repo": f"{owner}/{repo}",
                    "ref": branch
                }

            proj_settings = {}
            if effective_build_cmd:
                proj_settings["buildCommand"] = effective_build_cmd
            if root_dir:
                proj_settings["rootDirectory"] = root_dir
            if framework_slug:
                proj_settings["framework"] = framework_slug
            if proj_settings:
                deploy_payload["projectSettings"] = proj_settings

            deploy_resp = await client.post(deploy_url, headers=headers, json=deploy_payload)
            if deploy_resp.status_code not in (200, 201):
                err_data = deploy_resp.json() if deploy_resp.text else {}
                err_msg = err_data.get("error", {}).get("message") or deploy_resp.text
                
                # If gitSource failed due to GitHub app permissions, retry with direct files
                if repo_info.get("file_contents") and ("git" in err_msg.lower() or "not connected" in err_msg.lower() or "repoid" in err_msg.lower()):
                    file_payload = {
                        "name": name,
                        "project": name,
                        "target": "production",
                        "files": [
                            {"file": p, "data": content}
                            for p, content in repo_info["file_contents"].items() if content
                        ]
                    }
                    if effective_build_cmd:
                        file_payload["projectSettings"] = {"buildCommand": effective_build_cmd}
                    file_resp = await client.post(deploy_url, headers=headers, json=file_payload)
                    if file_resp.status_code in (200, 201):
                        deploy_resp = file_resp
                    else:
                        raise RuntimeError(f"Vercel Deployment Failed: {err_msg}")
                else:
                    raise RuntimeError(f"Vercel Deployment Failed: {err_msg}")

            data = deploy_resp.json()
            external_id = data.get("id")
            preview_url = f"https://{data.get('url')}" if data.get("url") else None
            initial_status = data.get("readyState", "INITIALIZING")

            return {
                "external_id": external_id,
                "status": initial_status,
                "url": preview_url,
                "project_name": name,
                "raw": data
            }

    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Queries status of an existing Vercel deployment."""
        if not self.is_configured():
            raise ValueError("VERCEL_TOKEN is not configured.")

        url = f"{self.BASE_URL}/v13/deployments/{deployment_id}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                return {"status": "ERROR", "error": "Deployment not found on Vercel"}
            resp.raise_for_status()
            data = resp.json()

            ready_state = data.get("readyState", "QUEUED")  # INITIALIZING, ANALYZING, BUILDING, READY, ERROR, CANCELED
            url_domain = data.get("url")
            live_url = f"https://{url_domain}" if url_domain else None

            error_msg = None
            if ready_state in ("ERROR", "CANCELED"):
                error_info = data.get("error") or {}
                error_msg = error_info.get("message") or "Vercel build or execution failed."

            progress_map = {
                "INITIALIZING": 20,
                "ANALYZING": 35,
                "BUILDING": 60,
                "DEPLOYING": 85,
                "READY": 100,
                "ERROR": 100,
                "CANCELED": 100
            }

            return {
                "status": ready_state,
                "progress": progress_map.get(ready_state, 50),
                "url": live_url,
                "error": error_msg,
                "meta": {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "created": data.get("createdAt")
                }
            }

    async def get_logs(self, deployment_id: str) -> List[str]:
        """Fetches deployment build and runtime events/logs from Vercel API."""
        if not self.is_configured():
            return ["Vercel token not configured. Unable to fetch remote logs."]

        url = f"{self.BASE_URL}/v3/deployments/{deployment_id}/events"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    events = resp.json()
                    logs = []
                    for ev in events:
                        text = ev.get("text") or ev.get("payload", {}).get("text") or ""
                        if text:
                            logs.append(text.strip())
                    return logs
        except Exception as e:
            return [f"Log retrieval notice: {str(e)}"]

        return []
