#!/usr/bin/env python3
"""
Database backup and restore utilities.
Handles automated backups, point-in-time recovery, and data archival.
"""

import os
import sys
import asyncio
import asyncpg
import subprocess
import gzip
import json
import boto3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Handles database backup and restore operations."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
        
        # S3 configuration for remote backups
        self.s3_bucket = os.getenv("BACKUP_S3_BUCKET")
        self.s3_region = os.getenv("BACKUP_S3_REGION", "us-east-1")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize S3 client if credentials are available
        self.s3_client = None
        if all([self.s3_bucket, self.aws_access_key, self.aws_secret_key]):
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.s3_region
            )
    
    def parse_database_url(self) -> Dict[str, str]:
        """Parse database URL into components."""
        from urllib.parse import urlparse
        
        parsed = urlparse(self.database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'username': parsed.username,
            'password': parsed.password
        }
    
    async def create_backup(
        self, 
        backup_name: Optional[str] = None,
        compress: bool = True,
        upload_to_s3: bool = True
    ) -> str:
        """Create a database backup."""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / f"{backup_name}.sql"
        if compress:
            backup_path = backup_path.with_suffix('.sql.gz')
        
        logger.info(f"Creating backup: {backup_path}")
        
        # Parse database URL
        db_config = self.parse_database_url()
        
        # Create pg_dump command
        cmd = [
            'pg_dump',
            '--host', str(db_config['host']),
            '--port', str(db_config['port']),
            '--username', db_config['username'],
            '--dbname', db_config['database'],
            '--no-password',
            '--verbose',
            '--clean',
            '--if-exists',
            '--create',
            '--format=plain'
        ]
        
        # Set environment variables for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        try:
            # Run pg_dump
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"pg_dump failed: {stderr}")
            
            # Write backup file
            if compress:
                with gzip.open(backup_path, 'wt') as f:
                    f.write(stdout)
            else:
                with open(backup_path, 'w') as f:
                    f.write(stdout)
            
            # Get file size
            file_size = backup_path.stat().st_size
            logger.info(f"Backup created: {backup_path} ({file_size} bytes)")
            
            # Create metadata file
            metadata = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'file_size': file_size,
                'compressed': compress,
                'database_url': self.database_url.split('@')[1],  # Hide credentials
                'pg_dump_version': self._get_pg_dump_version()
            }
            
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload to S3 if configured
            if upload_to_s3 and self.s3_client:
                await self._upload_to_s3(backup_path, metadata_path)
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Clean up partial backup
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    async def restore_backup(self, backup_path: str, drop_existing: bool = False):
        """Restore database from backup."""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        logger.info(f"Restoring backup: {backup_path}")
        
        # Parse database URL
        db_config = self.parse_database_url()
        
        # Drop existing database if requested
        if drop_existing:
            await self._drop_database(db_config)
        
        # Create psql command
        cmd = [
            'psql',
            '--host', str(db_config['host']),
            '--port', str(db_config['port']),
            '--username', db_config['username'],
            '--dbname', 'postgres',  # Connect to postgres db first
            '--no-password',
            '--quiet'
        ]
        
        # Set environment variables
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        try:
            # Read backup file
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rt') as f:
                    backup_content = f.read()
            else:
                with open(backup_file, 'r') as f:
                    backup_content = f.read()
            
            # Run psql
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            stdout, stderr = process.communicate(input=backup_content)
            
            if process.returncode != 0:
                raise Exception(f"psql failed: {stderr}")
            
            logger.info("Backup restored successfully")
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    async def list_backups(self, include_s3: bool = False) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        # Local backups
        for backup_file in self.backup_dir.glob("*.sql*"):
            if backup_file.suffix in ['.sql', '.gz']:
                metadata_file = backup_file.with_suffix('.json')
                
                backup_info = {
                    'name': backup_file.stem,
                    'path': str(backup_file),
                    'size': backup_file.stat().st_size,
                    'created': datetime.fromtimestamp(backup_file.stat().st_mtime),
                    'location': 'local'
                }
                
                # Add metadata if available
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        backup_info.update(metadata)
                
                backups.append(backup_info)
        
        # S3 backups
        if include_s3 and self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.s3_bucket,
                    Prefix='backups/'
                )
                
                for obj in response.get('Contents', []):
                    if obj['Key'].endswith(('.sql', '.sql.gz')):
                        backup_info = {
                            'name': Path(obj['Key']).stem,
                            'path': f"s3://{self.s3_bucket}/{obj['Key']}",
                            'size': obj['Size'],
                            'created': obj['LastModified'],
                            'location': 's3'
                        }
                        backups.append(backup_info)
                        
            except Exception as e:
                logger.warning(f"Failed to list S3 backups: {e}")
        
        # Sort by creation date
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    async def cleanup_old_backups(self, keep_days: int = 7, keep_count: int = 5):
        """Clean up old backup files."""
        logger.info(f"Cleaning up backups older than {keep_days} days")
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        backups = await self.list_backups()
        
        # Keep at least keep_count backups
        backups_to_remove = []
        for i, backup in enumerate(backups):
            if i >= keep_count and backup['created'] < cutoff_date:
                backups_to_remove.append(backup)
        
        for backup in backups_to_remove:
            try:
                backup_path = Path(backup['path'])
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"Removed old backup: {backup_path}")
                    
                    # Remove metadata file
                    metadata_path = backup_path.with_suffix('.json')
                    if metadata_path.exists():
                        metadata_path.unlink()
                        
            except Exception as e:
                logger.warning(f"Failed to remove backup {backup['path']}: {e}")
    
    async def _upload_to_s3(self, backup_path: Path, metadata_path: Path):
        """Upload backup to S3."""
        try:
            s3_key = f"backups/{backup_path.name}"
            
            # Upload backup file
            self.s3_client.upload_file(
                str(backup_path),
                self.s3_bucket,
                s3_key
            )
            
            # Upload metadata file
            self.s3_client.upload_file(
                str(metadata_path),
                self.s3_bucket,
                f"backups/{metadata_path.name}"
            )
            
            logger.info(f"Backup uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            
        except Exception as e:
            logger.warning(f"Failed to upload backup to S3: {e}")
    
    async def _drop_database(self, db_config: Dict[str, str]):
        """Drop existing database."""
        logger.warning(f"Dropping database: {db_config['database']}")
        
        # Connect to postgres database
        conn = await asyncpg.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['username'],
            password=db_config['password'],
            database='postgres'
        )
        
        try:
            # Terminate existing connections
            await conn.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{db_config['database']}'
                AND pid <> pg_backend_pid()
            """)
            
            # Drop database
            await conn.execute(f'DROP DATABASE IF EXISTS "{db_config["database"]}"')
            
        finally:
            await conn.close()
    
    def _get_pg_dump_version(self) -> str:
        """Get pg_dump version."""
        try:
            result = subprocess.run(
                ['pg_dump', '--version'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
    
    async def create_scheduled_backup(self):
        """Create a scheduled backup with retention."""
        try:
            # Create backup
            backup_path = await self.create_backup()
            
            # Clean up old backups
            await self.cleanup_old_backups()
            
            logger.info("Scheduled backup completed successfully")
            return backup_path
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
            raise


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database backup tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create backup
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument("--name", help="Backup name")
    backup_parser.add_argument("--no-compress", action="store_true", help="Don't compress backup")
    backup_parser.add_argument("--no-upload", action="store_true", help="Don't upload to S3")
    
    # Restore backup
    restore_parser = subparsers.add_parser("restore", help="Restore database backup")
    restore_parser.add_argument("backup_path", help="Path to backup file")
    restore_parser.add_argument("--drop", action="store_true", help="Drop existing database")
    
    # List backups
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--include-s3", action="store_true", help="Include S3 backups")
    
    # Cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument("--keep-days", type=int, default=7, help="Days to keep")
    cleanup_parser.add_argument("--keep-count", type=int, default=5, help="Minimum count to keep")
    
    # Scheduled backup
    subparsers.add_parser("scheduled", help="Run scheduled backup")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    backup = DatabaseBackup()
    
    try:
        if args.command == "backup":
            path = await backup.create_backup(
                backup_name=args.name,
                compress=not args.no_compress,
                upload_to_s3=not args.no_upload
            )
            print(f"Backup created: {path}")
            
        elif args.command == "restore":
            await backup.restore_backup(args.backup_path, args.drop)
            print("Restore completed")
            
        elif args.command == "list":
            backups = await backup.list_backups(args.include_s3)
            
            print("\nAvailable backups:")
            for b in backups:
                print(f"  {b['name']} ({b['location']}) - {b['created']} - {b['size']} bytes")
                
        elif args.command == "cleanup":
            await backup.cleanup_old_backups(args.keep_days, args.keep_count)
            print("Cleanup completed")
            
        elif args.command == "scheduled":
            path = await backup.create_scheduled_backup()
            print(f"Scheduled backup created: {path}")
            
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())