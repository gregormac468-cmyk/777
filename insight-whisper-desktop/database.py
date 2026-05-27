"""
Модуль базы данных SQLite для хранения звонков, менеджеров и инструкций.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from config import CONFIG_DIR, ensure_dirs

DB_PATH = CONFIG_DIR / "insight_whisper.db"


@contextmanager
def get_conn():
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Инициализация таблиц БД."""
    ensure_dirs()
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS managers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            position TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT,
            manager_name TEXT,
            instruction_name TEXT,
            status TEXT DEFAULT 'done',
            transcript TEXT,
            analysis_json TEXT,
            call_type TEXT,
            overall_score REAL,
            duration_seconds INTEGER,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_calls_created ON calls(created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_calls_manager ON calls(manager_name)")



# ===== MANAGERS =====
def add_manager(name: str, position: str = "") -> bool:
    try:
        with get_conn() as conn:
            conn.execute("INSERT INTO managers (name, position) VALUES (?, ?)",
                         (name.strip(), position.strip()))
        return True
    except sqlite3.IntegrityError:
        return False


def update_manager(manager_id: int, name: str, position: str = ""):
    with get_conn() as conn:
        conn.execute("UPDATE managers SET name = ?, position = ? WHERE id = ?",
                     (name.strip(), position.strip(), manager_id))


def delete_manager(manager_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM managers WHERE id = ?", (manager_id,))


def list_managers() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM managers ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def list_manager_names() -> list[str]:
    return [m["name"] for m in list_managers()]


# ===== CALLS =====
def save_call(data: dict) -> int:
    """Сохранить результат анализа звонка. Возвращает ID."""
    analysis = data.get("analysis") or {}
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO calls (
                file_name, file_path, manager_name, instruction_name,
                status, transcript, analysis_json, call_type, overall_score,
                duration_seconds, error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("file_name", ""),
            data.get("file_path", ""),
            data.get("manager", "") or data.get("manager_name", ""),
            data.get("instruction_name", ""),
            data.get("status", "done"),
            data.get("transcript", ""),
            json.dumps(analysis, ensure_ascii=False) if analysis else None,
            analysis.get("call_type", "") if analysis else "",
            analysis.get("overall_score") if analysis else None,
            data.get("duration_seconds"),
            data.get("error", ""),
            data.get("timestamp", datetime.now().isoformat()),
        ))
        return cur.lastrowid



def update_call(call_id: int, data: dict):
    """Обновить запись звонка (например, после повторного анализа)."""
    analysis = data.get("analysis") or {}
    with get_conn() as conn:
        conn.execute("""
            UPDATE calls SET
                status = ?, transcript = ?, analysis_json = ?,
                call_type = ?, overall_score = ?, error_message = ?
            WHERE id = ?
        """, (
            data.get("status", "done"),
            data.get("transcript", ""),
            json.dumps(analysis, ensure_ascii=False) if analysis else None,
            analysis.get("call_type", "") if analysis else "",
            analysis.get("overall_score") if analysis else None,
            data.get("error", ""),
            call_id,
        ))


def get_call(call_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("analysis_json"):
            try:
                d["analysis"] = json.loads(d["analysis_json"])
            except Exception:
                d["analysis"] = None
        else:
            d["analysis"] = None
        return d


def delete_call(call_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM calls WHERE id = ?", (call_id,))


def delete_calls(call_ids: list[int]):
    if not call_ids:
        return
    placeholders = ",".join("?" * len(call_ids))
    with get_conn() as conn:
        conn.execute(f"DELETE FROM calls WHERE id IN ({placeholders})", call_ids)



def list_calls(
    date_from: str | None = None,
    date_to: str | None = None,
    manager: str | None = None,
    call_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 1000,
) -> list[dict]:
    """Получить список звонков с фильтрами."""
    where = []
    params = []

    if date_from:
        where.append("date(created_at) >= date(?)")
        params.append(date_from)
    if date_to:
        where.append("date(created_at) <= date(?)")
        params.append(date_to)
    if manager and manager != "__all__":
        where.append("manager_name = ?")
        params.append(manager)
    if call_type and call_type != "__all__":
        where.append("call_type LIKE ?")
        params.append(f"%{call_type}%")
    if status and status != "__all__":
        where.append("status = ?")
        params.append(status)
    if search:
        where.append("(file_name LIKE ? OR transcript LIKE ?)")
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    sql = "SELECT * FROM calls"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("analysis_json"):
                try:
                    d["analysis"] = json.loads(d["analysis_json"])
                except Exception:
                    d["analysis"] = None
            else:
                d["analysis"] = None
            result.append(d)
        return result


def get_stats(date_from: str | None = None, date_to: str | None = None,
              manager: str | None = None) -> dict:
    """Агрегированная статистика."""
    calls = list_calls(date_from=date_from, date_to=date_to, manager=manager, limit=100000)
    return {"calls": calls, "total": len(calls)}
