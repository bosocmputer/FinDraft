from workers.celery_app import celery_app
from datetime import datetime, timezone


def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


@celery_app.task(bind=True, max_retries=3)
def run_mapping_task(self, project_id: str, org_id: str):
    """
    Async AI mapping task
    1. ดึง unconfirmed TB rows
    2. Batch map ผ่าน AI provider (ผ่าน provider_factory)
    3. บันทึกผลลง account_mappings
    4. Update jobs table progress
    TODO: implement full async mapping
    """
    raise NotImplementedError("Mapping worker — implement async mapping")
