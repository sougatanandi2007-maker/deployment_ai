from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="Public GitHub repository URL")
    project_description: Optional[str] = Field(None, description="Optional user-provided project description")
    target_platform: Optional[str] = Field(None, description="Optional user target preference (e.g. vercel, render)")

class ReadinessCheckItem(BaseModel):
    name: str
    status: str  # "pass" | "warn" | "fail" | "info"
    message: str

class ReadinessReport(BaseModel):
    score: int  # 0 to 100
    grade: str  # "A" | "B" | "C" | "F"
    checks: List[ReadinessCheckItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class IaCFile(BaseModel):
    filename: str
    content: str
    description: str
    language: str  # "yaml" | "dockerfile" | "json"

class IaCConfigResponse(BaseModel):
    success: bool
    platform: str
    files: List[IaCFile] = Field(default_factory=list)

class GenerateIaCRequest(BaseModel):
    repo_url: str
    platform: str = "vercel"
    build_command: Optional[str] = None
    start_command: Optional[str] = None
    environment_variables: Optional[List[str]] = Field(default_factory=list)

class DeploymentSummary(BaseModel):
    deployment_id: str
    repo_url: str
    platform: str
    stage: str
    status: str
    progress: int
    deployment_url: Optional[str] = None
    created_at: str
    updated_at: str
    logs_count: int = 0

class ProjectAnalysis(BaseModel):
    repo_name: str
    repo_owner: str
    repo_url: str
    default_branch: str = "main"
    language: str
    framework: str
    project_type: str  # "frontend" | "backend" | "full_stack" | "static"
    frontend: Optional[str] = None
    backend: Optional[str] = None
    package_manager: Optional[str] = None
    has_package_json: bool = False
    has_requirements_txt: bool = False
    has_pyproject_toml: bool = False
    has_dockerfile: bool = False
    has_vercel_json: bool = False
    has_render_yaml: bool = False
    detected_files: List[str] = Field(default_factory=list)
    detected_env_vars: List[str] = Field(default_factory=list)
    readme_snippet: Optional[str] = None
    readiness_report: Optional[ReadinessReport] = None

class DeploymentPlan(BaseModel):
    project_type: str
    frontend: Optional[str] = None
    backend: Optional[str] = None
    frontend_platform: Optional[str] = None
    backend_platform: Optional[str] = None
    build_command: Optional[str] = None
    start_command: Optional[str] = None
    environment_variables: List[str] = Field(default_factory=list)
    deployment_plan: List[str] = Field(default_factory=list)
    intent_explanation: str
    is_safe_command: bool = True

class AnalyzeResponse(BaseModel):
    success: bool
    analysis: Optional[ProjectAnalysis] = None
    plan: Optional[DeploymentPlan] = None
    error: Optional[str] = None

class DeploymentRequest(BaseModel):
    repo_url: str
    platform: str = "vercel"  # "vercel" | "render" | "auto"
    branch: Optional[str] = "main"
    build_command: Optional[str] = None
    start_command: Optional[str] = None
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict)
    project_name: Optional[str] = None
    user_confirmed: bool = True
    custom_tokens: Optional[Dict[str, str]] = Field(default_factory=dict)

class LogEntry(BaseModel):
    timestamp: str
    stage: str
    level: str  # "info" | "warn" | "error" | "success"
    message: str

class ErrorDiagnosis(BaseModel):
    error_summary: str
    root_cause: str
    explanation: str
    suggested_fix: str
    recommended_changes: Dict[str, Any] = Field(default_factory=dict)
    retry_allowed: bool = True

class DeploymentStatusResponse(BaseModel):
    deployment_id: str
    repo_url: str
    platform: str
    stage: str
    status: str  # "queued" | "in_progress" | "ready" | "failed"
    progress: int  # 0 to 100
    deployment_url: Optional[str] = None
    frontend_url: Optional[str] = None
    backend_url: Optional[str] = None
    error: Optional[str] = None
    diagnosis: Optional[ErrorDiagnosis] = None
    created_at: str
    updated_at: str
    logs_count: int = 0

class RetryRequest(BaseModel):
    deployment_id: str
    approved_changes: Dict[str, Any] = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    version: str
    providers: Dict[str, bool]
