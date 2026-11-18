"""Publish raw exports to GCS and load them into BigQuery.

``spec``, ``bigquery`` and ``function`` depend only on the Google Cloud client
libraries, so they deploy unchanged as the Cloud Function; ``publish`` and
``cli`` also use the export package and run where the export files are.
"""
