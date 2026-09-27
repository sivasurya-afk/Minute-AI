"""
Tests for ExportService CSV and Excel generation.
"""

import io
import pandas as pd
from services.export_service import ExportService


def test_export_csv():
    items = [
        {
            "action_title": "Fix navbar",
            "description": "Fix alignment of navigation bar dropdown",
            "assignee": "Charlie",
            "project_name": "Frontend Web App",
            "jira_project_key": "FRONT",
            "priority": "High",
            "due_date": "Tomorrow",
            "action_type": "bug",
            "status": "Approved",
            "confidence_score": 0.95,
            "source_excerpt": "Charlie: I will fix the dropdown bug today.",
            "meeting_name": "Frontend Standup",
            "created_at": "2026-09-27T10:00:00Z",
        }
    ]

    csv_bytes = ExportService.to_csv(items)
    assert len(csv_bytes) > 0
    # Decode CSV and check content
    csv_str = csv_bytes.decode("utf-8")
    assert "Action Item" in csv_str
    assert "Fix navbar" in csv_str
    assert "Frontend Web App" in csv_str
    assert "Charlie" in csv_str


def test_export_excel():
    items = [
        {
            "action_title": "Deploy staging DB",
            "description": "Deploy PostgreSQL on RDS",
            "assignee": "Dana",
            "project_name": "Cloud Infrastructure",
            "jira_project_key": "INFRA",
            "priority": "Highest",
            "due_date": "Friday",
            "action_type": "task",
            "status": "Pending Review",
            "confidence_score": 0.92,
            "source_excerpt": "Dana: I will deploy the staging database by Friday.",
            "meeting_name": "DevOps Sync",
            "created_at": "2026-09-27T11:00:00Z",
        }
    ]

    excel_bytes = ExportService.to_excel(items)
    assert len(excel_bytes) > 0

    # Read back using pandas to verify Excel integrity
    df_read = pd.read_excel(io.BytesIO(excel_bytes))
    assert len(df_read) == 1
    assert df_read.iloc[0]["Action Item"] == "Deploy staging DB"
    assert df_read.iloc[0]["Project Key"] == "INFRA"
    assert df_read.iloc[0]["Assignee"] == "Dana"


def test_export_empty_list():
    csv_bytes = ExportService.to_csv([])
    assert len(csv_bytes) > 0  # Should contain header line
    excel_bytes = ExportService.to_excel([])
    assert len(excel_bytes) > 0
