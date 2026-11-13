import json
import logging
import secrets
import time
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from auth import (
    DB_CONNECTION,
    _db,
    _sql,
    get_current_user,
)
from chat_quota import ChatQuota


logger = logging.getLogger(__name__)


def init_chat_db():
    suffix = (
        " ENGINE=InnoDB"
        if DB_CONNECTION == "mysql"
        else ""
    )

    with _db() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_conversations (
                id VARCHAR(32) PRIMARY KEY,
                user_id VARCHAR(32) NOT NULL,
                title VARCHAR(120) NOT NULL,
                created_at DOUBLE NOT NULL,
                updated_at DOUBLE NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES app_users(id)
                    ON DELETE CASCADE
            )
            """ + suffix
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS app_chat_messages (
                id VARCHAR(32) PRIMARY KEY,
                conversation_id VARCHAR(32) NOT NULL,
                position INTEGER NOT NULL,
                role VARCHAR(16) NOT NULL,
                content LONGTEXT NOT NULL,
                sources LONGTEXT NOT NULL,
                created_at DOUBLE NOT NULL,
                UNIQUE (conversation_id, position),
                FOREIGN KEY (conversation_id)
                    REFERENCES app_conversations(id)
                    ON DELETE CASCADE
            )
            """ + suffix
        )


def owned(cur, user_id, conversation_id):
    """Mengambil percakapan yang dimiliki akun ini."""

    _sql(
        cur,
        """
        SELECT id, title, created_at, updated_at
        FROM app_conversations
        WHERE id = ? AND user_id = ?
        """,
        (conversation_id, user_id),
    )

    row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Percakapan tidak ditemukan.",
        )

    return dict(
        zip(
            ("id", "title", "created_at", "updated_at"),
            row,
        )
    )


def messages(cur, conversation_id, history_only=False):
    query = """
        SELECT id, role, content, sources, created_at
        FROM app_chat_messages
        WHERE conversation_id = ?
        ORDER BY position DESC
    """

    # Hanya 20 pesan terakhir yang dikirim sebagai konteks AI.
    # Riwayat yang dibuka pengguna tetap memuat seluruh pesan.
    if history_only:
        query += " LIMIT 20"

    _sql(cur, query, (conversation_id,))

    result = []

    for row in reversed(cur.fetchall()):
        result.append({
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "sources": json.loads(row[3]),
            "created_at": row[4],
        })

    return result


