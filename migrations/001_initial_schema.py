"""
Database migration: Initial schema
"""
from database import init_db

def up():
    """Run migration"""
    init_db()
    print("✅ Initial schema created")

def down():
    """Rollback migration"""
    # For SQLite, we would need to drop tables
    # This is a placeholder for future more complex migrations
    print("⚠️ Rollback not implemented for initial migration")

if __name__ == "__main__":
    up()
