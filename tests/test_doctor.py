import asyncio
from unittest.mock import AsyncMock

import pytest

from app import doctor
from app.doctor import main


@pytest.fixture
def set_valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db.project.supabase.com:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")


def test_no_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    assert main() == 1
    output = capsys.readouterr().out
    assert ".env missing" in output


def test_placeholder_database_url(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "<SERVICE_KEY>")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@db.example.com:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    assert main() == 1
    output = capsys.readouterr().out
    assert "AI_SERVICE_KEY is empty or has a placeholder" in output


def test_dev_ai_service_key_is_not_a_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_SERVICE_KEY", "dev-secret-key-123")

    assert doctor.check_required_vars().ok is True


def test_database_check_uses_shared_probe(
    monkeypatch: pytest.MonkeyPatch,
    set_valid_env: None,
) -> None:
    database_url = "postgresql+asyncpg://user:password@db.example.test:5432/ai"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("HEALTH_TIMEOUT_SECONDS", "15")
    settings = doctor._settings_or_load(None)
    database_probe = AsyncMock()
    monkeypatch.setattr(doctor, "check_database_connection", database_probe)

    check = asyncio.run(doctor._check_database_async(settings))

    assert check.ok is True
    database_probe.assert_awaited_once_with(
        database_url,
        timeout_seconds=15,
    )


def test_uses_asyncpg_url(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:postgres@db.project.supabase.com:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    assert main() == 1
    output = capsys.readouterr().out
    assert "Use postgresql+asyncpg:// not postgresql://" in output


def test_unencoded_password_is_flagged(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:weird@pass@db.project.supabase.com:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    assert main() == 1
    output = capsys.readouterr().out
    assert "Password has '@'" in output


def test_supabase_pooler_url_is_required(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db.project.supabase.com:6543/postgres?ssl=require")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    assert main() == 1
    output = capsys.readouterr().out
    assert "Use the Session pooler URL" in output


def test_celery_requires_ssl_cert_reqs(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db.project.supabase.com:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    assert main() == 1
    output = capsys.readouterr().out
    assert "ssl_cert_reqs=required" in output


def test_password_never_printed(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:super@secret!@db.project.supabase.com:5432/postgres")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    assert main() == 1
    output = capsys.readouterr().out
    assert "super@secret!" not in output
    assert "****" in output


def test_missing_variable_reports_once_and_skips_dependents(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "AI_SERVICE_KEY=service-key\n"
        "DATABASE_URL=\nREDIS_URL=\nCELERY_BROKER_URL=\nCELERY_RESULT_BACKEND=\n"
        "MODEL_SERVER_URL=http://localhost:11434\nLLM_MODEL=qwen3.5:4b\nLLM_THINK=false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)

    assert main() == 1
    output = capsys.readouterr().out
    assert output.count("FAIL: DATABASE_URL") == 1
    assert "SKIP: DATABASE_URL is missing" in output
    assert "SKIP: REDIS_URL is missing" in output


def test_redis_tls_check_fails_when_urls_empty(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "AI_SERVICE_KEY=service-key\n"
        "DATABASE_URL=postgresql+asyncpg://localhost/test\n"
        "REDIS_URL=\n"
        "CELERY_BROKER_URL=\n"
        "CELERY_RESULT_BACKEND=\n"
        "MODEL_SERVER_URL=http://localhost:11434\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)

    check = doctor.check_redis_urls()

    assert check.status == "FAIL"
    assert "REDIS_URL" in check.message or "CELERY_BROKER_URL" in check.message or "CELERY_RESULT_BACKEND" in check.message


def test_all_checks_mocked_ok(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AI_SERVICE_KEY=service-key\n", encoding="utf-8")
    monkeypatch.setenv("AI_SERVICE_KEY", "service-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@aws-0-us-east-1.pooler.supabase.com:5432/postgres?ssl=require")
    monkeypatch.setenv("REDIS_URL", "rediss://:password@host.upstash.io:6379")
    monkeypatch.setenv("CELERY_BROKER_URL", "rediss://:password@host.upstash.io:6379/1?ssl_cert_reqs=required")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "rediss://:password@host.upstash.io:6379/2?ssl_cert_reqs=required")
    monkeypatch.setenv("MODEL_SERVER_URL", "http://localhost:11434")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:4b")
    monkeypatch.setenv("LLM_THINK", "false")

    monkeypatch.setattr(doctor, "check_database", lambda settings=None: doctor.DoctorCheck(True, "ok"))
    monkeypatch.setattr(doctor, "check_redis", lambda settings=None: doctor.DoctorCheck(True, "ok"))
    monkeypatch.setattr(doctor, "check_model", lambda settings=None: doctor.DoctorCheck(True, "ok"))

    assert main() == 0
    output = capsys.readouterr().out
    assert "OK" in output
