from workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def run_export_task(self, project_id: str, export_type: str, org_id: str):
    """
    Async export task (Excel/PDF)
    1. ดึง financial_statements ล่าสุด
    2. Generate file (Excel หรือ PDF + DRAFT watermark ถ้า status != finalized)
    3. Upload ไป Supabase Storage (exports/ bucket)
    4. บันทึกลง export_history
    5. Update jobs table → done
    TODO: implement full async export
    """
    raise NotImplementedError("Export worker — implement async export")
