import streamlit as st
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# ===== CONFIG =====
QUIZ_PATH = Path("quiz_data.json")
DB_PATH = "quiz.db"
ADMIN_PASSWORD = "ipl2025"  # change to a secret one!

st.set_page_config(page_title="🛠️ Admin Dashboard", layout="centered")

# ===== AUTH =====
st.title("🔐 Admin Login")
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    pwd = st.text_input("Enter Admin Password", type="password")
    if st.button("Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("✅ Access granted")
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    st.stop()

# ===== FUNCTIONS =====
def load_quiz():
    if QUIZ_PATH.exists():
        with QUIZ_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_quiz(quiz):
    with QUIZ_PATH.open("w", encoding="utf-8") as f:
        json.dump(quiz, f, indent=4)

def fetch_leaderboard():
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute("""
            SELECT name, score, total_time, timestamp
            FROM results
            ORDER BY score DESC, total_time ASC
        """).fetchall()
    return result

# ===== TABS =====
tab1, tab2, tab3 = st.tabs(["📋 Questions", "➕ Add Question", "🏆 Leaderboard"])

# ===== VIEW/DELETE QUESTIONS =====
with tab1:
    st.subheader("🧾 Existing Questions")
    quiz = load_quiz()
    for i, q in enumerate(quiz):
        with st.expander(f"Q{i+1}: {q['question']}", expanded=False):
            st.write("Options:", q["options"])
            st.write("Answer:", q["answer"])
            st.write("Info:", q.get("information", ""))
            if st.button("❌ Delete", key=f"del-{i}"):
                quiz.pop(i)
                save_quiz(quiz)
                st.success("Question deleted.")
                st.rerun()

# ===== ADD QUESTION =====
with tab2:
    st.subheader("➕ Add New Question")
    question = st.text_area("Question")
    options = [st.text_input(f"Option {i+1}") for i in range(4)]
    correct_answer = st.selectbox("Correct Answer", options)
    information = st.text_area("Extra Info (optional)", "")

    if st.button("✅ Save Question"):
        if not question or any(o.strip() == "" for o in options):
            st.error("Please fill in all fields.")
        else:
            quiz = load_quiz()
            quiz.append({
                "question": question.strip(),
                "options": options,
                "answer": correct_answer,
                "information": information.strip()
            })
            save_quiz(quiz)
            st.success("✅ Question added.")
            st.experimental_rerun()

# ===== LEADERBOARD =====
with tab3:
    st.subheader("📊 Live Leaderboard")
    leaderboard = fetch_leaderboard()

    if leaderboard:
        st.table(
            [{"Name": row[0], "Score": row[1], "Time": row[2], "Timestamp": row[3]} for row in leaderboard]
        )
    else:
        st.info("No results yet.")

