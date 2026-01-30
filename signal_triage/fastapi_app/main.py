"""
FastAPI Application Main Module.

REST API for Signal Triage document analysis with:
- POST /analyze: Trigger document analysis (async)
- GET /jobs/{job_id}: Check job status
- GET /analyses/{analysis_id}: Get analysis results
- POST /webhook/test: Test webhook delivery
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field

from signal_triage.config import get_config
from signal_triage.database import (
    init_db,
    session_scope,
    Document,
    Analysis,
    AnalysisJob,
    JobStatus,
    APIAuditLog,
)
from signal_triage.fastapi_app.health import router as health_router
from signal_triage.adversarial_forensics import perform_adversarial_forensics
from signal_triage.stress_test import run_priming_stress_test


logger = logging.getLogger(__name__)


# Pydantic Models for API

class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze."""
    
    document_url: Optional[HttpUrl] = Field(None, description="URL to document (alternative to file upload)")
    ticker: Optional[str] = Field(None, description="Company ticker symbol")
    cik: Optional[str] = Field(None, description="Company CIK")
    analysis_type: str = Field("full", description="Analysis type: 'full', 'quick', 'forensic'")
    webhook_url: Optional[HttpUrl] = Field(None, description="Webhook URL for async notification")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for authentication")
    
    # Advanced options
    industry: Optional[str] = Field(None, description="Industry filter for benchmarking")
    geography: Optional[str] = Field(None, description="Geography filter for benchmarking")
    require_audit_gate: bool = Field(False, description="Require auditor to pass before publishing")
    include_tornado: bool = Field(True, description="Include tornado sensitivity analysis")
    
    # Forensic analysis parameters
    covenant_params: Optional[dict] = Field(None, description="Covenant headroom parameters")
    ch11_params: Optional[dict] = Field(None, description="Chapter 11 feasibility parameters")
    run_adversarial_forensics: bool = Field(False, description="Run adversarial forensics analysis (voting thresholds, exploitation vectors)")
    ica_document_url: Optional[HttpUrl] = Field(None, description="URL to Intercreditor Agreement for adversarial forensics gap analysis")
    run_priming_stress_test: bool = Field(False, description="Run priming stress test on recovery waterfall")
    priming_amount: Optional[float] = Field(None, description="Priming facility amount for stress test")


class JobResponse(BaseModel):
    """Response for job status queries."""
    
    job_id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    analysis_id: Optional[int] = None
    error_message: Optional[str] = None
    progress_pct: Optional[float] = Field(None, description="Estimated progress percentage (0-100)")
    current_stage: Optional[str] = Field(None, description="Current pipeline stage")


class AnalysisResponse(BaseModel):
    """Response for analysis results."""
    
    analysis_id: int
    document_id: int
    distress_score: Optional[float] = None
    credit_opinion: Optional[str] = None
    key_findings: Optional[dict] = None
    signals: Optional[dict] = None
    market_data_sources: Optional[list] = None
    pipeline_version: Optional[str] = None
    created_at: datetime
    execution_time_seconds: Optional[float] = None
    warnings: Optional[list[str]] = Field(None, description="Non-fatal warnings during analysis")


class HealthResponse(BaseModel):
    """Response for health check."""
    
    status: str
    version: str
    database: str
    available_providers: dict[str, bool]


class JobListResponse(BaseModel):
    """Response for job listing."""
    
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int


class MetricsResponse(BaseModel):
    """Response for metrics endpoint."""
    
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    running_jobs: int
    pending_jobs: int
    avg_execution_time_seconds: Optional[float] = None
    total_documents: int
    total_analyses: int


class AdversarialForensicsResponse(BaseModel):
    """Response for adversarial forensics analysis."""
    
    analysis_id: int
    overall_exploit_risk: str
    serta_incora_risk_score: int
    executive_summary: str
    amendment_provisions: list[dict]
    pro_rata_provisions: list[dict]
    guarantor_release_triggers: list[dict]
    intercreditor_gaps: list[dict]


