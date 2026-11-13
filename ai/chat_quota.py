import math
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager

from fastapi import HTTPException


class ChatQuota:
    def __init__(
        self,
        limit=100,
        cooldown_seconds=600,
        lease_seconds=300,
    ):
        self.limit = limit
        self.cooldown = cooldown_seconds

        # Batas waktu penanda permintaan yang sedang berjalan.
        self.lease = lease_seconds

        self.mysql = (
            os.getenv("DB_CONNECTION", "sqlite").lower() == "mysql"
        )

        self.path = os.getenv(
            "SQLITE_PATH",
            "chat_history.db",
        )

        if not self.mysql:
            os.makedirs(
                os.path.dirname(self.path) or ".",
                exist_ok=True,
            )

        conn = self._connect()

        try:
            cur = conn.cursor()

            query = """
                CREATE TABLE IF NOT EXISTS user_chat_quotas (
                    user_id VARCHAR(64) PRIMARY KEY,
                    used INTEGER NOT NULL DEFAULT 0,
                    reset_at DOUBLE NOT NULL DEFAULT 0,
                    active_request VARCHAR(64),
                    active_until DOUBLE NOT NULL DEFAULT 0
                )
            """

            if self.mysql:
                query += " ENGINE=InnoDB"

            cur.execute(query)
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def _connect(self):
        if self.mysql:
            import mysql.connector

            return mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "rag_karir"),
            )

        return sqlite3.connect(self.path, timeout=30)

    def _sql(self, cur, query, values=()):
        if self.mysql:
            query = query.replace("?", "%s")

        cur.execute(query, values)

    @contextmanager
    def _locked(self, user_id):
        """Baca dan ubah kuota dalam satu transaksi."""

        conn = self._connect()
        cur = conn.cursor()

        try:
            if self.mysql:
                cur.execute("START TRANSACTION")
            else:
                cur.execute("BEGIN IMMEDIATE")

            insert = (
                "INSERT IGNORE"
                if self.mysql
                else "INSERT OR IGNORE"
            )

            self._sql(
                cur,
                f"""
                    {insert} INTO user_chat_quotas (user_id)
                    VALUES (?)
                """,
                (user_id,),
            )

            suffix = " FOR UPDATE" if self.mysql else ""

            self._sql(
                cur,
                """
                    SELECT used, reset_at,
                           active_request, active_until
                    FROM user_chat_quotas
                    WHERE user_id = ?
                """ + suffix,
                (user_id,),
            )

            used, reset_at, active, active_until = cur.fetchone()
            now = time.time()

            # Isi ulang setelah cooldown selesai.
            if reset_at and now >= reset_at:
                used = 0
                reset_at = 0

            # Lepaskan penanda permintaan yang kedaluwarsa.
            if active and now >= active_until:
                active = None
                active_until = 0

            self._sql(
                cur,
                """
                    UPDATE user_chat_quotas
                    SET used = ?, reset_at = ?,
                        active_request = ?, active_until = ?
                    WHERE user_id = ?
                """,
                (
                    used,
                    reset_at,
                    active,
                    active_until,
                    user_id,
                ),
            )

            yield cur, (
                used,
                reset_at,
                active,
                active_until,
            ), now

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cur.close()
            conn.close()

    def _view(self, used, reset_at, now):
        remaining = max(0, self.limit - used)

        return {
            "server_time": now,
            "limit": self.limit,
            "used": used,
            "remaining": remaining,
            "remaining_percent": round(
                remaining / self.limit * 100
            ),
            "blocked": remaining == 0,
            "reset_at": reset_at or None,
            "retry_after": (
                max(0, math.ceil(reset_at - now))
                if reset_at
                else 0
            ),
        }

    def status(self, user_id):
        """Mengambil sisa kuota untuk ditampilkan di UI."""

        with self._locked(user_id) as (_, row, now):
            return self._view(row[0], row[1], now)

    def reserve(self, user_id):
        """Dipanggil sebelum menjalankan pencarian dan AI."""

        with self._locked(user_id) as (cur, row, now):
            used, reset_at, active, _ = row
            quota = self._view(used, reset_at, now)

            if quota["blocked"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "quota_exhausted",
                        "message": (
                            "Kuota habis. Tunggu sampai "
                            "waktu isi ulang selesai."
                        ),
                        "quota": quota,
                    },
                    headers={
                        "Retry-After": str(
                            quota["retry_after"]
                        )
                    },
                )

            # Satu akun hanya memproses satu pesan sekaligus.
            if active:
                raise HTTPException(
                    status_code=409,
                    detail="Pesan sebelumnya masih diproses.",
                )

            request_id = secrets.token_hex(24)

            self._sql(
                cur,
                """
                    UPDATE user_chat_quotas
                    SET active_request = ?, active_until = ?
                    WHERE user_id = ?
                """,
                (
                    request_id,
                    now + self.lease,
                    user_id,
                ),
            )

            return request_id

    def complete(self, user_id, request_id, persist=None):
        """
        Menyimpan hasil chat dan mengurangi kuota
        dalam transaksi yang sama.
        """

        with self._locked(user_id) as (cur, row, now):
            used, _, active, _ = row

            if not request_id or active != request_id:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Permintaan sudah kedaluwarsa. "
                        "Silakan kirim ulang."
                    ),
                )

            # Jika penyimpanan gagal, transaksi dibatalkan
            # sehingga kuota tidak ikut berkurang.
            if persist is not None:
                persist(cur)

            used += 1

            reset_at = (
                now + self.cooldown
                if used >= self.limit
                else 0
            )

            self._sql(
                cur,
                """
                UPDATE user_chat_quotas
                SET used = ?, reset_at = ?,
                    active_request = NULL,
                    active_until = 0
                WHERE user_id = ?
                """,
                (used, reset_at, user_id),
            )

            return self._view(used, reset_at, now)

    def cancel(self, user_id, request_id):
        """Melepas permintaan gagal tanpa mengurangi kuota."""

        with self._locked(user_id) as (cur, _, _):
            self._sql(
                cur,
                """
                    UPDATE user_chat_quotas
                    SET active_request = NULL,
                        active_until = 0
                    WHERE user_id = ?
                      AND active_request = ?
                """,
                (user_id, request_id),
            )