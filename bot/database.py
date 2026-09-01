"""
Database models and initialization
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import Config

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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    last_sync = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="pull_requests")
    comments = relationship("Comment", back_populates="pull_request")


class Comment(Base):
    """Comment synchronization tracking"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id"))
    github_comment_id = Column(String, unique=True, index=True)
    discord_message_id = Column(String)
    author = Column(String)
    source = Column(String)  # github or discord
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