class PrimingStressTestResponse(BaseModel):
    """Response for priming stress test."""
    
    analysis_id: int
    priming_facility_amount: float
    pre_priming: dict
    post_priming: dict
    fulcrum_migration: dict
    recovery_changes: list[dict]


# FastAPI Application Factory

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    config = get_config()
    
    app = FastAPI(
        title="Signal Triage API",
        description="Production-grade distressed debt analysis API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.fastapi.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include health check router
    app.include_router(health_router)
    
    # Initialize database on startup
    @app.on_event("startup")
    async def startup_event():
        init_db()
        logger.info("FastAPI application started")
    
    # Dependency: API Key Authentication
    async def verify_api_key(request: Request) -> bool:
        """Verify API key from request header."""
        if not config.fastapi.api_keys:
            # No API keys configured, allow all requests
            return True
        
        api_key = request.headers.get(config.fastapi.api_key_header)
        if not api_key or api_key not in config.fastapi.api_keys:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
        
        return True
    
    # Middleware: Request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all API requests to audit log."""
        request_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        response = await call_next(request)
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Log to database (async)
        try:
            with session_scope() as session:
                api_key = request.headers.get(config.fastapi.api_key_header, "")
                api_key_hash = hashlib.sha256(api_key.encode()).hexdigest() if api_key else None
                
                audit_log = APIAuditLog(
                    timestamp=start_time,
                    endpoint=str(request.url.path),
                    method=request.method,
                    request_id=request_id,
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    api_key_hash=api_key_hash,
                    response_status=response.status_code,
                    response_time_ms=response_time_ms,
                )
                session.add(audit_log)
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
        
        return response
    
    # Routes
    
    @app.get("/", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "available_providers": config.get_available_providers(),
        }
    
    @app.post("/analyze", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
    async def analyze_document(
        background_tasks: BackgroundTasks,
        request: AnalyzeRequest,
        file: Optional[UploadFile] = File(None)
    ):
        """
        Submit document for analysis (async).
        
        Accepts either file upload or document URL.
        Returns job_id for status tracking.
        """
        if not file and not request.document_url:
            raise HTTPException(status_code=400, detail="Either file or document_url required")
        
        job_id = str(uuid.uuid4())
        uploaded_file_content = None
        
        try:
            with session_scope() as session:
                # Create document record
                if file:
                    # File upload - read content for storage
                    content = await file.read()
                    file_hash = hashlib.sha256(content).hexdigest()
                    uploaded_file_content = content
                    
                    document = Document(
                        filename=file.filename,
                        file_hash=file_hash,
                        content_type=file.content_type,
                        file_size_bytes=len(content),
                        source_type="upload",
                        ticker=request.ticker,
                        cik=request.cik,
                    )
                else:
                    # URL ingestion
                    document = Document(
                        filename=str(request.document_url).split("/")[-1],
                        file_hash=hashlib.sha256(str(request.document_url).encode()).hexdigest(),
                        source_url=str(request.document_url),
                        source_type="url",
                        ticker=request.ticker,
                        cik=request.cik,
                    )
                
                session.add(document)
                session.flush()  # Get document.id
                
                # Store request parameters for potential retry
                request_params = {
                    "industry": request.industry,
                    "geography": request.geography,
                    "require_audit_gate": request.require_audit_gate,
                    "include_tornado": request.include_tornado,
                    "covenant_params": request.covenant_params,
                    "ch11_params": request.ch11_params,
                }
                
                # Create job record
                job = AnalysisJob(
                    job_id=job_id,
                    status=JobStatus.PENDING,
                    document_id=document.id,
                    analysis_type=request.analysis_type,
                    request_params=request_params,
                    webhook_url=str(request.webhook_url) if request.webhook_url else None,
                    webhook_secret=request.webhook_secret,
                )
                session.add(job)
                session.commit()
                
                # Schedule background task with all parameters
                background_tasks.add_task(
                    process_analysis_job,
                    job_id=job_id,
                    document_id=document.id,
                    analysis_type=request.analysis_type,
                    uploaded_file_content=uploaded_file_content,
                    uploaded_filename=file.filename if file else None,
                    industry=request.industry,
                    geography=request.geography,
                    require_audit_gate=request.require_audit_gate,
                    include_tornado=request.include_tornado,
                    covenant_params=request.covenant_params,
                    ch11_params=request.ch11_params,
                )
                
                return JobResponse(
                    job_id=job_id,
                    status=JobStatus.PENDING.value,
                    created_at=job.created_at,
                )
        
        except Exception as e:
            logger.error(f"Failed to create analysis job: {e}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    @app.get("/jobs/{job_id}", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
    async def get_job_status(job_id: str):
        """Get analysis job status."""
        with session_scope() as session:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return JobResponse(
                job_id=job.job_id,
                status=job.status.value,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                analysis_id=job.analysis_id,
                error_message=job.error_message,
            )
    
    @app.get("/analyses/{analysis_id}", response_model=AnalysisResponse, dependencies=[Depends(verify_api_key)])
    async def get_analysis(analysis_id: int):
        """Get analysis results."""
        with session_scope() as session:
            analysis = session.query(Analysis).filter_by(id=analysis_id).first()
            
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            # Extract warnings from key_findings if present
            warnings = None
            if analysis.key_findings and "warnings" in analysis.key_findings:
                warnings = analysis.key_findings["warnings"]
            
            return AnalysisResponse(
                analysis_id=analysis.id,
                document_id=analysis.document_id,
                distress_score=analysis.distress_score,
                credit_opinion=analysis.credit_opinion,
                key_findings=analysis.key_findings,
                signals=analysis.signals,
                market_data_sources=analysis.market_data_sources,
                pipeline_version=analysis.pipeline_version,
                created_at=analysis.created_at,
                execution_time_seconds=analysis.execution_time_seconds,
                warnings=warnings,
            )
    
    @app.get("/documents/{document_id}", dependencies=[Depends(verify_api_key)])
    async def get_document(document_id: int):
        """Get document metadata and analysis history."""
        with session_scope() as session:
            document = session.query(Document).filter_by(id=document_id).first()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get all analyses for this document
            analyses = session.query(Analysis).filter_by(document_id=document_id).all()
            
            return {
                "document_id": document.id,
                "filename": document.filename,
                "ticker": document.ticker,
                "cik": document.cik,
                "created_at": document.created_at,
                "analyses_count": len(analyses),
                "analyses": [
                    {
                        "analysis_id": a.id,
                        "distress_score": a.distress_score,
                        "created_at": a.created_at,
                    }
                    for a in analyses
                ],
            }
    
    @app.get("/jobs", response_model=JobListResponse, dependencies=[Depends(verify_api_key)])
    async def list_jobs(
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ):
        """
        List analysis jobs with optional filtering.
        
        Args:
            status: Filter by status (pending, running, completed, failed, cancelled)
            limit: Maximum number of results (default 50, max 100)
            offset: Offset for pagination
        """
        limit = min(limit, 100)  # Cap at 100
        
        with session_scope() as session:
            query = session.query(AnalysisJob)
            
            # Filter by status if provided
            if status:
                try:
                    status_enum = JobStatus(status)
                    query = query.filter(AnalysisJob.status == status_enum)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            jobs = query.order_by(AnalysisJob.created_at.desc()).limit(limit).offset(offset).all()
            
            return JobListResponse(
                jobs=[
                    JobResponse(
                        job_id=job.job_id,
                        status=job.status.value,
                        created_at=job.created_at,
                        started_at=job.started_at,
                        completed_at=job.completed_at,
                        analysis_id=job.analysis_id,
                        error_message=job.error_message,
                    )
                    for job in jobs
                ],
                total=total,
                page=offset // limit + 1,
                page_size=limit
            )
    
    @app.post("/jobs/{job_id}/cancel", dependencies=[Depends(verify_api_key)])
    async def cancel_job(job_id: str):
        """
        Cancel a pending or running job.
        
        Note: Jobs that are already running may not stop immediately.
        """
        with session_scope() as session:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel job with status: {job.status.value}"
                )
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.error_message = "Job cancelled by user"
            session.commit()
            
            return {"message": "Job cancelled successfully", "job_id": job_id}
    
    @app.post("/jobs/{job_id}/retry", dependencies=[Depends(verify_api_key)])
    async def retry_job(job_id: str, background_tasks: BackgroundTasks):
        """
        Retry a failed job.
        
        Creates a new job with the same parameters.
        """
        with session_scope() as session:
            old_job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            
            if not old_job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            if old_job.status != JobStatus.FAILED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only retry failed jobs (current status: {old_job.status.value})"
                )
            
            # Get document for retry
            document = session.query(Document).filter_by(id=old_job.document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Original document not found")
            
            # Create new job
            new_job_id = str(uuid.uuid4())
            new_job = AnalysisJob(
                job_id=new_job_id,
                status=JobStatus.PENDING,
                document_id=document.id,
                analysis_type=old_job.analysis_type,
                request_params=old_job.request_params,
                webhook_url=old_job.webhook_url,
                webhook_secret=old_job.webhook_secret,
            )
            session.add(new_job)
            session.commit()
            
            # Extract parameters from old job
            params = old_job.request_params or {}
            
            # Schedule retry
            background_tasks.add_task(
                process_analysis_job,
                job_id=new_job_id,
                document_id=document.id,
                analysis_type=old_job.analysis_type,
                uploaded_file_content=None,  # File no longer available
                uploaded_filename=None,
                industry=params.get("industry"),
                geography=params.get("geography"),
                require_audit_gate=params.get("require_audit_gate", False),
                include_tornado=params.get("include_tornado", True),
                covenant_params=params.get("covenant_params"),
                ch11_params=params.get("ch11_params"),
            )
            
            return {
                "message": "Job retry scheduled",
                "new_job_id": new_job_id,
                "original_job_id": job_id
            }
    
    @app.get("/metrics", response_model=MetricsResponse, dependencies=[Depends(verify_api_key)])
    async def get_metrics():
        """Get API usage metrics and statistics."""
        with session_scope() as session:
            # Job statistics
            total_jobs = session.query(AnalysisJob).count()
            completed_jobs = session.query(AnalysisJob).filter_by(status=JobStatus.COMPLETED).count()
            failed_jobs = session.query(AnalysisJob).filter_by(status=JobStatus.FAILED).count()
            running_jobs = session.query(AnalysisJob).filter_by(status=JobStatus.RUNNING).count()
            pending_jobs = session.query(AnalysisJob).filter_by(status=JobStatus.PENDING).count()
            
            # Average execution time from completed analyses
            from sqlalchemy import func
            avg_time = session.query(func.avg(Analysis.execution_time_seconds)).scalar()
            
            # Document and analysis counts
            total_documents = session.query(Document).count()
            total_analyses = session.query(Analysis).count()
            
            return MetricsResponse(
                total_jobs=total_jobs,
                completed_jobs=completed_jobs,
                failed_jobs=failed_jobs,
                running_jobs=running_jobs,
                pending_jobs=pending_jobs,
                avg_execution_time_seconds=float(avg_time) if avg_time else None,
                total_documents=total_documents,
                total_analyses=total_analyses,
            )
    
    @app.post("/analyses/{analysis_id}/adversarial-forensics", response_model=AdversarialForensicsResponse, dependencies=[Depends(verify_api_key)])
    async def run_adversarial_forensics_on_analysis(
        analysis_id: int,
        ica_document_url: Optional[HttpUrl] = None
    ):
        """
        Run adversarial forensics on a completed analysis.
        
        Performs deep-dive analysis of voting thresholds, amendment provisions,
        guarantor release triggers, and intercreditor agreement gaps to identify
        Serta/Incora/J.Crew exploitation vectors.
        """
        with session_scope() as session:
            # Get analysis and document
            analysis = session.query(Analysis).filter_by(id=analysis_id).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            document = session.query(Document).filter_by(id=analysis.document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get document text
            if document.source_url:
                # Fetch from URL
                from signal_triage.ingest.web import fetch_document_from_url
                from signal_triage.ingest.reader import full_text
                try:
                    chunks = fetch_document_from_url(document.source_url)
                    credit_agreement_text = full_text(chunks)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to fetch document: {e}")
            else:
                raise HTTPException(status_code=400, detail="Document source not available for forensics")
            
            # Get ICA text if provided
            ica_text = None
            if ica_document_url:
                try:
                    from signal_triage.ingest.web import fetch_document_from_url
                    from signal_triage.ingest.reader import full_text
                    ica_chunks = fetch_document_from_url(str(ica_document_url))
                    ica_text = full_text(ica_chunks)
                except Exception as e:
                    logger.warning(f"Failed to fetch ICA document: {e}")
            
            # Run adversarial forensics
            try:
                forensics_report = perform_adversarial_forensics(credit_agreement_text, ica_text)
                forensics_dict = forensics_report.to_dict()
                
                return AdversarialForensicsResponse(
                    analysis_id=analysis_id,
                    overall_exploit_risk=forensics_dict["overall_exploit_risk"],
                    serta_incora_risk_score=forensics_dict["serta_incora_risk_score"],
                    executive_summary=forensics_dict["executive_summary"],
                    amendment_provisions=forensics_dict["amendment_provisions"],
                    pro_rata_provisions=forensics_dict["pro_rata_provisions"],
                    guarantor_release_triggers=forensics_dict["guarantor_release_triggers"],
                    intercreditor_gaps=forensics_dict["intercreditor_gaps"],
                )
            except Exception as e:
                logger.error(f"Adversarial forensics failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Forensics analysis failed: {e}")
    
    @app.post("/analyses/{analysis_id}/priming-stress-test", response_model=PrimingStressTestResponse, dependencies=[Depends(verify_api_key)])
    async def run_priming_stress_test_on_analysis(
        analysis_id: int,
        priming_amount: Optional[float] = None
    ):
        """
        Run priming stress test on a completed analysis.
        
        Compares pre/post-priming recovery scenarios to identify fulcrum migration
        and recovery changes for each tranche.
        """
        with session_scope() as session:
            analysis = session.query(Analysis).filter_by(id=analysis_id).first()
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            # Extract waterfall data from analysis
            if not analysis.signals or "quant" not in analysis.signals:
                raise HTTPException(
                    status_code=400,
                    detail="Analysis does not contain waterfall data (quant signals missing)"
                )
            
            quant_data = analysis.signals["quant"]
            if not quant_data or "waterfall" not in quant_data:
                raise HTTPException(
                    status_code=400,
                    detail="Analysis does not contain waterfall results"
                )
            
            waterfall = quant_data["waterfall"]
            
            # Extract tranches and EV
            tranches = [
                {"name": r["name"], "claim": r["claim"]}
                for r in waterfall.get("recoveries", [])
            ]
            ev = waterfall.get("ev_used", 0) + waterfall.get("ev_remaining", 0)
            
            if not tranches or ev <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient waterfall data for priming stress test"
                )
            
            # Run priming stress test
            try:
                stress_result = run_priming_stress_test(
                    tranches=tranches,
                    ev=ev,
                    priming_amount=priming_amount,
                )
                
                return PrimingStressTestResponse(
                    analysis_id=analysis_id,
                    priming_facility_amount=stress_result["priming_facility_amount"],
                    pre_priming=stress_result["pre_priming"],
                    post_priming=stress_result["post_priming"],
                    fulcrum_migration=stress_result["fulcrum_migration"],
                    recovery_changes=stress_result["recovery_changes"],
                )
            except Exception as e:
                logger.error(f"Priming stress test failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Stress test failed: {e}")
    
    return app


async def process_analysis_job(
    job_id: str, 
    document_id: int, 
    analysis_type: str,
    uploaded_file_content: Optional[bytes] = None,
    uploaded_filename: Optional[str] = None,
    industry: Optional[str] = None,
    geography: Optional[str] = None,
    require_audit_gate: bool = False,
    include_tornado: bool = True,
    covenant_params: Optional[dict] = None,
    ch11_params: Optional[dict] = None,
):
    """
    Background task: Process analysis job.
    
    Args:
        job_id: Job identifier.
        document_id: Document to analyze.
        analysis_type: Type of analysis to perform.
        uploaded_file_content: Optional file content for uploaded files.
        uploaded_filename: Optional filename for uploaded files.
        industry: Optional industry filter for benchmarking.
        geography: Optional geography filter for benchmarking.
        require_audit_gate: Whether to require auditor pass.
        include_tornado: Whether to include tornado analysis.
        covenant_params: Optional covenant forensics parameters.
        ch11_params: Optional Chapter 11 feasibility parameters.
    """
    logger.info(f"Starting analysis job {job_id} for document {document_id}")
    
    try:
        with session_scope() as session:
            # Update job status to RUNNING
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            session.commit()
        
        # Run actual analysis pipeline
        import time
        import tempfile
        import shutil
        from pathlib import Path
        from signal_triage.pipeline import run_pipeline
        
        start_time = time.time()
        temp_upload_dir = None
        
        try:
            # Get document details
            with session_scope() as session:
                document = session.query(Document).filter_by(id=document_id).first()
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                
                # Determine input source
                if document.source_url:
                    # URL-based document
                    input_path = document.source_url
                    logger.info(f"Running pipeline on URL: {input_path}")
                elif uploaded_file_content and uploaded_filename:
                    # File upload - save to temporary file
                    temp_upload_dir = tempfile.mkdtemp()
                    temp_file_path = Path(temp_upload_dir) / uploaded_filename
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file_content)
                    input_path = temp_file_path
                    logger.info(f"Running pipeline on uploaded file: {uploaded_filename}")
                else:
                    # No source available
                    logger.error(f"Document {document_id} has no source_url or uploaded content")
                    raise ValueError("Document has no source - internal error")
            
            # Create temporary signals file
            signals_tmpdir = tempfile.mkdtemp()
            signals_path = Path(signals_tmpdir) / "signals.json"
            
            # Run pipeline with comprehensive parameters
            pipeline_params = {
                "file_path": input_path,
                "signals_path": signals_path,
                "require_audit_gate": require_audit_gate,
                "include_tornado": include_tornado,
            }
            
            # Add optional parameters
            if industry:
                pipeline_params["industry"] = industry
            if geography:
                pipeline_params["geography"] = geography
            if covenant_params:
                pipeline_params["covenant_params"] = covenant_params
            if ch11_params:
                pipeline_params["ch11_params"] = ch11_params
            
            logger.info(f"Executing pipeline with params: {pipeline_params}")
            report = run_pipeline(**pipeline_params)
            
        finally:
            # Clean up temporary directories
            if temp_upload_dir:
                try:
                    shutil.rmtree(temp_upload_dir)
                    logger.debug(f"Cleaned up temporary upload directory: {temp_upload_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary upload directory: {e}")
            
            if 'signals_tmpdir' in locals():
                try:
                    shutil.rmtree(signals_tmpdir)
                    logger.debug(f"Cleaned up temporary signals directory: {signals_tmpdir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary signals directory: {e}")
        
        execution_time = time.time() - start_time
        
        # Extract results from pipeline report
        document_report = report.get("document", {})
        distress_score = document_report.get("score")
        credit_opinion = document_report.get("tier_label", "Unknown")
        
        # Collect warnings from various stages
        warnings = []
        if report.get("error"):
            warnings.append(f"Pipeline error: {report['error']}")
        if not report.get("published", True):
            warnings.append("Report not published due to auditor gate failure")
        
        # Extract key findings from document report
        key_findings = {
            "tier": document_report.get("tier_label"),
            "signals_detected": document_report.get("signals", []),
            "covenant_score": document_report.get("covenant_score"),
            "financial_score": document_report.get("financial_score"),
            "market_score": document_report.get("market_score"),
        }
        
        # Add forensic results if available
        if report.get("covenant_forensics_result"):
            key_findings["covenant_forensics"] = report["covenant_forensics_result"]
        if report.get("ch11_feasibility_result"):
            key_findings["ch11_feasibility"] = report["ch11_feasibility_result"]
        if report.get("priming_risk_result"):
            key_findings["priming_risk"] = report["priming_risk_result"]
        
        # Extract signals from all agents
        signals = {
            "librarian": report.get("librarian_summary"),
            "quant": report.get("quant_summary"),
            "benchmarker": report.get("benchmarker_summary"),
            "auditor": report.get("auditor_summary"),
            "comparator": report.get("comparator_result"),
        }
        
        # Remove None values to reduce response size
        signals = {k: v for k, v in signals.items() if v is not None}
        
        # Identify market data sources used
        market_data_sources = []
        if report.get("benchmarker_summary"):
            benchmarker = report["benchmarker_summary"]
            if benchmarker.get("data_freshness"):
                market_data_sources.append({
                    "source": "benchmarker",
                    "last_updated": benchmarker["data_freshness"].get("last_updated_iso"),
                })
        
        # Store pipeline version from config
        pipeline_version = report.get("config_versions", {}).get("signals_config", "unknown")
        
        # Create analysis record with comprehensive results
        with session_scope() as session:
            # Prepare key_findings with warnings if present
            if warnings:
                key_findings["warnings"] = warnings
            
            analysis = Analysis(
                document_id=document_id,
                analysis_type=analysis_type,
                pipeline_version=str(pipeline_version),
                distress_score=distress_score,
                credit_opinion=credit_opinion,
                key_findings=key_findings,
                signals=signals,
                market_data_sources=market_data_sources,
                execution_time_seconds=execution_time,
            )
            session.add(analysis)
            session.flush()
            
            # Update job with analysis results
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.analysis_id = analysis.id
            session.commit()
            
            # Deliver webhook if configured
            if job.webhook_url:
                await deliver_webhook(job_id, job.webhook_url, job.webhook_secret, analysis.id)
        
        logger.info(f"Completed analysis job {job_id} (execution time: {execution_time:.2f}s)")
    
    except Exception as e:
        logger.error(f"Analysis job {job_id} failed: {e}", exc_info=True)
        
        # Update job status to FAILED
        with session_scope() as session:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
                job.error_message = str(e)
                session.commit()


async def deliver_webhook(job_id: str, webhook_url: str, webhook_secret: Optional[str], analysis_id: int):
    """
    Deliver webhook notification.
    
    Args:
        job_id: Job identifier.
        webhook_url: Webhook URL to call.
        webhook_secret: Optional webhook secret for HMAC signature.
        analysis_id: Analysis ID to include in payload.
    """
    import requests
    
    payload = {
        "job_id": job_id,
        "status": "completed",
        "analysis_id": analysis_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Add HMAC signature if secret provided
    if webhook_secret:
        import hmac
        import json
        
        signature = hmac.new(
            webhook_secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = signature
    
    try:
        config = get_config()
        resp = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=config.fastapi.webhook_timeout
        )
        resp.raise_for_status()
        
        # Update job webhook status
        with session_scope() as session:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            if job:
                job.webhook_delivered = True
                job.webhook_attempts += 1
                job.webhook_last_attempt = datetime.utcnow()
                session.commit()
        
        logger.info(f"Webhook delivered for job {job_id}")
    
    except Exception as e:
        logger.error(f"Webhook delivery failed for job {job_id}: {e}")
        
        # Update webhook attempt count
        with session_scope() as session:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            if job:
                job.webhook_attempts += 1
                job.webhook_last_attempt = datetime.utcnow()
                session.commit()
