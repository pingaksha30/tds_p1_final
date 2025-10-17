# db.py
import sqlite3
import time
from pathlib import Path

DB_PATH = Path("tasks.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS repos (
        id INTEGER PRIMARY KEY,
        email TEXT,
        task TEXT,
        round INTEGER,
        nonce TEXT,
        repo_full TEXT,
        repo_url TEXT,
        commit_sha TEXT,
        pages_url TEXT,
        created_at INTEGER
    )
    """)
    conn.commit()
    conn.close()

def save_repo_record(email, task, round_idx, nonce, repo_full, repo_url, commit_sha, pages_url):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO repos (email, task, round, nonce, repo_full, repo_url, commit_sha, pages_url, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (email, task, round_idx, nonce, repo_full, repo_url, commit_sha, pages_url, int(time.time()))
    )
    conn.commit()
    conn.close()

def get_latest_repo(email, task):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT id, email, task, round, nonce, repo_full, repo_url, commit_sha, pages_url FROM repos WHERE email=? AND task=? ORDER BY id DESC LIMIT 1", (email, task))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    keys = ["id","email","task","round","nonce","repo_full","repo_url","commit_sha","pages_url"]
    return dict(zip(keys, row))
