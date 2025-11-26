import os
import pandas as pd
from typing import List
from datetime import datetime
import zipfile
import json
from app.models.job import CompanyResult


class ExportService:
    """Service to export job results to various formats."""
    
    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
    
    def export_to_csv(self, job_id: int, results: List[CompanyResult]) -> str:
        """
        Export results to CSV file.
        
        Returns:
            Path to CSV file
        """
        # Convert results to list of dicts
        data = []
        for result in results:
            data.append({
                'Original Input': result.original_input,
                'Input Type': result.detected_input_type.value,
                'Company Name': result.resolved_company_name,
                'Website URL': result.resolved_website_url,
                'Phone Count': result.number_of_unique_phone_numbers_found,
                'Email Count': result.number_of_unique_emails_found,
                'Phone Numbers': ', '.join(result.list_of_phone_numbers),
                'Emails': ', '.join(result.list_of_emails),
                'LinkedIn': result.other_contact_links.get('linkedin', ''),
                'Facebook': result.other_contact_links.get('facebook', ''),
                'Twitter': result.other_contact_links.get('twitter', ''),
                'Instagram': result.other_contact_links.get('instagram', ''),
                'Data Sources': ', '.join(result.data_sources),
                'Extraction Status': result.extraction_status.value,
                'Confidence Score': result.confidence_score,
                'Timestamp': result.timestamp,
                'Notes': result.notes
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export to CSV
        filename = f"job_{job_id}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.export_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath
    
    def export_to_excel(self, job_id: int, results: List[CompanyResult]) -> str:
        """
        Export results to Excel file with multiple sheets.
        
        Returns:
            Path to Excel file
        """
        # Main results sheet
        data = []
        for result in results:
            data.append({
                'Original Input': result.original_input,
                'Input Type': result.detected_input_type.value,
                'Company Name': result.resolved_company_name,
                'Website URL': result.resolved_website_url,
                'Phone Count': result.number_of_unique_phone_numbers_found,
                'Email Count': result.number_of_unique_emails_found,
                'Phone Numbers': ', '.join(result.list_of_phone_numbers),
                'Emails': ', '.join(result.list_of_emails),
                'LinkedIn': result.other_contact_links.get('linkedin', ''),
                'Facebook': result.other_contact_links.get('facebook', ''),
                'Twitter': result.other_contact_links.get('twitter', ''),
                'Instagram': result.other_contact_links.get('instagram', ''),
                'Data Sources': ', '.join(result.data_sources),
                'Extraction Status': result.extraction_status.value,
                'Confidence Score': result.confidence_score,
                'Timestamp': result.timestamp,
                'Notes': result.notes
            })
        
        df_main = pd.DataFrame(data)
        
        # Summary sheet
        total_companies = len(results)
        total_phones = sum(r.number_of_unique_phone_numbers_found for r in results)
        total_emails = sum(r.number_of_unique_emails_found for r in results)
        no_contact = sum(1 for r in results if r.number_of_unique_phone_numbers_found == 0 and r.number_of_unique_emails_found == 0)
        
        summary_data = [
            {'Metric': 'Total Companies Processed', 'Value': total_companies},
            {'Metric': 'Total Unique Phone Numbers', 'Value': total_phones},
            {'Metric': 'Total Unique Emails', 'Value': total_emails},
            {'Metric': 'Companies with No Contact Info', 'Value': no_contact},
            {'Metric': 'Companies with Contact Info', 'Value': total_companies - no_contact},
        ]
        df_summary = pd.DataFrame(summary_data)
        
        # Export to Excel with multiple sheets
        filename = f"job_{job_id}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.export_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df_main.to_excel(writer, sheet_name='Results', index=False)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        return filepath
    
    def export_to_zip(self, job_id: int, results: List[CompanyResult]) -> str:
        """
        Export results to ZIP archive with JSON and raw HTML pages.
        
        Returns:
            Path to ZIP file
        """
        filename = f"job_{job_id}_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        filepath = os.path.join(self.export_dir, filename)
        
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON results
            json_data = []
            for result in results:
                json_data.append({
                    'original_input': result.original_input,
                    'detected_input_type': result.detected_input_type.value,
                    'resolved_company_name': result.resolved_company_name,
                    'resolved_website_url': result.resolved_website_url,
                    'number_of_unique_phone_numbers_found': result.number_of_unique_phone_numbers_found,
                    'number_of_unique_emails_found': result.number_of_unique_emails_found,
                    'list_of_phone_numbers': result.list_of_phone_numbers,
                    'list_of_emails': result.list_of_emails,
                    'other_contact_links': result.other_contact_links,
                    'data_sources': result.data_sources,
                    'extraction_status': result.extraction_status.value,
                    'confidence_score': result.confidence_score,
                    'timestamp': result.timestamp.isoformat() if result.timestamp else None,
                    'notes': result.notes,
                    'raw_html_pages': result.raw_html_pages
                })
            
            # Write JSON file
            zipf.writestr('results.json', json.dumps(json_data, indent=2))
            
            # Write summary
            summary = {
                'job_id': job_id,
                'total_companies': len(results),
                'total_phones': sum(r.number_of_unique_phone_numbers_found for r in results),
                'total_emails': sum(r.number_of_unique_emails_found for r in results),
                'export_date': datetime.now().isoformat()
            }
            zipf.writestr('summary.json', json.dumps(summary, indent=2))
        
        return filepath
    
    def generate_summary(self, results: List[CompanyResult]) -> dict:
        """Generate aggregated summary statistics."""
        total_companies = len(results)
        total_phones = sum(r.number_of_unique_phone_numbers_found for r in results)
        total_emails = sum(r.number_of_unique_emails_found for r in results)
        no_contact = sum(
            1 for r in results 
            if r.number_of_unique_phone_numbers_found == 0 and r.number_of_unique_emails_found == 0
        )
        
        # Group by extraction status
        status_breakdown = {}
        for result in results:
            status = result.extraction_status.value
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Average confidence score
        avg_confidence = sum(r.confidence_score for r in results) / total_companies if total_companies > 0 else 0
        
        return {
            'total_companies_processed': total_companies,
            'total_unique_phone_numbers': total_phones,
            'total_unique_emails': total_emails,
            'companies_with_no_contact': no_contact,
            'companies_with_contact': total_companies - no_contact,
            'status_breakdown': status_breakdown,
            'average_confidence_score': round(avg_confidence, 2)
        }
