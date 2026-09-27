#!/usr/bin/env python3
"""
Minute AI - Supabase Migration Runner
Executes the schema migration against remote Supabase PostgreSQL.
Supports direct Postgres connection string, db password, management API token, or CLI flags.
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PROJECT_REF = "qklcxzdumitujatjoxqn"
MIGRATION_FILE = PROJECT_ROOT / "supabase" / "migrations" / "001_initial_schema.sql"


def run_migration_via_postgres(connection_string: str) -> bool:
    """Execute SQL migration via direct PostgreSQL connection."""
    import psycopg2
    print(f"🔗 Connecting to Supabase PostgreSQL...")
    try:
        conn = psycopg2.connect(connection_string)
        conn.autocommit = True
        cursor = conn.cursor()

        print(f"📄 Reading migration from {MIGRATION_FILE.name}...")
        with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
            sql_content = f.read()

        print(f"⚡ Applying DDL migrations, RLS policies, and triggers...")
        cursor.execute(sql_content)

        # Verify created tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('profiles', 'jira_projects', 'transcripts', 'action_items');
        """)
        created = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        print(f"\n✅ Migration Successful! Verified {len(created)} tables in Supabase:")
        for t in created:
            print(f"   ✓ public.{t}")
        return True
    except Exception as e:
        print(f"\n❌ PostgreSQL migration failed: {e}")
        return False


def run_migration_via_management_api(token: str) -> bool:
    """Execute SQL migration via Supabase Management API."""
    import urllib.request
    import json

    print(f"🔑 Using Supabase Management API with personal access token...")
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"

    with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
        sql_content = f.read()

    req = urllib.request.Request(
        url,
        data=json.dumps({"query": sql_content}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Migration Successful! API response code: {resp.status}")
            return True
    except Exception as e:
        print(f"\n❌ Management API query failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Migrate Minute AI database schema to Supabase.")
    parser.add_argument("--db-password", "-p", help="Database password for postgres role")
    parser.add_argument("--db-url", help="Direct PostgreSQL connection string (postgresql://...)")
    parser.add_argument("--token", "-t", help="Supabase Personal Access Token (sbp_...)")
    args = parser.parse_args()

    # 1. Connection string provided
    conn_str = args.db_url or os.getenv("DATABASE_URL")
    if conn_str:
        success = run_migration_via_postgres(conn_str)
        sys.exit(0 if success else 1)

    # 2. Database password provided
    db_pass = args.db_password or os.getenv("SUPABASE_DB_PASSWORD")
    if db_pass:
        # Standard Supabase pooler / direct connection strings
        candidates = [
            f"postgresql://postgres:{db_pass}@db.{PROJECT_REF}.supabase.co:5432/postgres?sslmode=require",
            f"postgresql://postgres.{PROJECT_REF}:{db_pass}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require",
            f"postgresql://postgres.{PROJECT_REF}:{db_pass}@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require",
        ]
        for conn_attempt in candidates:
            try:
                if run_migration_via_postgres(conn_attempt):
                    sys.exit(0)
            except Exception:
                continue

    # 3. Management API token provided
    token = args.token or os.getenv("SUPABASE_ACCESS_TOKEN")
    if token:
        success = run_migration_via_management_api(token)
        sys.exit(0 if success else 1)

    # If no credentials were provided in CLI or environment
    print("=" * 70)
    print("           Minute AI - Supabase Migration Helper")
    print(f"           Project Reference: {PROJECT_REF}")
    print("=" * 70)
    print("\nTo apply the migration, choose one of the following methods:\n")
    print("Method 1: Run via Database Password")
    print(f"  python3 scripts/migrate_supabase.py --db-password <YOUR_DB_PASSWORD>")
    print("\nMethod 2: Run via Direct Connection String")
    print(f"  python3 scripts/migrate_supabase.py --db-url \"postgresql://postgres:[PASSWORD]@db.{PROJECT_REF}.supabase.co:5432/postgres\"")
    print("\nMethod 3: Run via Supabase Access Token")
    print(f"  python3 scripts/migrate_supabase.py --token <SUPABASE_PERSONAL_ACCESS_TOKEN>")
    print("\nMethod 4: Copy-paste in Supabase Dashboard SQL Editor (Instant & 100% Reliable)")
    print(f"  1. Open: https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new")
    print(f"  2. Paste the contents of: supabase/RUN_IN_SQL_EDITOR.sql")
    print(f"  3. Click 'Run' (Ctrl+Enter)")
    print("=" * 70)


if __name__ == "__main__":
    main()
