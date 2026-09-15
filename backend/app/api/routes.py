from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DeploymentRequest,
    DeploymentStatusResponse,
    LogEntry,
    RetryRequest,
    HealthResponse,
    GenerateIaCRequest,
    IaCConfigResponse,
    DeploymentSummary
)
from ..config import settings
from ..services.github_service import GitHubService
from ..services.analyzer_service import AnalyzerService
from ..services.agent_service import AIAgentService
from ..services.deployment_manager import deployment_manager

router = APIRouter(prefix="/api")

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint indicating API operational status and configured providers."""
    return HealthResponse(
        status="healthy",
        version="1.0.0-prototype",
        providers=settings.get_configured_providers()
    )

@router.get("/config/providers")
async def get_providers_status():
    """Returns provider credentials status without exposing actual secrets."""
    return settings.get_configured_providers()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(req: AnalyzeRequest):
    """Analyzes a public GitHub repository and produces an AI-powered deployment plan."""
    try:
        gh_service = GitHubService()
        repo_data = await gh_service.inspect_repository(req.repo_url)
        
        # Analyze project structure and frameworks
        analysis = AnalyzerService.analyze_repository_data(repo_data)
        
        # Generate AI Deployment Plan
        plan = await AIAgentService.generate_deployment_plan(
            analysis=analysis,
            user_description=req.project_description,
            preferred_target=req.target_platform
        )

        return AnalyzeResponse(
            success=True,
            analysis=analysis,
            plan=plan
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=429, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/deploy")
async def deploy_repository(req: DeploymentRequest):
    """Initiates an automated deployment workflow after user confirmation."""
    if not req.user_confirmed:
        raise HTTPException(status_code=400, detail="Deployment confirmation required.")

    # Validate command safety
    if req.build_command and not AIAgentService.validate_command_safety(req.build_command):
        raise HTTPException(status_code=400, detail="Disallowed or unsafe build command provided.")
    if req.start_command and not AIAgentService.validate_command_safety(req.start_command):
        raise HTTPException(status_code=400, detail="Disallowed or unsafe start command provided.")

    try:
        deployment_id = await deployment_manager.initiate_deployment(req)
        return {
            "success": True,
            "deployment_id": deployment_id,
            "message": "Deployment queued successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate deployment: {str(e)}")

@router.get("/deploy/{deployment_id}", response_model=DeploymentStatusResponse)
async def get_deployment_status(deployment_id: str):
    """Retrieves current deployment stage, progress, status, and live URLs."""
    status = deployment_manager.get_status_response(deployment_id)
    if not status:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    return status

@router.get("/deploy/{deployment_id}/logs", response_model=List[LogEntry])
async def get_deployment_logs(deployment_id: str):
    """Fetches real-time log entries for the specified deployment."""
    dep = deployment_manager.get_deployment(deployment_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    return deployment_manager.get_logs(deployment_id)

@router.post("/deploy/{deployment_id}/retry", response_model=DeploymentStatusResponse)
async def retry_deployment(deployment_id: str, payload: Dict[str, Any]):
    """Retries a failed deployment with user-approved remedial changes."""
    try:
        req = RetryRequest(
            deployment_id=deployment_id,
            approved_changes=payload.get("approved_changes", {})
        )
        return await deployment_manager.retry_deployment(req)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")

@router.post("/deploy/{deployment_id}/diagnose")
async def manual_diagnose(deployment_id: str):
    """Manually triggers AI error diagnosis on a deployment."""
    dep = deployment_manager.get_deployment(deployment_id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found.")
    if not dep.get("error"):
        raise HTTPException(status_code=400, detail="No error logged for this deployment.")

    diagnosis = await AIAgentService.diagnose_error(
        dep["error"],
        {"platform": dep["platform"], "repo_url": dep["repo_url"]}
    )
    dep["diagnosis"] = diagnosis.model_dump()
    return diagnosis

@router.get("/deployments", response_model=List[DeploymentSummary])
async def list_deployments():
    """Returns past deployment runs and their current operational status."""
    return deployment_manager.get_all_deployments_summary()

@router.post("/generate-iac", response_model=IaCConfigResponse)
async def generate_iac(req: GenerateIaCRequest):
    """Generates production-grade GitHub Actions CI/CD workflow, Dockerfile, and cloud manifests."""
    try:
        gh_service = GitHubService()
        repo_data = await gh_service.inspect_repository(req.repo_url)
        analysis = AnalyzerService.analyze_repository_data(repo_data)
        
        files = AnalyzerService.generate_iac_files(
            analysis=analysis,
            preferred_target=req.platform,
            build_command=req.build_command,
            start_command=req.start_command,
            env_vars=req.environment_variables
        )
        return IaCConfigResponse(
            success=True,
            platform=req.platform,
            files=files
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate IaC files: {str(e)}")

