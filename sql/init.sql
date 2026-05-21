-- Run once after creating the `ai_core` database.
-- Tables are auto-created on app startup; this file only enables the
-- pgvector extension which requires superuser.

CREATE EXTENSION IF NOT EXISTS vector;
