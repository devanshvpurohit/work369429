import streamlit as st
import sqlite3
import pandas as pd
import time
import json
from datetime import datetime

DB_FILE = "quiz.db"
QUIZ_JSON = "quiz_data.json"

# === DB INIT ===
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                name TEXT UNIQUE,
                score INTEGER,
                ip TEXT,
                time_taken REAL,
                date TEXT
            )
        """)
        conn.commit()

# === CACHE: LOAD DATA ===
@st.cache_data(ttl=10)
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM scores", conn)
    return df

# === INSERT SINGLE SCORE ===
def insert_score(name, score, ip, time_taken):
    date = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO scores (name, score, ip, time_taken, date) VALUES (?, ?, ?, ?, ?)",
            (name, score, ip, time_taken, date)
        )
        conn.commit()

# === IP GETTER ===
def get_user_id():
    return st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]

# === LOAD QUIZ JSON ===
def load_quiz_json():
    with open(QUIZ_JSON, "r") as f:
        return json.load(f)

# === QUIZ PAGE ===
def quiz_page():
    st.title("🏏 IPL Quiz")
    name = st.text_input("Enter your name")

    df = load_data()
    if name and name in df["name"].values:
        st.warning("This name has already been used. Please try a different one.")
        return

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if st.button("Start Quiz") and name:
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()

    if st.session_state.quiz_started:
        quiz_data = load_quiz_json()
        answers = {}
        with st.form("quiz_form"):
            for i, q in enumerate(quiz_data):
                answers[i] = st.radio(q["question"], q["options"], key=f"q{i}")
            submit = st.form_submit_button("Submit")

            if submit:
                end_time = time.time()
                time_taken = round(end_time - st.session_state.start_time, 2)

                # Calculate score
                score = 0
                for i, q in enumerate(quiz_data):
                    if answers[i] == q["answer"]:
                        score += 1

                ip = get_user_id()
                insert_score(name, score, ip, time_taken)

                st.success(f"✅ {name}, you scored {score}/{len(quiz_data)}")
                st.info(f"⏱️ Time Taken: {time_taken} seconds")

                st.session_state.quiz_started = False
                st.cache_data.clear()  # Invalidate leaderboard cache

                df = load_data()
                top_df = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
                st.subheader("🏆 Top 10 Leaderboard")
                st.dataframe(top_df.reset_index(drop=True))

# === LEADERBOARD PAGE ===
def leaderboard_page():
    st.title("📊 Public Leaderboard")
    df = load_data()

    if df.empty:
        st.warning("No scores recorded yet.")
        return

    # Filter
    filter_date = st.selectbox("📅 Filter by date:", ["All"] + sorted(df["date"].unique()))
    if filter_date != "All":
        df = df[df["date"] == filter_date]

    name_filter = st.text_input("🔍 Search by name")
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]

    tab1, tab2 = st.tabs(["🏅 Highest Scores", "⚡ Fastest Perfect Scores"])

    with tab1:
        top = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(20)
        st.dataframe(top.reset_index(drop=True))

    with tab2:
        perfect = df[df["score"] == df["score"].max()]
        fast = perfect.sort_values(by="time_taken").head(20)
        st.dataframe(fast.reset_index(drop=True))

# === MAIN ===
def main():
    st.set_page_config(page_title="IPL Quiz", layout="centered")
    init_db()

    choice = st.sidebar.radio("📚 Menu", ["Take Quiz", "Leaderboard"])
    if choice == "Take Quiz":
        quiz_page()
    else:
        leaderboard_page()

if __name__ == "__main__":
    main()
