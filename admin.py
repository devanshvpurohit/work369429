import streamlit as st
import sqlite3
import pandas as pd
import time
import random
from datetime import datetime
from pathlib import Path
import ast

DB_FILE = "quiz.db"

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

# === LOAD QUIZ QUESTIONS ===
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

# === GET USER ID ===
def get_user_id():
    return st.session_state.get("user_id", str(time.time())[-6:])

# === QUIZ PAGE ===
def quiz_page():
    st.title("🏏 IPL Quiz")
    name = st.text_input("Enter your name to begin")
    ip = get_user_id()
    df = load_data()

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    already_played = not df[(df["name"] == name) & (df["ip"] == ip)].empty
    if already_played:
        st.warning("🚫 You have already attempted the quiz with this name and device.")
        return

    if not st.session_state.quiz_started and name:
        if st.button("Start Quiz"):
            st.session_state.quiz_started = True
            st.session_state.start_time = time.time()
            raw_data = load_quiz_data()
            random.shuffle(raw_data)
            for q in raw_data:
                random.shuffle(q["options"])
            st.session_state.quiz_data = raw_data
            st.session_state.responses = []
            st.session_state.current_question = 0
            st.session_state.question_start_time = time.time()
            st.experimental_rerun()

    if st.session_state.quiz_started:
        q_idx = st.session_state.current_question
        quiz_data = st.session_state.quiz_data

        if q_idx >= len(quiz_data):
            # Quiz finished
            end_time = time.time()
            total_time = round(end_time - st.session_state.start_time, 2)
            score = sum(1 for correct, given in st.session_state.responses if correct == given)
            insert_score(name, score, ip, total_time)
            st.success(f"✅ {name}, you scored {score}/{len(quiz_data)}")
            st.info(f"⏱ Total Time Taken: {total_time} seconds")
            st.session_state.quiz_started = False
            st.cache_data.clear()

            # Leaderboard preview
            df = load_data()
            top10 = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
            st.subheader("🏆 Real-Time Top 10 Leaderboard")
            st.dataframe(top10[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)
            return

        question = quiz_data[q_idx]
        elapsed = time.time() - st.session_state.question_start_time
        remaining = int(30 - elapsed)

        if remaining <= 0:
            # Time up, auto skip
            st.session_state.responses.append((question["answer"], "Skipped"))
            st.session_state.current_question += 1
            st.session_state.question_start_time = time.time()
            st.experimental_rerun()

        st.subheader(f"Question {q_idx + 1} / {len(quiz_data)}")
        st.write(f"⏳ Time remaining: {remaining} seconds")

        with st.form(f"form_q{q_idx}"):
            response = st.radio(question["question"], question["options"], key=f"q{q_idx}")
            submit = st.form_submit_button("Submit")
            if submit:
                st.session_state.responses.append((question["answer"], response))
                st.session_state.current_question += 1
                st.session_state.question_start_time = time.time()
                st.experimental_rerun()

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

    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "quiz_results.csv", "text/csv")

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
    st.session_state.user_id = get_user_id()

    menu = st.sidebar.radio("📚 Menu", ["Take Quiz", "Leaderboard"])
    if menu == "Take Quiz":
        quiz_page()
    else:
        leaderboard_page()

if __name__ == "__main__":
    main()