class ConversationInput(BaseModel):
    title: str = Field(
        default="Percakapan baru",
        min_length=1,
        max_length=120,
    )

    @field_validator("title")
    @classmethod
    def clean_title(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Judul tidak boleh kosong")

        return value


class ChatInput(BaseModel):
    conversation_id: str = Field(
        min_length=32,
        max_length=32,
    )

    message: str = Field(
        min_length=1,
        max_length=6000,
    )

    @field_validator("message")
    @classmethod
    def clean_message(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Pesan tidak boleh kosong")

        return value


def create_chat_router(generate_reply: Callable):
    api = APIRouter(tags=["Chat"])

    quota = ChatQuota(
        limit=100,
        cooldown_seconds=600,
        lease_seconds=600,
    )

    def view_quota(value):
        return {
            **value,
            "server_time": time.time(),
        }

    @api.get("/quota")
    def get_quota(
        user: dict = Depends(get_current_user),
    ):
        return view_quota(
            quota.status(user["id"])
        )

    @api.get("/conversations")
    def list_conversations(
        offset: int = Query(default=0, ge=0),
        q: str = Query(default="", max_length=100),
        user: dict = Depends(get_current_user),
    ):
        with _db() as cur:
            _sql(
                cur,
                """
                SELECT id, title, created_at, updated_at
                FROM app_conversations
                WHERE user_id = ?
                  AND LOWER(title) LIKE ?
                ORDER BY updated_at DESC, id DESC
                LIMIT 51 OFFSET ?
                """,
                (
                    user["id"],
                    "%" + q.lower() + "%",
                    offset,
                ),
            )

            rows = cur.fetchall()

        return {
            "items": [
                dict(
                    zip(
                        (
                            "id",
                            "title",
                            "created_at",
                            "updated_at",
                        ),
                        row,
                    )
                )
                for row in rows[:50]
            ],
            "has_more": len(rows) > 50,
        }

    @api.post("/conversations", status_code=201)
    def create_conversation(
        data: ConversationInput,
        user: dict = Depends(get_current_user),
    ):
        conversation_id = secrets.token_hex(16)
        now = time.time()

        with _db(write=True) as cur:
            _sql(
                cur,
                """
                INSERT INTO app_conversations
                    (id, user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    user["id"],
                    data.title,
                    now,
                    now,
                ),
            )

        return {
            "id": conversation_id,
            "title": data.title,
            "created_at": now,
            "updated_at": now,
        }

    @api.get("/conversations/{cid}")
    def read_conversation(
        cid: str,
        user: dict = Depends(get_current_user),
    ):
        with _db() as cur:
            conversation = owned(
                cur, user["id"], cid
            )
            items = messages(cur, cid)

        return {
            "conversation": conversation,
            "messages": items,
        }

    @api.patch("/conversations/{cid}")
    def rename_conversation(
        cid: str,
        data: ConversationInput,
        user: dict = Depends(get_current_user),
    ):
        with _db(write=True) as cur:
            owned(cur, user["id"], cid)

            _sql(
                cur,
                """
                UPDATE app_conversations
                SET title = ?
                WHERE id = ? AND user_id = ?
                """,
                (data.title, cid, user["id"]),
            )

            return owned(cur, user["id"], cid)

    @api.delete(
        "/conversations/{cid}",
        status_code=204,
    )
    def delete_conversation(
        cid: str,
        user: dict = Depends(get_current_user),
    ):
        with _db(write=True) as cur:
            owned(cur, user["id"], cid)

            _sql(
                cur,
                """
                DELETE FROM app_conversations
                WHERE id = ? AND user_id = ?
                """,
                (cid, user["id"]),
            )

    @api.post("/chat")
    def send_chat(
        data: ChatInput,
        user: dict = Depends(get_current_user),
    ):
        reservation = quota.reserve(user["id"])
        finished = False

        try:
            with _db() as cur:
                owned(
                    cur,
                    user["id"],
                    data.conversation_id,
                )

                history = [
                    {
                        "role": (
                            "model"
                            if item["role"] == "assistant"
                            else "user"
                        ),
                        "content": item["content"],
                    }
                    for item in messages(
                        cur,
                        data.conversation_id,
                        history_only=True,
                    )
                ]

            if history and history[0]["role"] == "model":
                history = history[1:]

            result = generate_reply(
                history,
                data.message,
            )

            if not result.get("reply", "").strip():
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Layanan AI belum memberikan jawaban. "
                        "Coba lagi nanti."
                    ),
                )

            now = time.time()

            pair = [
                {
                    "id": secrets.token_hex(16),
                    "role": "user",
                    "content": data.message,
                    "sources": [],
                    "created_at": now,
                },
                {
                    "id": secrets.token_hex(16),
                    "role": "assistant",
                    "content": result["reply"],
                    "sources": result.get("sources", []),
                    "created_at": now,
                },
            ]

            def persist(cur):
                """
                Dipanggil di dalam transaksi kuota.
                Jika salah satu penulisan gagal,
                seluruh transaksi dibatalkan.
                """

                owned(
                    cur,
                    user["id"],
                    data.conversation_id,
                )

                _sql(
                    cur,
                    """
                    SELECT COUNT(*)
                    FROM app_chat_messages
                    WHERE conversation_id = ?
                    """,
                    (data.conversation_id,),
                )

                position = cur.fetchone()[0]

                for index, item in enumerate(
                    pair,
                    start=1,
                ):
                    _sql(
                        cur,
                        """
                        INSERT INTO app_chat_messages
                            (
                                id,
                                conversation_id,
                                position,
                                role,
                                content,
                                sources,
                                created_at
                            )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item["id"],
                            data.conversation_id,
                            position + index,
                            item["role"],
                            item["content"],
                            json.dumps(
                                item["sources"],
                                ensure_ascii=False,
                            ),
                            now,
                        ),
                    )

                _sql(
                    cur,
                    """
                    UPDATE app_conversations
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (now, data.conversation_id),
                )

            remaining = quota.complete(
                user["id"],
                reservation,
                persist=persist,
            )

            finished = True

            return {
                "messages": pair,
                "quota": view_quota(remaining),
            }

        finally:
            if not finished:
                try:
                    quota.cancel(
                        user["id"],
                        reservation,
                    )
                except Exception:
                    logger.exception(
                        "Gagal melepas reservasi kuota"
                    )

    return api