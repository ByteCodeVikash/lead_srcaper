import asyncio
from datetime import datetime
from typing import List, Dict
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.services.job_processor import JobProcessor
from app.models.job import Job, CompanyResult, JobStatus
from app.database import AsyncSessionLocal
import json


@celery_app.task(bind=True, name='process_scraping_job')
def process_scraping_job_task(self, job_id: int, company_inputs: List[str]):
    """
    Celery task to process a scraping job.
    
    Args:
        job_id: Database ID of the job
        company_inputs: List of company names/URLs to process
    """
    # Run async processing
    asyncio.run(_process_job_async(self, job_id, company_inputs))


async def _process_job_async(task, job_id: int, company_inputs: List[str]):
    """Async function to process job."""
    async with AsyncSessionLocal() as session:
        try:
            # Get job from database
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            
            if not job:
                return
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            await session.commit()
            
            # Initialize processor
            processor = JobProcessor()
            
            # Process each company
            total_companies = len(company_inputs)
            processed = 0
            
            total_phones = 0
            total_emails = 0
            no_contact_count = 0
            
            for idx, company_input in enumerate(company_inputs):
                try:
                    # Update progress
                    task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': idx + 1,
                            'total': total_companies,
                            'status': f'Processing: {company_input[:50]}...'
                        }
                    )
                    
                    # Process company
                    result_data = await processor.process_company(company_input)
                    
                    # Create result record
                    company_result = CompanyResult(
                        job_id=job_id,
                        original_input=result_data['original_input'],
                        detected_input_type=result_data['detected_input_type'],
                        resolved_company_name=result_data['resolved_company_name'],
                        resolved_website_url=result_data['resolved_website_url'],
                        number_of_unique_phone_numbers_found=result_data['number_of_unique_phone_numbers_found'],
                        number_of_unique_emails_found=result_data['number_of_unique_emails_found'],
                        list_of_phone_numbers=result_data['list_of_phone_numbers'],
                        list_of_emails=result_data['list_of_emails'],
                        other_contact_links=result_data['other_contact_links'],
                        data_sources=result_data['data_sources'],
                        extraction_status=result_data['extraction_status'],
                        confidence_score=result_data['confidence_score'],
                        notes=result_data['notes'],
                        raw_html_pages=result_data.get('raw_html_pages')
                    )
                    
                    session.add(company_result)
                    
                    # Update counters
                    total_phones += result_data['number_of_unique_phone_numbers_found']
                    total_emails += result_data['number_of_unique_emails_found']
                    
                    if result_data['number_of_unique_phone_numbers_found'] == 0 and \
                       result_data['number_of_unique_emails_found'] == 0:
                        no_contact_count += 1
                    
                    processed += 1
                    
                    # Commit after each company (for progress tracking)
                    job.processed_companies = processed
                    await session.commit()
                
                except Exception as e:
                    print(f"Error processing company '{company_input}': {e}")
                    # Continue with next company
                    processed += 1
                    job.processed_companies = processed
                    await session.commit()
            
            # Update job with final stats
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.total_phones_found = total_phones
            job.total_emails_found = total_emails
            job.companies_with_no_contact = no_contact_count
            
            await session.commit()
        
        except Exception as e:
            # Mark job as failed
            async with AsyncSessionLocal() as err_session:
                result = await err_session.execute(select(Job).where(Job.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    await err_session.commit()
            raise


@celery_app.task(name='process_single_company')
def process_single_company_task(company_input: str) -> Dict:
    """
    Process a single company (for retries).
    
    Args:
        company_input: Company name or URL
    
    Returns:
        Processed result dict
    """
    processor = JobProcessor()
    return asyncio.run(processor.process_company(company_input))
