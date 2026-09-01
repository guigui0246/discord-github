#!/usr/bin/env python3
"""
Migration management utility

Usage:
    python migrate.py up      # Run all pending migrations
    python migrate.py down    # Rollback last migration
    python migrate.py status  # Show migration status
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def list_migrations():
    """List all migration files"""
    migrations_dir = Path("migrations")
    return sorted(migrations_dir.glob("*.py"))

def run_migrations():
    """Run all pending migrations"""
    migrations = list_migrations()

    print("🔄 Running migrations...")
    for migration_file in migrations:
        if migration_file.name.startswith("__"):
            continue

        print(f"  ↳ {migration_file.name}...", end=" ")

        # Import and run migration
        spec = __import__(f"migrations.{migration_file.stem}", fromlist=[migration_file.stem])
        if hasattr(spec, "up"):
            try:
                spec.up()
                print("✅")
            except Exception as e:
                print(f"❌\n    Error: {e}")
                return False
        else:
            print("⏭️  (no up function)")

    return True

def show_status():
    """Show migration status"""
    migrations = list_migrations()
    print("📋 Migration Status")
    print("==================")

    for migration_file in migrations:
        if migration_file.name.startswith("__"):
            continue
        print(f"  {migration_file.name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [up|down|status]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "up":
        success = run_migrations()
        if success:
            print("✅ All migrations completed successfully")
        else:
            print("❌ Migration failed")
            sys.exit(1)
    elif command == "down":
        print("⚠️  Rollback not yet implemented")
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
