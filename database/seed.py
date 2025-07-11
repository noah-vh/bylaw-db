#!/usr/bin/env python3
"""
Database seeding script for testing data.
Populates the database with sample data for development and testing.
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime, timedelta
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import json
import random

# Load environment variables
load_dotenv()


class DatabaseSeeder:
    """Handles database seeding for development and testing."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        if not all([self.supabase_url, self.supabase_key, self.database_url]):
            raise ValueError("Missing required environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    async def get_connection(self) -> asyncpg.Connection:
        """Get a direct database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def clear_data(self, conn: asyncpg.Connection):
        """Clear all data from tables (keeping schema)."""
        print("Clearing existing data...")
        
        # Get all tables to clear (excluding system tables)
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE 'schema_migrations'
        """)
        
        # Disable foreign key checks temporarily
        await conn.execute("SET session_replication_role = replica;")
        
        try:
            for table in tables:
                table_name = table['table_name']
                await conn.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
                print(f"  Cleared {table_name}")
        finally:
            # Re-enable foreign key checks
            await conn.execute("SET session_replication_role = DEFAULT;")
    
    async def seed_jurisdictions(self, conn: asyncpg.Connection) -> List[str]:
        """Seed jurisdiction data."""
        print("Seeding jurisdictions...")
        
        jurisdictions = [
            {
                'name': 'City of Toronto',
                'type': 'municipal',
                'code': 'TOR',
                'country': 'Canada',
                'province_state': 'Ontario',
                'website': 'https://www.toronto.ca',
                'population': 2731571,
                'established': '1834-01-01'
            },
            {
                'name': 'City of Vancouver',
                'type': 'municipal',
                'code': 'VAN',
                'country': 'Canada',
                'province_state': 'British Columbia',
                'website': 'https://vancouver.ca',
                'population': 662248,
                'established': '1886-04-06'
            },
            {
                'name': 'City of Montreal',
                'type': 'municipal',
                'code': 'MTL',
                'country': 'Canada',
                'province_state': 'Quebec',
                'website': 'https://montreal.ca',
                'population': 1704694,
                'established': '1642-01-01'
            },
            {
                'name': 'Province of Ontario',
                'type': 'provincial',
                'code': 'ON',
                'country': 'Canada',
                'province_state': 'Ontario',
                'website': 'https://ontario.ca',
                'population': 14734014,
                'established': '1867-07-01'
            },
            {
                'name': 'Government of Canada',
                'type': 'federal',
                'code': 'CAN',
                'country': 'Canada',
                'province_state': None,
                'website': 'https://canada.ca',
                'population': 38000000,
                'established': '1867-07-01'
            }
        ]
        
        jurisdiction_ids = []
        for j in jurisdictions:
            result = await conn.fetchrow("""
                INSERT INTO jurisdictions (
                    name, type, code, country, province_state, 
                    website, population, established, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                RETURNING id
            """, j['name'], j['type'], j['code'], j['country'], 
                j['province_state'], j['website'], j['population'], 
                j['established']
            )
            jurisdiction_ids.append(result['id'])
            print(f"  Added {j['name']}")
        
        return jurisdiction_ids
    
    async def seed_documents(self, conn: asyncpg.Connection, jurisdiction_ids: List[str]) -> List[str]:
        """Seed document data."""
        print("Seeding documents...")
        
        document_types = ['bylaw', 'regulation', 'policy', 'ordinance', 'resolution']
        statuses = ['active', 'draft', 'archived', 'superseded']
        
        documents = []
        for i, jurisdiction_id in enumerate(jurisdiction_ids):
            for j in range(random.randint(5, 15)):
                doc_type = random.choice(document_types)
                status = random.choice(statuses)
                
                # Generate realistic document data
                doc_number = f"{doc_type.upper()}-{2020 + random.randint(0, 4)}-{random.randint(1, 999):03d}"
                
                documents.append({
                    'jurisdiction_id': jurisdiction_id,
                    'title': f"Sample {doc_type.title()} {doc_number}",
                    'document_number': doc_number,
                    'document_type': doc_type,
                    'status': status,
                    'effective_date': datetime.now() - timedelta(days=random.randint(0, 1825)),
                    'url': f"https://example.com/docs/{doc_number.lower()}",
                    'file_path': f"documents/{jurisdiction_id}/{doc_number}.pdf",
                    'file_size': random.randint(50000, 5000000),
                    'checksum': f"sha256:{random.randint(1000000000, 9999999999)}",
                    'metadata': json.dumps({
                        'pages': random.randint(1, 50),
                        'language': 'en',
                        'format': 'pdf'
                    })
                })
        
        document_ids = []
        for doc in documents:
            result = await conn.fetchrow("""
                INSERT INTO documents (
                    jurisdiction_id, title, document_number, document_type,
                    status, effective_date, url, file_path, file_size,
                    checksum, metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW()
                ) RETURNING id
            """, doc['jurisdiction_id'], doc['title'], doc['document_number'],
                doc['document_type'], doc['status'], doc['effective_date'],
                doc['url'], doc['file_path'], doc['file_size'],
                doc['checksum'], doc['metadata']
            )
            document_ids.append(result['id'])
        
        print(f"  Added {len(documents)} documents")
        return document_ids
    
    async def seed_sections(self, conn: asyncpg.Connection, document_ids: List[str]):
        """Seed document sections."""
        print("Seeding document sections...")
        
        section_count = 0
        for document_id in document_ids:
            # Each document gets 3-10 sections
            num_sections = random.randint(3, 10)
            
            for i in range(num_sections):
                section_number = f"{i+1}"
                if random.random() < 0.3:  # 30% chance of subsection
                    section_number = f"{i+1}.{random.randint(1, 5)}"
                
                await conn.execute("""
                    INSERT INTO document_sections (
                        document_id, section_number, title, content,
                        page_number, created_at
                    ) VALUES ($1, $2, $3, $4, $5, NOW())
                """, document_id, section_number, 
                    f"Section {section_number} - Sample Title",
                    f"This is sample content for section {section_number}. " +
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " +
                    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                    random.randint(1, 20)
                )
                section_count += 1
        
        print(f"  Added {section_count} sections")
    
    async def seed_scraping_jobs(self, conn: asyncpg.Connection, jurisdiction_ids: List[str]):
        """Seed scraping job data."""
        print("Seeding scraping jobs...")
        
        job_statuses = ['pending', 'running', 'completed', 'failed']
        
        jobs = []
        for jurisdiction_id in jurisdiction_ids:
            for _ in range(random.randint(2, 8)):
                status = random.choice(job_statuses)
                
                job = {
                    'jurisdiction_id': jurisdiction_id,
                    'job_type': 'full_scrape',
                    'status': status,
                    'started_at': datetime.now() - timedelta(days=random.randint(0, 30)),
                    'parameters': json.dumps({
                        'max_pages': random.randint(10, 100),
                        'include_archived': random.choice([True, False])
                    })
                }
                
                if status in ['completed', 'failed']:
                    job['completed_at'] = job['started_at'] + timedelta(
                        minutes=random.randint(5, 120)
                    )
                    job['documents_found'] = random.randint(0, 50) if status == 'completed' else 0
                    job['documents_processed'] = job['documents_found']
                    job['errors'] = json.dumps([]) if status == 'completed' else json.dumps([
                        {'error': 'Connection timeout', 'timestamp': datetime.now().isoformat()}
                    ])
                
                jobs.append(job)
        
        for job in jobs:
            await conn.execute("""
                INSERT INTO scraping_jobs (
                    jurisdiction_id, job_type, status, started_at,
                    completed_at, documents_found, documents_processed,
                    parameters, errors, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
            """, job['jurisdiction_id'], job['job_type'], job['status'],
                job['started_at'], job.get('completed_at'), 
                job.get('documents_found'), job.get('documents_processed'),
                job['parameters'], job.get('errors')
            )
        
        print(f"  Added {len(jobs)} scraping jobs")
    
    async def seed_all(self, clear_existing: bool = False):
        """Seed all test data."""
        conn = await self.get_connection()
        
        try:
            if clear_existing:
                await self.clear_data(conn)
            
            print("Starting database seeding...")
            
            # Seed in order of dependencies
            jurisdiction_ids = await self.seed_jurisdictions(conn)
            document_ids = await self.seed_documents(conn, jurisdiction_ids)
            await self.seed_sections(conn, document_ids)
            await self.seed_scraping_jobs(conn, jurisdiction_ids)
            
            print("Database seeding completed successfully!")
            
        except Exception as e:
            print(f"Seeding failed: {e}")
            raise
        finally:
            await conn.close()
    
    async def seed_minimal(self):
        """Seed minimal data for basic testing."""
        conn = await self.get_connection()
        
        try:
            print("Seeding minimal test data...")
            
            # Add one jurisdiction
            jurisdiction_id = await conn.fetchval("""
                INSERT INTO jurisdictions (
                    name, type, code, country, website, created_at
                ) VALUES (
                    'Test City', 'municipal', 'TEST', 'Canada', 
                    'https://test.example.com', NOW()
                ) RETURNING id
            """)
            
            # Add one document
            document_id = await conn.fetchval("""
                INSERT INTO documents (
                    jurisdiction_id, title, document_number, 
                    document_type, status, created_at
                ) VALUES (
                    $1, 'Test Bylaw 2024-001', 'BYLAW-2024-001',
                    'bylaw', 'active', NOW()
                ) RETURNING id
            """, jurisdiction_id)
            
            # Add one section
            await conn.execute("""
                INSERT INTO document_sections (
                    document_id, section_number, title, content, created_at
                ) VALUES (
                    $1, '1', 'Test Section', 'This is test content.', NOW()
                )
            """, document_id)
            
            print("Minimal seeding completed!")
            
        finally:
            await conn.close()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database seeding tool")
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear existing data before seeding"
    )
    parser.add_argument(
        "--minimal", 
        action="store_true",
        help="Seed minimal data only"
    )
    
    args = parser.parse_args()
    
    seeder = DatabaseSeeder()
    
    try:
        if args.minimal:
            await seeder.seed_minimal()
        else:
            await seeder.seed_all(clear_existing=args.clear)
    except Exception as e:
        print(f"Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())