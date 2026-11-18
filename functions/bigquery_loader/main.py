"""Cloud Function ``bigquery-loader``: GCS ``_load.json`` finalized → BigQuery load.

The logic lives in ``glamira_pipeline.warehouse.function``; the deploy script
copies that package next to this file. See src/glamira_pipeline/warehouse/README.md.
"""
import functions_framework

from glamira_pipeline.warehouse.function import handle


@functions_framework.cloud_event
def on_object_finalized(cloud_event) -> None:
    handle(cloud_event.data)
