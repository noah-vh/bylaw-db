#!/usr/bin/env python3
"""
Script to set up the database schema in Supabase
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

# Read SQL files
def read_sql_file(filepath):
    with open(filepath, 'r') as file:
        return file.read()

# Execute SQL via Supabase REST API
def execute_sql(sql_content):
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "apikey": SUPABASE_SERVICE_KEY
    }
    
    data = {
        "sql": sql_content
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response

def main():
    print("Setting up Bylaw Database schema...")
    
    # Create a simple function to execute SQL (since we can't use the built-in exec_sql)
    create_function_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql text)
    RETURNS void AS $$
    BEGIN
        EXECUTE sql;
    END;
    $$ LANGUAGE plpgsql;
    """
    
    # Try to create the function first
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "apikey": SUPABASE_SERVICE_KEY
    }
    
    # First, let's just try to execute the schema directly via the SQL editor
    print("Please run the following SQL in your Supabase SQL Editor:")
    print("\n" + "="*50)
    
    # Read and print the schema files
    schema_files = [
        "database/schemas/001_initial_schema.sql",
        "database/schemas/002_rls_policies.sql"
    ]
    
    for schema_file in schema_files:
        if os.path.exists(schema_file):
            print(f"\n-- {schema_file} --")
            content = read_sql_file(schema_file)
            print(content)
            print("\n" + "="*50)
    
    print("\nTo apply the schema:")
    print("1. Go to your Supabase dashboard")
    print("2. Click on 'SQL Editor' in the left menu")
    print("3. Copy and paste the SQL above")
    print("4. Click 'Run' to execute")

if __name__ == "__main__":
    main()