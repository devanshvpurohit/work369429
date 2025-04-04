import streamlit as st
import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path
import socket

DB_PATH = "quiz.db"
QUIZ_PATH = Path("quiz_data.json")
MAX_TIME = 30  # seconds per question

# ===== SETUP =====
st.set_page_config(page_title="🧠 Quiz Master", page_icon="❓", layout="centered")

# ===== INIT DATABASE =====
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                name TEXT PRIMARY KEY,
                score INTEGER,
                total_time REAL,
                timestamp TEXT,
                session_id TEXT,
                ip_address TEXT
            )
        """)
        conn.commit()

# ===== GET IP ADDRESS =====
def get_ip():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "unknown"

# ===== LOAD QUIZ =====
if not QUIZ_PATH.exists():
    st.error("❌ 'quiz_data.json' not found. Upload it to the app folder.")
    st.stop()

with QUIZ_PATH.open(encoding="utf-8") as f:
    quiz_data = json.load(f)

# ===== STATE INIT =====
defaults = {
    'name': '',
    'current_index': 0,
    'score': 0,
    'selected_option': None,
    'answer_submitted': False,
    'start_time': time.time(),
    'total_time': 0.0,
    'ip_address': get_ip()
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ===== DB INSERT =====
def save_result():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO results (name, score, total_time, timestamp, session_id, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.name,
            st.session_state.score,
            round(st.session_state.total_time, 2),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.get("session_id", "unknown"),
            st.session_state.ip_address
        ))
        conn.commit()

# ===== FORM: NAME INPUT =====
if not st.session_state.name:
    st.title("🧠 Welcome to the IPL Quiz")
    st.subheader("Enter your name to begin")
    name_input = st.text_input("Name", max_chars=30)
    if st.button("Start Quiz") and name_input:
        with sqlite3.connect(DB_PATH) as conn:
            result = conn.execute("""
                SELECT 1 FROM results 
                WHERE name = ? OR ip_address = ?
            """, (name_input, st.session_state.ip_address)).fetchone()
        if result:
            st.error("❌ You have already participated from this IP or name.")
        else:
            st.session_state.name = name_input
            st.session_state.session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]
            st.rerun()

# ===== QUIZ FLOW =====
elif st.session_state.current_index >= len(quiz_data):
    st.balloons()
    st.title("🎉 Quiz Completed!")
    st.success(f"Your score: {st.session_state.score} / {len(quiz_data) * 10}")
    st.info(f"⏱ Total Time: {round(st.session_state.total_time, 2)} seconds")
    save_result()

    st.subheader("🏆 Leaderboard (Top 10)")
    with sqlite3.connect(DB_PATH) as conn:
        leaderboard = conn.execute("""
            SELECT name, score, total_time FROM results 
            ORDER BY score DESC, total_time ASC 
            LIMIT 10
        """).fetchall()

    for i, (n, s, t) in enumerate(leaderboard, 1):
        st.write(f"{i}. **{n}** — {s} pts in {t:.2f}s")

    if st.button("🔁 Restart"):
        for k in defaults:
            st.session_state[k] = defaults[k]
        st.session_state.name = ''
        st.rerun()
else:
    # Question + Timer
    question = quiz_data[st.session_state.current_index]
    elapsed = round(time.time() - st.session_state.start_time)
    remaining = MAX_TIME - elapsed

    if not st.session_state.answer_submitted and remaining <= 0:
        st.toast("⏱ Time's up! Auto-submitting.")
        st.session_state.answer_submitted = True

    st.title("🧠 IPL Quiz")
    st.metric("Score", f"{st.session_state.score} / {len(quiz_data)*10}")
    st.progress((st.session_state.current_index + 1) / len(quiz_data))
    st.success(f"⏱ Time Left: {max(0, remaining)} sec")

    st.header(f"Question {st.session_state.current_index + 1}")
    st.subheader(question["question"])
    st.caption(question.get("information", ""))
    st.markdown("---")

    # Display options
    options = question["options"]
    answer = question["answer"]

    if not st.session_state.answer_submitted:
        for i, opt in enumerate(options):
            if st.button(opt, key=f"opt-{i}", use_container_width=True):
                st.session_state.selected_option = opt

    st.markdown("---")

    # Submit & Next
    def submit_answer():
        if st.session_state.selected_option == answer:
            st.session_state.score += 10
        st.session_state.answer_submitted = True
        st.session_state.total_time += time.time() - st.session_state.start_time

    def next_question():
        st.session_state.current_index += 1
        st.session_state.selected_option = None
        st.session_state.answer_submitted = False
        st.session_state.start_time = time.time()

    if st.session_state.answer_submitted:
        if st.session_state.current_index < len(quiz_data) - 1:
            st.button("➡️ Next", on_click=next_question)
        else:
            st.button("✅ Finish", on_click=next_question)
    else:
        st.button("🚀 Submit", on_click=submit_answer)

# ===== INIT DB ON LOAD =====
init_db()

# ===== CUSTOM GREEN STYLING =====
st.markdown("""
<style>
div.stButton > button {
    margin: 4px auto;
    width: 100%;
    font-size: 16px;
    border-radius: 12px;
    background-color: #00aa00 !important;
    color: white !important;
    border: none;
}
.stProgress > div > div > div {
    background-color: #00cc00;
}
.stMetric label, .stMetric div {
    color: #006600 !important;
}
</style>
""", unsafe_allow_html=True)
