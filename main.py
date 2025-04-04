import streamlit as st
import time
import sqlite3
from datetime import datetime
from pathlib import Path

QUIZ_FILE = Path("quiz_data.json")
DB_PATH = "quiz.db"
MAX_TIME = 30

st.set_page_config(page_title="🧠 IPL Quiz", page_icon="❓")

# ===== Read & Write Helpers for quiz_data.json =====
def read_quiz():
    if QUIZ_FILE.exists():
        with QUIZ_FILE.open("r", encoding="utf-8") as f:
            return eval(f.read())
    return []

def write_quiz(data):
    with QUIZ_FILE.open("w", encoding="utf-8") as f:
        f.write(str(data))

# ===== DB Setup =====
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                name TEXT PRIMARY KEY,
                score INTEGER,
                total_time REAL,
                timestamp TEXT,
                session_id TEXT
            )
        """)
        conn.commit()

init_db()
quiz_data = read_quiz()

# ===== Admin Panel =====
def admin_panel():
    st.title("🛠️ Admin Panel")

    # Add Question
    with st.expander("➕ Add New Question"):
        question = st.text_input("Question")
        options = st.text_area("Options (one per line)").splitlines()
        answer = st.text_input("Correct Answer")
        info = st.text_area("Extra Info (optional)", "")

        if st.button("Add Question"):
            if question and options and answer:
                quiz_data.append({
                    "question": question,
                    "options": options,
                    "answer": answer,
                    "information": info
                })
                write_quiz(quiz_data)
                st.success("Question added!")

    # Delete Question
    st.subheader("🗑 Existing Questions")
    for idx, q in enumerate(quiz_data):
        st.markdown(f"**Q{idx+1}:** {q['question']}")
        if st.button(f"Delete Q{idx+1}", key=f"del-{idx}"):
            quiz_data.pop(idx)
            write_quiz(quiz_data)
            st.success("Deleted successfully!")
            st.experimental_rerun()

    # Leaderboard
    st.subheader("🏆 Leaderboard")
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT name, score, total_time, timestamp FROM results
            ORDER BY score DESC, total_time ASC
        """).fetchall()

    for i, (name, score, total_time, ts) in enumerate(rows, 1):
        st.write(f"**{i}. {name}** — 🧠 {score} points ⏱ {total_time}s on {ts}")

# ===== Save Quiz Result =====
def save_result():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO results (name, score, total_time, timestamp, session_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            st.session_state.name,
            st.session_state.score,
            round(st.session_state.total_time, 2),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.get("session_id", "unknown")
        ))
        conn.commit()

# ===== Quiz Logic =====
def run_quiz():
    st.title("🧠 IPL Quiz")
    if st.session_state.current_index >= len(quiz_data):
        st.balloons()
        st.success(f"✅ You scored {st.session_state.score} / {len(quiz_data)*10}")
        st.info(f"⏱ Time: {round(st.session_state.total_time, 2)}s")
        save_result()
        if st.button("Restart"):
            for k in st.session_state.keys():
                del st.session_state[k]
            st.experimental_rerun()
        return

    question = quiz_data[st.session_state.current_index]
    elapsed = round(time.time() - st.session_state.start_time)
    remaining = MAX_TIME - elapsed
    if not st.session_state.answer_submitted and remaining <= 0:
        st.toast("⏱ Time's up!")
        st.session_state.answer_submitted = True

    st.metric("Score", f"{st.session_state.score}")
    st.progress((st.session_state.current_index+1) / len(quiz_data))
    st.warning(f"⏳ Time Left: {max(0, remaining)}s")

    st.header(f"Q{st.session_state.current_index+1}")
    st.subheader(question["question"])
    st.caption(question.get("information", ""))

    for i, opt in enumerate(question["options"]):
        if not st.session_state.answer_submitted:
            if st.button(opt, key=f"opt-{i}"):
                st.session_state.selected_option = opt

    if st.session_state.answer_submitted:
        st.markdown(f"✅ Your choice: **{st.session_state.selected_option}**")

    def submit():
        if not st.session_state.answer_submitted:
            if st.session_state.selected_option == question["answer"]:
                st.session_state.score += 10
            st.session_state.total_time += time.time() - st.session_state.start_time
            st.session_state.answer_submitted = True

    def next_q():
        st.session_state.current_index += 1
        st.session_state.selected_option = None
        st.session_state.answer_submitted = False
        st.session_state.start_time = time.time()

    if st.session_state.answer_submitted:
        st.button("➡️ Next", on_click=next_q)
    else:
        st.button("🚀 Submit", on_click=submit)

# ===== Main Login =====
if "name" not in st.session_state:
    st.session_state.name = ""
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    st.session_state.start_time = time.time()
    st.session_state.total_time = 0.0

st.title("🔐 IPL Quiz Platform")

if not st.session_state.name:
    name = st.text_input("Enter your name to start")
    if st.button("Enter"):
        if name:
            st.session_state.name = name
            st.session_state.session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]
            st.experimental_rerun()

elif st.session_state.name == "ecell_696969":
    admin_panel()
else:
    run_quiz()
