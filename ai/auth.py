import hashlib
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Iterator

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, Field, field_validator


load_dotenv()

DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite").lower()
SQLITE_PATH = os.getenv("SQLITE_PATH", "chat_history.db")

# Token login berlaku selama 24 jam.
TOKEN_TTL = 24 * 60 * 60

hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
)

# Digunakan saat email tidak ditemukan, agar proses
# pengecekan tetap menjalankan verifikasi password.
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))

bearer = HTTPBearer(auto_error=False)

auth_router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


def _connect() -> Any:
    """Mengikuti konfigurasi database proyek."""

    if DB_CONNECTION == "mysql":
        import mysql.connector

        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "rag_karir"),
        )

    if DB_CONNECTION != "sqlite":
        raise ValueError(
            "DB_CONNECTION harus sqlite atau mysql"
        )

    os.makedirs(
        os.path.dirname(SQLITE_PATH) or ".",
        exist_ok=True,
    )

    conn = sqlite3.connect(SQLITE_PATH, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def _sql(
    cur: Any,
    query: str,
    params: tuple = (),
) -> None:
    if DB_CONNECTION == "mysql":
        query = query.replace("?", "%s")

    cur.execute(query, params)


@contextmanager
def _db(write: bool = False) -> Iterator[Any]:
    conn = _connect()
    cur = conn.cursor()

    try:
        if write:
            cur.execute(
                "START TRANSACTION"
                if DB_CONNECTION == "mysql"
                else "BEGIN IMMEDIATE"
            )

        yield cur
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


def init_auth_db() -> None:
    """Membuat tabel akun dan sesi login."""

    suffix = (
        " ENGINE=InnoDB"
        if DB_CONNECTION == "mysql"
        else ""
    )

    tables = [
        """
        CREATE TABLE IF NOT EXISTS app_users (
            id VARCHAR(32) PRIMARY KEY,
            name VARCHAR(80) NOT NULL,
            email VARCHAR(254) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at BIGINT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS app_auth_sessions (
            token_hash VARCHAR(64) PRIMARY KEY,
            user_id VARCHAR(32) NOT NULL,
            expires_at BIGINT NOT NULL,
            FOREIGN KEY (user_id)
                REFERENCES app_users(id)
                ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS app_auth_limits (
            bucket VARCHAR(64) PRIMARY KEY,
            attempts INTEGER NOT NULL,
            reset_at BIGINT NOT NULL
        )
        """,
    ]

    with _db() as cur:
        for query in tables:
            cur.execute(query + suffix)


def _rate_limit(
    request: Request,
    action: str,
    email: str = "",
) -> None:
    """Membatasi percobaan autentikasi selama 10 menit."""

    ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    bucket = hashlib.sha256(
        f"{action}:{ip}:{email}".encode()
    ).hexdigest()

    now = int(time.time())

    # Login: maksimal 10 percobaan per kombinasi IP/email.
    # Register: maksimal 30 percobaan per IP.
    limit = 10 if action == "login" else 30

    with _db(write=True) as cur:
        _sql(
            cur,
            """
            DELETE FROM app_auth_limits
            WHERE reset_at <= ?
            """,
            (now,),
        )

        insert = (
            "INSERT IGNORE"
            if DB_CONNECTION == "mysql"
            else "INSERT OR IGNORE"
        )

        _sql(
            cur,
            f"""
            {insert} INTO app_auth_limits
                (bucket, attempts, reset_at)
            VALUES (?, 0, ?)
            """,
            (bucket, now + 600),
        )

        suffix = (
            " FOR UPDATE"
            if DB_CONNECTION == "mysql"
            else ""
        )

        _sql(
            cur,
            """
            SELECT attempts, reset_at
            FROM app_auth_limits
            WHERE bucket = ?
            """ + suffix,
            (bucket,),
        )

        attempts, reset_at = cur.fetchone()

        if attempts >= limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Terlalu banyak percobaan. "
                    "Coba lagi nanti."
                ),
                headers={
                    "Retry-After": str(
                        max(1, reset_at - now)
                    )
                },
            )

        _sql(
            cur,
            """
            UPDATE app_auth_limits
            SET attempts = attempts + 1
            WHERE bucket = ?
            """,
            (bucket,),
        )


class LoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=254,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        value = value.strip().casefold()

        if not re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+",
            value,
        ):
            raise ValueError("Format email tidak valid")

        return value


class RegisterRequest(LoginRequest):
    name: str = Field(
        min_length=2,
        max_length=80,
    )

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Nama minimal 2 karakter")

        return value


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer
    ),
) -> dict:
    """Mengambil akun berdasarkan token login."""

    error = HTTPException(
        status_code=401,
        detail="Silakan login terlebih dahulu.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
    ):
        raise error

    token = credentials.credentials

    if not 32 <= len(token) <= 128:
        raise error

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    with _db() as cur:
        _sql(
            cur,
            """
            SELECT u.id, u.name, u.email, u.created_at
            FROM app_auth_sessions s
            JOIN app_users u ON u.id = s.user_id
            WHERE s.token_hash = ?
              AND s.expires_at > ?
            """,
            (token_hash, int(time.time())),
        )

        row = cur.fetchone()

    if row is None:
        raise error

    return dict(
        zip(
            ("id", "name", "email", "created_at"),
            row,
        )
    )


@auth_router.post("/register", status_code=201)
def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
):
    _rate_limit(request, "register")

    user_id = secrets.token_hex(16)
    created_at = int(time.time())
    password_hash = hasher.hash(data.password)

    try:
        with _db(write=True) as cur:
            _sql(
                cur,
                """
                INSERT INTO app_users
                    (id, name, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    data.name,
                    data.email,
                    password_hash,
                    created_at,
                ),
            )

    except Exception as error:
        duplicate = (
            isinstance(error, sqlite3.IntegrityError)
            or getattr(error, "errno", None) == 1062
        )

        if duplicate:
            raise HTTPException(
                status_code=409,
                detail="Email sudah terdaftar.",
            ) from error

        raise

    response.headers["Cache-Control"] = "no-store"

    return {
        "id": user_id,
        "name": data.name,
        "email": data.email,
        "created_at": created_at,
    }


@auth_router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
):
    _rate_limit(request, "login", data.email)

    with _db() as cur:
        _sql(
            cur,
            """
            SELECT id, name, email, created_at, password_hash
            FROM app_users
            WHERE email = ?
            """,
            (data.email,),
        )

        row = cur.fetchone()

    try:
        valid = hasher.verify(
            row[4] if row else DUMMY_HASH,
            data.password,
        )
    except (VerificationError, InvalidHashError):
        valid = False

    if row is None or not valid:
        raise HTTPException(
            status_code=401,
            detail="Email atau password salah.",
        )

    token = secrets.token_urlsafe(32)

    # Database menyimpan hash token login.
    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    now = int(time.time())
    expires_at = now + TOKEN_TTL

    with _db(write=True) as cur:
        _sql(
            cur,
            """
            DELETE FROM app_auth_sessions
            WHERE expires_at <= ?
            """,
            (now,),
        )

        _sql(
            cur,
            """
            INSERT INTO app_auth_sessions
                (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, row[0], expires_at),
        )

    response.headers["Cache-Control"] = "no-store"

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "user": dict(
            zip(
                ("id", "name", "email", "created_at"),
                row[:4],
            )
        ),
    }


@auth_router.get("/me")
def me(
    response: Response,
    user: dict = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store"
    return user


@auth_router.post("/logout", status_code=204)
def logout(
    user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer
    ),
):
    if credentials is not None:
        token_hash = hashlib.sha256(
            credentials.credentials.encode()
        ).hexdigest()

        with _db(write=True) as cur:
            _sql(
                cur,
                """
                DELETE FROM app_auth_sessions
                WHERE token_hash = ?
                  AND user_id = ?
                """,
                (token_hash, user["id"]),
            )

    return Response(
        status_code=204,
        headers={"Cache-Control": "no-store"},
    )