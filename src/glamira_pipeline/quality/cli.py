"""Run sample data-quality checks and write the reports."""
import argparse
from pathlib import Path

from bson.errors import BSONError

from glamira_pipeline.config import DEFAULT_REPORT_DIR, DEFAULT_SAMPLE, MAX_DOCUMENTS
from glamira_pipeline.quality.assessment import assess_sample
from glamira_pipeline.quality.reports import write_reports


def main() -> None:
    """Parse CLI arguments, assess the sample, and write reports; exit on errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE, help="Canonical Extended JSON array")
    parser.add_argument("--max-documents", type=int, default=MAX_DOCUMENTS, help="Maximum sample rows (1–100000)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Directory for the summary and data_quality/ reports")
    args = parser.parse_args()
    if not 1 <= args.max_documents <= MAX_DOCUMENTS:
        parser.error(f"--max-documents must be between 1 and {MAX_DOCUMENTS:,}")
    try:
        assessment = assess_sample(args.sample, args.max_documents)
        paths = write_reports(assessment, args.sample, args.output_dir)
    except OSError as exc:
        parser.exit(1, f"Data-quality assessment failed ({type(exc).__name__}): {exc.strerror or 'file access error'}\n")
    except (ValueError, TypeError, BSONError) as exc:
        parser.exit(1, f"Data-quality assessment failed ({type(exc).__name__}). Check the sample format and input options; raw data is not logged.\n")
    print(f"Assessed {assessment.rows:,} sample records")
    for path in paths:
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
