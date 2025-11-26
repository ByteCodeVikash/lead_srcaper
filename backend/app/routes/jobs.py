from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import io

from app.database import get_db
from app.models.job import Job, CompanyResult, JobStatus
from app.tasks.scraping_tasks import process_scraping_job_task
from app.services.export import ExportService
from app.config import get_settings

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
settings = get_settings()
export_service = ExportService(settings.export_dir)


# Pydantic models for requests/responses
class CreateJobRequest(BaseModel):
    companies: Optional[List[str]] = None
    settings: Optional[dict] = None


class JobResponse(BaseModel):
    id: int
    status: JobStatus
    total_companies: int
    processed_companies: int
    total_phones_found: int
    total_emails_found: int
    companies_with_no_contact: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    celery_task_id: Optional[str]
    
    class Config:
        from_attributes = True


class CompanyResultResponse(BaseModel):
    id: int
    original_input: str
    detected_input_type: str
    resolved_company_name: Optional[str]
    resolved_website_url: Optional[str]
    number_of_unique_phone_numbers_found: int
    number_of_unique_emails_found: int
    list_of_phone_numbers: List[str]
    list_of_emails: List[str]
    other_contact_links: dict
    data_sources: List[str]
    extraction_status: str
    confidence_score: float
    timestamp: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True


@router.post("/", response_model=JobResponse)
async def create_job(
    request: CreateJobRequest = None,
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new scraping job.
    
    Accepts either:
    - JSON with list of company names/URLs
    - CSV/Excel file upload
    """
    companies = []
    
    # Parse input from request body
    if request and request.companies:
        companies = request.companies
    
    # Parse input from file upload
    elif file:
        content = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")
        
        # Extract first column as company names/URLs
        if len(df.columns) > 0:
            companies = df.iloc[:, 0].dropna().astype(str).tolist()
    
    else:
        raise HTTPException(status_code=400, detail="Provide either companies list or file upload.")
    
    if not companies:
        raise HTTPException(status_code=400, detail="No companies provided.")
    
    # Create job record
    job = Job(
        status=JobStatus.PENDING,
        total_companies=len(companies),
        processed_companies=0,
        settings=request.settings if request else None
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Start background task
    task = process_scraping_job_task.delay(job.id, companies)
    
    # Update job with Celery task ID
    job.celery_task_id = task.id
    await db.commit()
    
    return job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all jobs with pagination."""
    result = await db.execute(
        select(Job)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get job details by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.get("/{job_id}/results", response_model=List[CompanyResultResponse])
async def get_job_results(
    job_id: int,
    skip: int = 0,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db)
):
    """Get results for a job."""
    # Verify job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get results
    result = await db.execute(
        select(CompanyResult)
        .where(CompanyResult.job_id == job_id)
        .order_by(CompanyResult.id)
        .offset(skip)
        .limit(limit)
    )
    results = result.scalars().all()
    
    return results


@router.get("/{job_id}/status")
async def get_job_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get detailed job status including progress.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate progress percentage
    progress = 0
    if job.total_companies > 0:
        progress = (job.processed_companies / job.total_companies) * 100
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress_percentage": round(progress, 2),
        "processed_companies": job.processed_companies,
        "total_companies": job.total_companies,
        "total_phones_found": job.total_phones_found,
        "total_emails_found": job.total_emails_found,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message
    }


@router.get("/{job_id}/export/csv")
async def export_csv(job_id: int, db: AsyncSession = Depends(get_db)):
    """Export job results to CSV."""
    # Get job and results
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results_query = await db.execute(
        select(CompanyResult).where(CompanyResult.job_id == job_id)
    )
    results = results_query.scalars().all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    # Export to CSV
    filepath = export_service.export_to_csv(job_id, results)
    
    return FileResponse(
        filepath,
        media_type="text/csv",
        filename=f"job_{job_id}_results.csv"
    )


@router.get("/{job_id}/export/xlsx")
async def export_excel(job_id: int, db: AsyncSession = Depends(get_db)):
    """Export job results to Excel."""
    # Get job and results
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results_query = await db.execute(
        select(CompanyResult).where(CompanyResult.job_id == job_id)
    )
    results = results_query.scalars().all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    # Export to Excel
    filepath = export_service.export_to_excel(job_id, results)
    
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"job_{job_id}_results.xlsx"
    )


@router.get("/{job_id}/export/zip")
async def export_zip(job_id: int, db: AsyncSession = Depends(get_db)):
    """Export job results to ZIP archive."""
    # Get job and results
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    results_query = await db.execute(
        select(CompanyResult).where(CompanyResult.job_id == job_id)
    )
    results = results_query.scalars().all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    # Export to ZIP
    filepath = export_service.export_to_zip(job_id, results)
    
    return FileResponse(
        filepath,
        media_type="application/zip",
        filename=f"job_{job_id}_archive.zip"
    )


@router.get("/{job_id}/summary")
async def get_job_summary(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get aggregated summary for a job."""
    # Get results
    results_query = await db.execute(
        select(CompanyResult).where(CompanyResult.job_id == job_id)
    )
    results = results_query.scalars().all()
    
    if not results:
        return {"message": "No results yet"}
    
    # Generate summary
    summary = export_service.generate_summary(results)
    
    return summary
