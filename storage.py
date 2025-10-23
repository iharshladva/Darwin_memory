import sqlite3, pathlib, json, time

DB_PATH = str(pathlib.Path("/content/memory.db"))

SCHEMA = r"""
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users(
  user_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  locale TEXT,
  consent_flags TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS sources(
  source_id TEXT PRIMARY KEY,
  channel TEXT CHECK(channel IN ('chat','image','audio','clicks','system')),
  raw_ref TEXT,
  parser_version TEXT
);

CREATE TABLE IF NOT EXISTS memories(
  memory_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  type TEXT,
  value TEXT NOT NULL,
  modality TEXT,
  source_id TEXT REFERENCES sources(source_id),
  embedding BLOB,
  keywords TEXT,
  confidence REAL,
  freshness_score REAL,
  ttl INTEGER,
  tags TEXT,
  pii_sensitivity TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
  memory_id UNINDEXED, value, content='memories', content_rowid=''
);

CREATE TABLE IF NOT EXISTS evidence(
  evidence_id TEXT PRIMARY KEY,
  memory_id TEXT NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
  raw_excerpt TEXT,
  explanation TEXT,
  timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policy_tags(
  name TEXT PRIMARY KEY,
  retention_days INTEGER,
  shareable_with_llm INTEGER,
  shareable_with_recsys INTEGER
);
"""

DEFAULT_POLICIES = [
  {"name":"private_health",   "retention_days":0,   "shareable_with_llm":0, "shareable_with_recsys":0},
  {"name":"general_interest", "retention_days":365, "shareable_with_llm":1, "shareable_with_recsys":1}
]

def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
  conn = sqlite3.connect(db_path, check_same_thread=False)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA journal_mode=WAL;")
  conn.execute("PRAGMA synchronous=NORMAL;")
  return conn

def init_db(conn: sqlite3.Connection) -> None:
  conn.executescript(SCHEMA)
  for p in DEFAULT_POLICIES:
    conn.execute(
      "INSERT OR IGNORE INTO policy_tags(name, retention_days, shareable_with_llm, shareable_with_recsys) VALUES (?,?,?,?)",
      (p["name"], p["retention_days"], p["shareable_with_llm"], p["shareable_with_recsys"])
    )
  conn.commit()

def upsert_user(conn, user_id: str, locale: str = "en_US", consent_flags: dict | None = None):
  now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
  cf = json.dumps(consent_flags or {"share_llm": True})
  conn.execute(
    "INSERT OR REPLACE INTO users(user_id, created_at, locale, consent_flags) VALUES (?,?,?,?)",
    (user_id, now, locale, cf)
  )
  conn.commit()

def upsert_source(conn, source_id: str, channel: str, raw_ref: str = "seed", parser_version: str = "v1"):
  conn.execute(
    "INSERT OR IGNORE INTO sources(source_id, channel, raw_ref, parser_version) VALUES (?,?,?,?)",
    (source_id, channel, raw_ref, parser_version)
  )
  conn.commit()
