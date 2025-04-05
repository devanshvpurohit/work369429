import streamlit as st

import sqlite3
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import ast

DB_FILE = "quiz.db"
QUESTION_TIME_LIMIT = 30  # seconds

# === DB INIT ===
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                name TEXT,
                score INTEGER,
                ip TEXT,
                time_taken REAL,
                date TEXT
            )
        """)
        conn.commit()

# === LOAD QUIZ QUESTIONS WITHOUT json IMPORT ===
def load_quiz_data():
    path = Path(__file__).parent / "quiz_data.json"
    with open(path, "r") as f:
        return ast.literal_eval(f.read())

# === CACHE: LOAD SCORES FROM DB ===
@st.cache_data(ttl=10)
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM scores", conn)
    return df

# === INSERT NEW SCORE ===
def insert_score(name, score, ip, time_taken):
    date = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO scores (name, score, ip, time_taken, date) VALUES (?, ?, ?, ?, ?)",
            (name, score, ip, time_taken, date)
        )
        conn.commit()

# === GET SESSION-BASED ID FOR USER ===
def get_user_id():
    return st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]

# === QUIZ PAGE ===
def quiz_page():
    st.title("🏏 IPL Quiz")
    name = st.text_input("Enter your name")

    ip = get_user_id()
    df = load_data()
    already_played = not df[(df["name"] == name) & (df["ip"] == ip)].empty

    if already_played:
        st.warning("🚫 You have already attempted the quiz with this name and device.")
        return

    if name and st.button("Start Quiz"):
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()
        st.session_state.quiz_data = load_quiz_data()
        st.session_state.responses = []
        st.session_state.current_q = 0
        st.session_state.q_start_time = time.time()

    if st.session_state.get("quiz_started", False):
        quiz_data = st.session_state.quiz_data
        q_idx = st.session_state.current_q

        if q_idx >= len(quiz_data):
            total_time = round(time.time() - st.session_state.start_time, 2)
            responses = st.session_state.responses
            score = sum(1 for correct, given in responses if correct == given)

            insert_score(name, score, ip, total_time)

            st.success(f"✅ {name}, you scored {score}/{len(responses)}")
            st.info(f"⏱ Time Taken: {total_time} seconds")

            st.session_state.quiz_started = False
            st.cache_data.clear()

            df = load_data()
            top10 = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
            st.subheader("🏆 Real-Time Top 10 Leaderboard")
            st.dataframe(top10[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)
            return

        question = quiz_data[q_idx]
        elapsed = time.time() - st.session_state.q_start_time
        remaining = int(QUESTION_TIME_LIMIT - elapsed)

        st.subheader(f"Question {q_idx + 1}/{len(quiz_data)}")
        st.write(question["question"])
        response = st.radio("Choose an option:", question["options"], key=f"q{q_idx}", index=-1)

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Next", key=f"next_{q_idx}"):
                selected = response if response else "Skipped"
                st.session_state.responses.append((question["answer"], selected))
                st.session_state.current_q += 1
                st.session_state.q_start_time = time.time()
                st.rerun()
        with col2:
            st.info(f"⏳ {remaining} seconds left")

        if remaining <= 0:
            selected = response if response else "Skipped"
            st.session_state.responses.append((question["answer"], selected))
            st.session_state.current_q += 1
            st.session_state.q_start_time = time.time()
            st.rerun()

# === LEADERBOARD PAGE ===
def leaderboard_page():
    st.title("📊 Public Leaderboard")
    df = load_data()

    if df.empty:
        st.warning("No scores yet.")
        return

    filter_date = st.selectbox("📅 Filter by date", ["All"] + sorted(df["date"].unique()))
    if filter_date != "All":
        df = df[df["date"] == filter_date]

    name_filter = st.text_input("🔍 Search by name")
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]

    tab1, tab2 = st.tabs(["🏅 Highest Scores", "⚡ Fastest Perfect Scores"])

    with tab1:
        top = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(20)
        st.dataframe(top[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)

    with tab2:
        perfect = df[df["score"] == df["score"].max()]
        fast = perfect.sort_values(by="time_taken").head(20)
        st.dataframe(fast[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)

# === MAIN ===
def main():
    st.set_page_config(page_title="IPL Quiz", layout="centered")
    init_db()

    st.sidebar.title("🎮 Quiz Navigation")
    choice = st.sidebar.radio("📚 Menu", ["Take Quiz", "Leaderboard"])
    if choice == "Take Quiz":
        quiz_page()
    else:
        leaderboard_page()

if __name__ == "__main__":
    main()
