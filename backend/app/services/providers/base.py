from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class DeploymentProvider(ABC):
    """Abstract base class for all deployment providers (Vercel, Render, future Browser/Playwright)."""

    def __init__(self, token: Optional[str] = None):
        self.token = token

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the human-readable identifier of the provider."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Checks if required API credentials exist."""
        pass

    @abstractmethod
    async def prepare(self, repo_info: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validates prerequisites, project settings, and target availability."""
        pass

    @abstractmethod
    async def deploy(
        self,
        repo_info: Dict[str, Any],
        build_command: Optional[str],
        start_command: Optional[str],
        environment_variables: Dict[str, str],
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initiates the deployment via API. Returns external deployment ID, initial status, and preview URL."""
        pass

    @abstractmethod
    async def get_status(self, deployment_id: str) -> Dict[str, Any]:
        """Fetches the current status (e.g. BUILDING, READY, ERROR), progress, and final live URL."""
        pass

    @abstractmethod
    async def get_logs(self, deployment_id: str) -> List[str]:
        """Fetches raw build/runtime logs from the provider API."""
        pass
