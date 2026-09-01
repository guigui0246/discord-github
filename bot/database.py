"""
Database models and initialization
"""
import os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from bot.config import Config

# Create database directory if using SQLite
if "sqlite:///" in Config.DATABASE_URL:
    try:
        # SQLAlchemy treats sqlite:/// paths without a fourth slash as relative.
        database_path = Config.DATABASE_URL[len("sqlite:///"):]
        db_dir = Path(database_path).parent
        if str(db_dir) != ".":
            db_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(db_dir, 0o777)
            print(f"✅ Database directory created: {db_dir}")
    except Exception as e:
        print(f"⚠️ Warning creating database directory: {e}")

# Create database engine
engine = create_engine(Config.DATABASE_URL, echo=Config.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class GitHubInstallation(Base):
    """GitHub App installation"""
    __tablename__ = "github_installations"

    id = Column(Integer, primary_key=True)
    installation_id = Column(String, unique=True, index=True)
    account_name = Column(String)
    account_type = Column(String)  # User or Organization
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    repositories = relationship("Repository", back_populates="installation")


class Repository(Base):
    """GitHub repository configuration"""
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    installation_id = Column(Integer, ForeignKey("github_installations.id"))
    repo_owner = Column(String)
    repo_name = Column(String)
    repo_full_name = Column(String, unique=True, index=True)
    discord_category_id = Column(String)
    webhook_id = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    installation = relationship("GitHubInstallation", back_populates="repositories")
    pull_requests = relationship("PullRequest", back_populates="repository")


class PullRequest(Base):
    """Pull request and Discord channel mapping"""
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    pr_number = Column(Integer)
    pr_title = Column(String)
    discord_channel_id = Column(String, unique=True, index=True)
    github_url = Column(String)
    author = Column(String)
    status = Column(String)  # open, closed, merged
    last_sync = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    comments = relationship("Comment", back_populates="pull_request")


class Issue(Base):
    """GitHub issue and Discord channel mapping"""
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    issue_number = Column(Integer)
    issue_title = Column(String)
    discord_channel_id = Column(String, unique=True, index=True)
    github_url = Column(String)
    author = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository")


class Comment(Base):
    """Comment synchronization tracking"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"))
    github_comment_id = Column(String, unique=True, index=True)
    discord_message_id = Column(String)
    author = Column(String)
    source = Column(String)  # github or discord
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    pull_request = relationship("PullRequest", back_populates="comments")


class WorkflowRun(Base):
    """GitHub Actions workflow run tracking"""
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    workflow_run_id = Column(String, unique=True, index=True)
    workflow_name = Column(String)
    branch = Column(String)
    status = Column(String)  # queued, in_progress, completed
    conclusion = Column(String)  # success, failure, neutral, cancelled
    discord_message_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


def init_db():
    """Initialize database with all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
