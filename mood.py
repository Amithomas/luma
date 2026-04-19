# mood.py

import sqlite3
from datetime import datetime
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS moods
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       mood_text
                       TEXT,
                       sentiment
                       TEXT,
                       emotion
                       TEXT,
                       intensity
                       REAL,
                       mood_summary
                       TEXT,
                       timestamp
                       TEXT
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS conversations
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       role
                       TEXT,
                       message
                       TEXT,
                       timestamp
                       TEXT
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS summaries
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER,
                       summary_text
                       TEXT,
                       timestamp
                       TEXT
                   )
                   ''')

    conn.commit()
    conn.close()


def save_mood(user_id, mood_text, sentiment="unknown",
              emotion="unknown", intensity=0.5, mood_summary=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO moods (user_id, mood_text, sentiment,
                                      emotion, intensity, mood_summary, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ''', (user_id, mood_text, sentiment, emotion,
                         intensity, mood_summary, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_recent_mood(user_id, limit=5):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT mood_text, sentiment, emotion, 
               intensity, mood_summary, timestamp 
        FROM moods 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (user_id, limit))

    rows = cursor.fetchall()
    conn.close()
    return rows


def save_message(user_id, role, message):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO conversations (user_id, role, message, timestamp)
                   VALUES (?, ?, ?, ?)
                   ''', (user_id, role, message, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_conversation_history(user_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT role, message
                   FROM conversations
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                       LIMIT ?
                   ''', (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    # Reverse so oldest message comes first
    rows.reverse()

    return rows


def save_summary(user_id, summary_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO summaries (user_id, summary_text, timestamp)
                   VALUES (?, ?, ?)
                   ''', (user_id, summary_text, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_summaries(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT summary_text, timestamp
                   FROM summaries
                   WHERE user_id = ?
                   ORDER BY timestamp ASC
                   ''', (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_message_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT COUNT(*)
                   FROM conversations
                   WHERE user_id = ?
                   ''', (user_id,))

    count = cursor.fetchone()[0]
    conn.close()
    return count