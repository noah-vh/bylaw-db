#!/usr/bin/env python3
"""
Database migration runner script.
Manages database schema migrations and version control.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import asyncio
import asyncpg
from typing import Optional, List, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migrations for Supabase/PostgreSQL."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        if not all([self.supabase_url, self.supabase_key, self.database_url]):
            raise ValueError("Missing required environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.migrations_dir = Path(__file__).parent / "migrations"
        
    async def get_connection(self) -> asyncpg.Connection:
        """Get a direct database connection."""
        return await asyncpg.connect(self.database_url)
    
    async def init_migrations_table(self, conn: asyncpg.Connection):
        """Create migrations tracking table if it doesn't exist."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64),
                description TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_migrations_version 
            ON schema_migrations(version);
        """)
        logger.info("Migrations table initialized")
    
    async def get_applied_migrations(self, conn: asyncpg.Connection) -> List[str]:
        """Get list of already applied migrations."""
        rows = await conn.fetch(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        return [row['version'] for row in rows]
    
    def get_pending_migrations(self, applied: List[str]) -> List[Tuple[str, Path]]:
        """Get list of migrations that haven't been applied yet."""
        pending = []
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return pending
        
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            version = migration_file.stem
            if version not in applied:
                pending.append((version, migration_file))
        
        return pending
    
    async def apply_migration(
        self, 
        conn: asyncpg.Connection, 
        version: str, 
        migration_path: Path
    ):
        """Apply a single migration."""
        logger.info(f"Applying migration: {version}")
        
        # Read migration content
        content = migration_path.read_text()
        
        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        # Extract description from first comment line
        description = ""
        for line in content.split('\n'):
            if line.strip().startswith('--'):
                description = line.strip()[2:].strip()
                break
        
        try:
            # Begin transaction
            async with conn.transaction():
                # Apply migration
                await conn.execute(content)
                
                # Record migration
                await conn.execute("""
                    INSERT INTO schema_migrations (version, checksum, description)
                    VALUES ($1, $2, $3)
                """, version, checksum, description)
                
            logger.info(f"Successfully applied migration: {version}")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
            raise
    
    async def migrate_up(self, target: Optional[str] = None):
        """Run pending migrations up to target version."""
        conn = await self.get_connection()
        
        try:
            # Initialize migrations table
            await self.init_migrations_table(conn)
            
            # Get applied migrations
            applied = await self.get_applied_migrations(conn)
            logger.info(f"Found {len(applied)} applied migrations")
            
            # Get pending migrations
            pending = self.get_pending_migrations(applied)
            logger.info(f"Found {len(pending)} pending migrations")
            
            if not pending:
                logger.info("No pending migrations to apply")
                return
            
            # Apply migrations
            for version, path in pending:
                if target and version > target:
                    logger.info(f"Stopping at target version: {target}")
                    break
                    
                await self.apply_migration(conn, version, path)
                
        finally:
            await conn.close()
    
    async def migrate_down(self, steps: int = 1):
        """Rollback migrations (requires down migrations)."""
        conn = await self.get_connection()
        
        try:
            # Get applied migrations
            applied = await self.get_applied_migrations(conn)
            
            if not applied:
                logger.info("No migrations to rollback")
                return
            
            # Rollback specified number of steps
            to_rollback = applied[-steps:]
            
            for version in reversed(to_rollback):
                down_path = self.migrations_dir / f"{version}.down.sql"
                
                if not down_path.exists():
                    logger.error(f"Down migration not found for {version}")
                    continue
                
                logger.info(f"Rolling back migration: {version}")
                
                content = down_path.read_text()
                
                async with conn.transaction():
                    await conn.execute(content)
                    await conn.execute(
                        "DELETE FROM schema_migrations WHERE version = $1",
                        version
                    )
                
                logger.info(f"Successfully rolled back: {version}")
                
        finally:
            await conn.close()
    
    async def status(self):
        """Show migration status."""
        conn = await self.get_connection()
        
        try:
            await self.init_migrations_table(conn)
            
            # Get applied migrations
            applied = await self.get_applied_migrations(conn)
            pending = self.get_pending_migrations(applied)
            
            print("\n=== Migration Status ===")
            print(f"Applied migrations: {len(applied)}")
            print(f"Pending migrations: {len(pending)}")
            
            if applied:
                print("\nApplied:")
                rows = await conn.fetch("""
                    SELECT version, applied_at, description 
                    FROM schema_migrations 
                    ORDER BY version DESC 
                    LIMIT 10
                """)
                for row in rows:
                    print(f"  - {row['version']} ({row['applied_at']}) - {row['description']}")
            
            if pending:
                print("\nPending:")
                for version, path in pending[:10]:
                    print(f"  - {version} ({path.name})")
                    
        finally:
            await conn.close()
    
    async def create_migration(self, name: str):
        """Create a new migration file."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version = f"{timestamp}_{name}"
        
        up_path = self.migrations_dir / f"{version}.sql"
        down_path = self.migrations_dir / f"{version}.down.sql"
        
        # Create migrations directory if it doesn't exist
        self.migrations_dir.mkdir(exist_ok=True)
        
        # Create up migration
        up_content = f"""-- {name}: Add description here

-- Add your UP migration SQL here

"""
        up_path.write_text(up_content)
        
        # Create down migration
        down_content = f"""-- Rollback for {name}

-- Add your DOWN migration SQL here

"""
        down_path.write_text(down_content)
        
        logger.info(f"Created migration: {version}")
        print(f"Created files:")
        print(f"  - {up_path}")
        print(f"  - {down_path}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database migration tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Migrate up
    up_parser = subparsers.add_parser("up", help="Run pending migrations")
    up_parser.add_argument(
        "--target", 
        help="Target version to migrate to"
    )
    
    # Migrate down
    down_parser = subparsers.add_parser("down", help="Rollback migrations")
    down_parser.add_argument(
        "--steps", 
        type=int, 
        default=1,
        help="Number of migrations to rollback"
    )
    
    # Status
    subparsers.add_parser("status", help="Show migration status")
    
    # Create
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("name", help="Migration name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    runner = MigrationRunner()
    
    try:
        if args.command == "up":
            await runner.migrate_up(args.target)
        elif args.command == "down":
            await runner.migrate_down(args.steps)
        elif args.command == "status":
            await runner.status()
        elif args.command == "create":
            await runner.create_migration(args.name)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())