import streamlit as st
import sqlite3
import pandas as pd
import time
import random
from datetime import datetime
from pathlib import Path
import ast

DB_FILE = "quiz.db"

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

def load_quiz_data():
    path = Path(__file__).parent / "quiz_data.json"
    with open(path, "r") as f:
        return ast.literal_eval(f.read())

@st.cache_data(ttl=10)
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM scores", conn)
    return df

def insert_score(name, score, ip, time_taken):
    date = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO scores (name, score, ip, time_taken, date) VALUES (?, ?, ?, ?, ?)",
            (name, score, ip, time_taken, date)
        )
        conn.commit()

def get_user_id():
    return st.session_state.get("user_id", str(time.time())[-6:])

def quiz_page():
    st.markdown("""
        <style>
            html, body, .stApp {
                background-color: #e6ffe6;
                font-family: 'Arial', sans-serif;
                font-size: 16px;
                padding: 0;
                margin: 0;
            }
            .main, .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
                max-width: 100% !important;
            }
            @media only screen and (max-width: 600px) {
                html, body, .stApp {
                    font-size: 14px;
                }
                .stRadio>div>label {
                    font-size: 14px;
                }
            }
            .stButton>button {
                background-color: #00cc44;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 0.5rem 1rem;
            }
            .stRadio>div>label {
                color: #006622;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("\U0001F3CF IPL Quiz")
    name = st.text_input("Enter your name to begin")
    ip = get_user_id()
    df = load_data()

    if not name:
        return

    already_played = not df[(df["name"] == name) & (df["ip"] == ip)].empty
    if already_played:
        st.warning("\u274C You have already attempted the quiz with this name and device.")
        return

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if not st.session_state.quiz_started:
        if st.button("Start Quiz"):
            raw_data = load_quiz_data()
            random.shuffle(raw_data)
            for q in raw_data:
                random.shuffle(q["options"])
            st.session_state.quiz_started = True
            st.session_state.quiz_data = raw_data
            st.session_state.start_time = time.time()
            st.session_state.responses = []
            st.session_state.current_question = 0
            st.session_state.question_start_time = time.time()

    if st.session_state.quiz_started:
        questions = st.session_state.quiz_data
        q_idx = st.session_state.current_question

        if q_idx >= len(questions):
            end_time = time.time()
            total_time = round(end_time - st.session_state.start_time, 2)
            score = sum(1 for correct, given in st.session_state.responses if correct == given)
            insert_score(name, score, ip, total_time)
            st.success(f"\u2705 {name}, you scored {score}/{len(questions)}")
            st.info(f"\u23F1 Time Taken: {total_time} seconds")
            st.session_state.quiz_started = False
            st.cache_data.clear()

            df = load_data()
            top10 = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
            st.subheader("\U0001F3C6 Real-Time Top 10 Leaderboard")
            st.dataframe(top10[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)
            return

        question = questions[q_idx]
        elapsed = time.time() - st.session_state.question_start_time
        remaining = max(0, int(30 - elapsed))
        st.subheader(f"Question {q_idx + 1} of {len(questions)}")
        st.markdown(f"<h4 style='color:green;'>\u23F3 Time remaining: {remaining} seconds</h4>", unsafe_allow_html=True)

        with st.form(key=f"form_q{q_idx}"):
            response = st.radio(question["question"], question["options"], key=f"q{q_idx}")
            submitted = st.form_submit_button("Submit")

            if submitted or remaining == 0:
                st.session_state.responses.append((question["answer"], response if submitted else "Skipped"))
                st.session_state.current_question += 1
                st.session_state.question_start_time = time.time()

        with st.expander("\U0001F4CA Live Poll Results"):
            poll_results = {opt: 0 for opt in question["options"]}
            for _, given in st.session_state.responses:
                if given in poll_results:
                    poll_results[given] += 1
            st.bar_chart(poll_results)

def leaderboard_page():
    st.title("\U0001F4CA Public Leaderboard")
    df = load_data()
    if df.empty:
        st.warning("No scores yet.")
        return

    filter_date = st.selectbox("\U0001F4C5 Filter by date", ["All"] + sorted(df["date"].unique()))
    if filter_date != "All":
        df = df[df["date"] == filter_date]

    name_filter = st.text_input("\U0001F50D Search by name")
    if name_filter:
        df = df[df["name"].str.contains(name_filter, case=False, na=False)]

    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("\u2B07\uFE0F Export CSV", csv, "quiz_results.csv", "text/csv")

    tab1, tab2 = st.tabs(["\U0001F3C5 Highest Scores", "\u26A1 Fastest Perfect Scores"])

    with tab1:
        top = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(20)
        st.dataframe(top[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)

    with tab2:
        perfect = df[df["score"] == df["score"].max()]
        fast = perfect.sort_values(by="time_taken").head(20)
        st.dataframe(fast[["name", "score", "ip", "time_taken"]].reset_index(drop=True), use_container_width=True)

def main():
    st.set_page_config(page_title="IPL Quiz", layout="wide")
    init_db()
    st.session_state.user_id = get_user_id()

    menu = st.sidebar.radio("\U0001F4DA Menu", ["Take Quiz", "Leaderboard"])
    if menu == "Take Quiz":
        quiz_page()
    else:
        leaderboard_page()

if __name__ == "__main__":
    main()
