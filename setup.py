#!/usr/bin/env python3
"""One-command project scaffolder for Business Dost AI."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent

FILES = {
    "README.md": """
    # BusinessDostAI

    Business Dost AI - AI Business Copilot for Indian SMEs. Voice-first, WhatsApp-native, zero training required.

    ## One-command setup

    ```bash
    python setup.py
    ```

    This scaffolds a complete FastAPI + Celery + SQLAlchemy + Alembic codebase with:
    - WhatsApp Cloud API webhook handler
    - Whisper transcription service
    - LLM action extraction
    - Business memory system
    - Customer / transaction / task tracking models

    ## Run

    ```bash
    python setup.py
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    docker compose up -d redis
    alembic upgrade head
    uvicorn app.main:app --reload
    ```
    """,
    "requirements.txt": """
    fastapi==0.115.0
    uvicorn[standard]==0.30.6
    sqlalchemy==2.0.35
    alembic==1.13.2
    pydantic==2.9.2
    pydantic-settings==2.5.2
    requests==2.32.3
    celery==5.4.0
    redis==5.0.8
    python-dotenv==1.0.1
    """,
    ".env.example": """
    APP_NAME=Business Dost AI
    DATABASE_URL=sqlite:///./business_dost_ai.db
    REDIS_URL=redis://localhost:6379/0

    WHATSAPP_VERIFY_TOKEN=replace-with-verify-token
    WHATSAPP_ACCESS_TOKEN=replace-with-access-token
    WHATSAPP_PHONE_NUMBER_ID=replace-with-phone-number-id
    WHATSAPP_API_VERSION=v20.0

    OPENAI_API_KEY=replace-with-openai-api-key
    WHISPER_MODEL=whisper-1
    LLM_MODEL=gpt-4o-mini
    """,
    "docker-compose.yml": """
    services:
      redis:
        image: redis:7-alpine
        ports:
          - "6379:6379"
    """,
    "app/__init__.py": """
    """,
    "app/main.py": """
    from contextlib import asynccontextmanager

    from fastapi import FastAPI

    from app.api.webhook import router as webhook_router
    from app.core.config import settings
    from app.core.database import engine
    from app.models.base import Base


    @asynccontextmanager
    async def lifespan(_: FastAPI):
        Base.metadata.create_all(bind=engine)
        yield


    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(webhook_router)


    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}
    """,
    "app/core/__init__.py": """
    """,
    "app/core/config.py": """
    from pydantic_settings import BaseSettings, SettingsConfigDict


    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        app_name: str = "Business Dost AI"
        database_url: str = "sqlite:///./business_dost_ai.db"
        redis_url: str = "redis://localhost:6379/0"

        whatsapp_verify_token: str = "replace-with-verify-token"
        whatsapp_access_token: str = "replace-with-access-token"
        whatsapp_phone_number_id: str = "replace-with-phone-number-id"
        whatsapp_api_version: str = "v20.0"

        openai_api_key: str = "replace-with-openai-api-key"
        whisper_model: str = "whisper-1"
        llm_model: str = "gpt-4o-mini"


    settings = Settings()
    """,
    "app/core/database.py": """
    from collections.abc import Generator

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    from app.core.config import settings


    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


    def get_db() -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    """,
    "app/core/celery_app.py": """
    from celery import Celery

    from app.core.config import settings


    celery_app = Celery("business_dost_ai", broker=settings.redis_url, backend=settings.redis_url)
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
    """,
    "app/models/__init__.py": """
    from app.models.customer import Customer
    from app.models.memory import BusinessMemory
    from app.models.task_item import TaskItem
    from app.models.transaction import Transaction

    __all__ = ["Customer", "Transaction", "TaskItem", "BusinessMemory"]
    """,
    "app/models/base.py": """
    from datetime import datetime, timezone

    from sqlalchemy import DateTime
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


    class Base(DeclarativeBase):
        pass


    class TimestampMixin:
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
        )
    """,
    "app/models/customer.py": """
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.models.base import Base, TimestampMixin


    class Customer(Base, TimestampMixin):
        __tablename__ = "customers"

        id: Mapped[int] = mapped_column(primary_key=True, index=True)
        phone_number: Mapped[str] = mapped_column(String(24), unique=True, index=True)
        name: Mapped[str | None] = mapped_column(String(255), nullable=True)

        transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
        tasks = relationship("TaskItem", back_populates="customer", cascade="all, delete-orphan")
        memories = relationship("BusinessMemory", back_populates="customer", cascade="all, delete-orphan")
    """,
    "app/models/transaction.py": """
    from sqlalchemy import Float, ForeignKey, String
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.models.base import Base, TimestampMixin


    class Transaction(Base, TimestampMixin):
        __tablename__ = "transactions"

        id: Mapped[int] = mapped_column(primary_key=True)
        customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
        amount: Mapped[float] = mapped_column(Float)
        description: Mapped[str] = mapped_column(String(500))

        customer = relationship("Customer", back_populates="transactions")
    """,
    "app/models/task_item.py": """
    from sqlalchemy import Boolean, ForeignKey, String
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.models.base import Base, TimestampMixin


    class TaskItem(Base, TimestampMixin):
        __tablename__ = "tasks"

        id: Mapped[int] = mapped_column(primary_key=True)
        customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
        title: Mapped[str] = mapped_column(String(500))
        done: Mapped[bool] = mapped_column(Boolean, default=False)

        customer = relationship("Customer", back_populates="tasks")
    """,
    "app/models/memory.py": """
    from sqlalchemy import ForeignKey, String, Text
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from app.models.base import Base, TimestampMixin


    class BusinessMemory(Base, TimestampMixin):
        __tablename__ = "business_memories"

        id: Mapped[int] = mapped_column(primary_key=True)
        customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
        key: Mapped[str] = mapped_column(String(255), index=True)
        value: Mapped[str] = mapped_column(Text)

        customer = relationship("Customer", back_populates="memories")
    """,
    "app/schemas/__init__.py": """
    """,
    "app/schemas/whatsapp.py": """
    from pydantic import BaseModel


    class WhatsAppWebhookResponse(BaseModel):
        status: str
        detail: str
    """,
    "app/services/__init__.py": """
    """,
    "app/services/whisper_service.py": """
    import tempfile
    from pathlib import Path

    import requests

    from app.core.config import settings


    class WhisperService:
        '''Whisper API integration for voice note transcription.'''

        def transcribe_from_url(self, media_url: str, media_token: str | None = None) -> str:
            token = media_token or settings.whatsapp_access_token
            headers = {"Authorization": " ".join(["Bearer", token])} if token else {}
            response = requests.get(media_url, headers=headers, timeout=30)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                temp_file.write(response.content)
                temp_path = Path(temp_file.name)

            try:
                with temp_path.open("rb") as audio_stream:
                    files = {"file": audio_stream}
                    data = {"model": settings.whisper_model}
                    whisper_headers = {"Authorization": " ".join(["Bearer", settings.openai_api_key])}
                    whisper_response = requests.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers=whisper_headers,
                        data=data,
                        files=files,
                        timeout=60,
                    )
                    whisper_response.raise_for_status()
                    return whisper_response.json().get("text", "")
            finally:
                temp_path.unlink(missing_ok=True)
    """,
    "app/services/llm_service.py": """
    import json

    import requests

    from app.core.config import settings


    class LLMService:
        '''Extract action items from transcription using LLM.'''

        def extract_actions(self, transcript: str) -> list[str]:
            system_prompt = (
                "You are an assistant for Indian SME owners. "
                "Extract actionable business todo items as a JSON array of strings."
            )
            payload = {
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }
            headers = {
                "Authorization": " ".join(["Bearer", settings.openai_api_key]),
                "Content-Type": "application/json",
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            actions = parsed.get("actions", [])
            return [a for a in actions if isinstance(a, str) and a.strip()]
    """,
    "app/services/memory_service.py": """
    from sqlalchemy.orm import Session

    from app.models.memory import BusinessMemory


    class MemoryService:
        '''Simple customer-level business memory system.'''

        def upsert(self, db: Session, customer_id: int, key: str, value: str) -> BusinessMemory:
            memory = (
                db.query(BusinessMemory)
                .filter(BusinessMemory.customer_id == customer_id, BusinessMemory.key == key)
                .one_or_none()
            )
            if memory is None:
                memory = BusinessMemory(customer_id=customer_id, key=key, value=value)
                db.add(memory)
            else:
                memory.value = value
            db.commit()
            db.refresh(memory)
            return memory
    """,
    "app/services/whatsapp_service.py": """
    import requests

    from app.core.config import settings


    class WhatsAppService:
        '''WhatsApp Cloud API integration for outbound messaging.'''

        @property
        def _messages_url(self) -> str:
            return (
                f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
                f"{settings.whatsapp_phone_number_id}/messages"
            )

        def get_media_download_url(self, media_id: str) -> str:
            media_lookup_url = f"https://graph.facebook.com/{settings.whatsapp_api_version}/{media_id}"
            headers = {"Authorization": " ".join(["Bearer", settings.whatsapp_access_token])}
            response = requests.get(media_lookup_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()["url"]

        def send_text(self, to_phone_number: str, text: str) -> None:
            headers = {
                "Authorization": " ".join(["Bearer", settings.whatsapp_access_token]),
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone_number,
                "type": "text",
                "text": {"body": text},
            }
            response = requests.post(self._messages_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
    """,
    "app/workers/__init__.py": """
    """,
    "app/workers/tasks.py": """
    from app.core.celery_app import celery_app
    from app.core.database import SessionLocal
    from app.models.customer import Customer
    from app.models.task_item import TaskItem
    from app.services.llm_service import LLMService
    from app.services.memory_service import MemoryService
    from app.services.whisper_service import WhisperService
    from app.services.whatsapp_service import WhatsAppService


    @celery_app.task(name="process_whatsapp_voice_note")
    def process_whatsapp_voice_note(customer_phone: str, media_id: str) -> dict[str, object]:
        db = SessionLocal()
        whisper_service = WhisperService()
        llm_service = LLMService()
        whatsapp_service = WhatsAppService()
        memory_service = MemoryService()

        try:
            customer = db.query(Customer).filter(Customer.phone_number == customer_phone).one_or_none()
            if customer is None:
                customer = Customer(phone_number=customer_phone)
                db.add(customer)
                db.commit()
                db.refresh(customer)

            media_url = whatsapp_service.get_media_download_url(media_id)
            transcript = whisper_service.transcribe_from_url(media_url)
            actions = llm_service.extract_actions(transcript)

            for action in actions:
                db.add(TaskItem(customer_id=customer.id, title=action, done=False))
            db.commit()

            memory_service.upsert(db, customer.id, "last_transcript", transcript)

            bullet_points = "\\n".join(f"- {action}" for action in actions) or "- No clear actions found"
            whatsapp_service.send_text(
                customer_phone,
                f"Here are your extracted actions:\\n{bullet_points}",
            )

            return {"status": "processed", "actions": actions}
        finally:
            db.close()
    """,
    "app/api/__init__.py": """
    """,
    "app/api/webhook.py": """
    from fastapi import APIRouter, HTTPException, Query

    from app.core.config import settings
    from app.schemas.whatsapp import WhatsAppWebhookResponse
    from app.workers.tasks import process_whatsapp_voice_note

    router = APIRouter(prefix="/webhook", tags=["whatsapp"])


    @router.get("")
    def verify_webhook(
        mode: str = Query(alias="hub.mode"),
        token: str = Query(alias="hub.verify_token"),
        challenge: str = Query(alias="hub.challenge"),
    ) -> str:
        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            return challenge
        raise HTTPException(status_code=403, detail="Webhook verification failed")


    @router.post("", response_model=WhatsAppWebhookResponse)
    def receive_webhook(payload: dict) -> WhatsAppWebhookResponse:
        entries = payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                contacts = value.get("contacts", [])
                phone_number = contacts[0].get("wa_id") if contacts else None
                for message in messages:
                    if message.get("type") == "audio" and phone_number:
                        media_id = message.get("audio", {}).get("id")
                        if media_id:
                            process_whatsapp_voice_note.delay(phone_number, media_id)

        return WhatsAppWebhookResponse(status="accepted", detail="Webhook processed")
    """,
    "alembic.ini": """
    [alembic]
    script_location = alembic
    sqlalchemy.url = sqlite:///./business_dost_ai.db

    [loggers]
    keys = root,sqlalchemy,alembic

    [handlers]
    keys = console

    [formatters]
    keys = generic

    [logger_root]
    level = WARN
    handlers = console

    [logger_sqlalchemy]
    level = WARN
    handlers =
    qualname = sqlalchemy.engine

    [logger_alembic]
    level = INFO
    handlers =
    qualname = alembic

    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = generic

    [formatter_generic]
    format = %(levelname)-5.5s [%(name)s] %(message)s
    """,
    "alembic/env.py": """
    from logging.config import fileConfig

    from alembic import context
    from sqlalchemy import engine_from_config, pool

    from app.models.base import Base
    from app.models import customer, memory, task_item, transaction

    config = context.config

    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    target_metadata = Base.metadata


    def run_migrations_offline() -> None:
        url = config.get_main_option("sqlalchemy.url")
        context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

        with context.begin_transaction():
            context.run_migrations()


    def run_migrations_online() -> None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)

            with context.begin_transaction():
                context.run_migrations()


    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
    """,
    "alembic/script.py.mako": """
    \"\"\"${message}\"\"\"

    revision = ${repr(up_revision)}
    down_revision = ${repr(down_revision)}
    branch_labels = ${repr(branch_labels)}
    depends_on = ${repr(depends_on)}


    def upgrade() -> None:
        ${upgrades if upgrades else \"pass\"}


    def downgrade() -> None:
        ${downgrades if downgrades else \"pass\"}
    """,
    "alembic/versions/0001_initial.py": """
    \"\"\"initial schema\"\"\"

    from alembic import op
    import sqlalchemy as sa


    revision = "0001_initial"
    down_revision = None
    branch_labels = None
    depends_on = None


    def upgrade() -> None:
        op.create_table(
            "customers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("phone_number", sa.String(length=24), nullable=False, unique=True),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_table(
            "transactions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        )
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        )
        op.create_table(
            "business_memories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("key", sa.String(length=255), nullable=False),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        )
        op.create_index("ix_customers_phone_number", "customers", ["phone_number"], unique=True)
        op.create_index("ix_tasks_customer_id", "tasks", ["customer_id"], unique=False)
        op.create_index("ix_transactions_customer_id", "transactions", ["customer_id"], unique=False)
        op.create_index("ix_business_memories_customer_id", "business_memories", ["customer_id"], unique=False)
        op.create_index("ix_business_memories_key", "business_memories", ["key"], unique=False)


    def downgrade() -> None:
        op.drop_index("ix_business_memories_key", table_name="business_memories")
        op.drop_index("ix_business_memories_customer_id", table_name="business_memories")
        op.drop_index("ix_transactions_customer_id", table_name="transactions")
        op.drop_index("ix_tasks_customer_id", table_name="tasks")
        op.drop_index("ix_customers_phone_number", table_name="customers")
        op.drop_table("business_memories")
        op.drop_table("tasks")
        op.drop_table("transactions")
        op.drop_table("customers")
    """,
}


def main() -> None:
    created_files = []
    for relative_path, content in FILES.items():
        target = ROOT / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dedent(content).lstrip("\n"), encoding="utf-8")
        created_files.append(str(relative_path))

    print("Business Dost AI scaffold generated successfully.")
    print(f"Created/updated {len(created_files)} files.")


if __name__ == "__main__":
    main()
