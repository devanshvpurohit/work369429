import streamlit as st
import sqlite3
from datetime import datetime
from pathlib import Path
import ast
import time

# === CONFIG ===
DB_PATH = "quiz.db"
QUIZ_PATH = Path("quiz_data.json")
MAX_TIME = 30

# === PAGE SETUP ===
st.set_page_config(page_title="IPL Quiz", page_icon="🏏", layout="centered")

# === STATE INIT ===
defaults = {
    "name": "",
    "admin": False,
    "current_index": 0,
    "score": 0,
    "total_time": 0.0,
    "selected_option": None,
    "answer_submitted": False,
    "start_time": time.time()
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# === DB INIT ===
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                options TEXT,
                answer TEXT,
                information TEXT
            )
        """)
        conn.commit()
init_db()

# === JSON LOADING WITHOUT json LIB ===
def load_questions_from_json():
    if not QUIZ_PATH.exists():
        return []

    raw = QUIZ_PATH.read_text(encoding="utf-8")
    try:
        parsed = ast.literal_eval(raw.strip())
        with sqlite3.connect(DB_PATH) as conn:
            existing = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
            if existing == 0:
                for q in parsed:
                    conn.execute("""
                        INSERT INTO questions (question, options, answer, information)
                        VALUES (?, ?, ?, ?)
                    """, (q["question"], str(q["options"]), q["answer"], q.get("information", "")))
                conn.commit()
    except Exception as e:
        st.error(f"Failed to parse quiz_data.json: {e}")

load_questions_from_json()

# === HELPERS ===
def get_all_questions():
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute("SELECT question, options, answer, information FROM questions").fetchall()
    return [{
        "question": row[0],
        "options": ast.literal_eval(row[1]),
        "answer": row[2],
        "information": row[3]
    } for row in result]

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

# === ADMIN INTERFACE ===
def admin_dashboard():
    st.title("🔐 Admin Dashboard")

    st.subheader("➕ Add New Question")
    q_text = st.text_area("Question")
    q_options = st.text_area("Options (comma-separated)")
    q_answer = st.text_input("Correct Answer")
    q_info = st.text_area("Extra Info (Optional)")
    if st.button("Add Question"):
        options = [o.strip() for o in q_options.split(",")]
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO questions (question, options, answer, information)
                VALUES (?, ?, ?, ?)
            """, (q_text, str(options), q_answer, q_info))
            conn.commit()
        st.success("Question added!")

    st.markdown("---")
    st.subheader("🗑 Remove Questions")
    questions = get_all_questions()
    for i, q in enumerate(questions):
        with st.expander(f"{i+1}. {q['question']}"):
            if st.button("Delete", key=f"del-{i}"):
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("DELETE FROM questions WHERE question = ?", (q["question"],))
                    conn.commit()
                st.rerun()

    st.markdown("---")
    st.subheader("🏆 Live Leaderboard")
    with sqlite3.connect(DB_PATH) as conn:
        data = conn.execute("SELECT name, score, total_time FROM results ORDER BY score DESC, total_time ASC").fetchall()
        for idx, (name, score, total_time) in enumerate(data, 1):
            st.write(f"**{idx}. {name}** — Score: {score}, Time: {total_time:.2f}s")

# === QUIZ UI ===
def run_quiz(questions):
    if st.session_state.current_index >= len(questions):
        st.title("🎉 Quiz Completed!")
        st.success(f"Score: {st.session_state.score} / {len(questions) * 10}")
        st.info(f"Time Taken: {round(st.session_state.total_time, 2)} sec")
        save_result()
        if st.button("🔁 Restart"):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.rerun()
        return

    question = questions[st.session_state.current_index]
    elapsed = round(time.time() - st.session_state.start_time)
    remaining = MAX_TIME - elapsed

    if not st.session_state.answer_submitted and remaining <= 0:
        st.toast("⏱ Time's up! Auto-submitting.")
        st.session_state.answer_submitted = True

    st.metric("Score", f"{st.session_state.score} / {len(questions) * 10}")
    st.warning(f"⏱ Time Left: {max(0, remaining)} sec")
    st.progress((st.session_state.current_index + 1) / len(questions))

    st.header(f"Q{st.session_state.current_index + 1}: {question['question']}")
    st.caption(question["information"])
    options = question["options"]
    correct_answer = question["answer"]

    if st.session_state.answer_submitted:
        st.write(f"You chose: {st.session_state.selected_option}")
        st.button("Next", on_click=next_question)
    else:
        for i, opt in enumerate(options):
            if st.button(opt, key=f"opt-{i}", use_container_width=True):
                st.session_state.selected_option = opt
        if st.session_state.selected_option:
            st.button("Submit", on_click=lambda: submit_answer(correct_answer))

def submit_answer(correct_answer):
    if st.session_state.selected_option == correct_answer:
        st.session_state.score += 10
    st.session_state.answer_submitted = True
    st.session_state.total_time += time.time() - st.session_state.start_time

def next_question():
    st.session_state.current_index += 1
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    st.session_state.start_time = time.time()

# === ENTRY GATE ===
if not st.session_state.name:
    st.title("🧠 IPL Quiz")
    st.subheader("Enter your name to begin")
    name_input = st.text_input("Name")
    if st.button("Enter"):
        if name_input.strip().lower() == "ecell_696969":
            st.session_state.name = name_input
            st.session_state.admin = True
            st.rerun()
        else:
            with sqlite3.connect(DB_PATH) as conn:
                exists = conn.execute("SELECT 1 FROM results WHERE name = ?", (name_input.strip(),)).fetchone()
            if exists:
                st.error("This name has already taken the quiz.")
            else:
                st.session_state.name = name_input.strip()
                st.session_state.admin = False
                st.rerun()

# === LAUNCH ===
if st.session_state.admin:
    admin_dashboard()
else:
    run_quiz(get_all_questions())

# === STYLING ===
st.markdown("""
<style>
button {
    border-radius: 8px;
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)
