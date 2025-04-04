import streamlit as st
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import ast

# ===== CONFIG =====
DB_PATH = "quiz.db"
QUIZ_PATH = Path("quiz_data.json")
MAX_TIME = 30

st.set_page_config(page_title="🧠 IPL Quiz", page_icon="🧠", layout="centered")

# ===== INIT DATABASE =====
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

# ===== LOAD QUIZ DATA =====
def load_questions():
    if not QUIZ_PATH.exists():
        st.error("❌ 'quiz_data.json' not found!")
        st.stop()
    raw = QUIZ_PATH.read_text(encoding='utf-8')
    try:
        return ast.literal_eval(raw)
    except Exception as e:
        st.error("❌ Error reading quiz data.")
        st.stop()

# ===== SAVE QUESTIONS TO DATABASE =====
def populate_questions_table(questions):
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if existing == 0:
            for q in questions:
                conn.execute("""
                    INSERT INTO questions (question, options, answer, information)
                    VALUES (?, ?, ?, ?)
                """, (q["question"], str(q["options"]), q["answer"], q.get("information", "")))
            conn.commit()

# ===== GET QUESTIONS FROM DB =====
def get_all_questions():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT * FROM questions").fetchall()
        questions = []
        for row in rows:
            questions.append({
                "id": row[0],
                "question": row[1],
                "options": ast.literal_eval(row[2]),
                "answer": row[3],
                "information": row[4]
            })
        return questions

# ===== SAVE RESULT =====
def save_result():
    with sqlite3.connect(DB_PATH) as conn:
        existing = conn.execute("SELECT 1 FROM results WHERE name = ?", (st.session_state.name,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE results SET score=?, total_time=?, timestamp=?, session_id=?
                WHERE name=?
            """, (
                st.session_state.score,
                round(st.session_state.total_time, 2),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                st.session_state.get("session_id", "unknown"),
                st.session_state.name
            ))
        else:
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

# ===== ADMIN UI =====
def admin_panel():
    st.title("🔐 Admin Dashboard")

    st.subheader("📋 Add New Question")
    q = st.text_area("Question")
    options = st.text_area("Options (comma separated)")
    ans = st.text_input("Correct Answer")
    info = st.text_area("Extra Info (optional)")

    if st.button("➕ Add Question"):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    INSERT INTO questions (question, options, answer, information)
                    VALUES (?, ?, ?, ?)
                """, (q, str([x.strip() for x in options.split(",")]), ans.strip(), info.strip()))
                conn.commit()
            st.success("Question added!")
        except Exception as e:
            st.error("Failed to add question.")

    st.markdown("---")
    st.subheader("🗑️ Remove Questions")

    all_q = get_all_questions()
    for item in all_q:
        with st.expander(f"{item['question']}"):
            if st.button(f"Delete Question #{item['id']}", key=f"del-{item['id']}"):
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("DELETE FROM questions WHERE id = ?", (item["id"],))
                    conn.commit()
                st.success("Question deleted.")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 Real-Time Leaderboard")

    with sqlite3.connect(DB_PATH) as conn:
        results = conn.execute("""
            SELECT name, score, total_time, timestamp FROM results
            ORDER BY score DESC, total_time ASC
        """).fetchall()

    st.table(results)

# ===== QUIZ FLOW =====
def run_quiz(quiz_data):
    if not st.session_state.name:
        st.title("🧠 Welcome to the IPL Quiz")
        name = st.text_input("Enter your name to begin")
        if st.button("Start"):
            if name.lower().strip() == "ecell_696969":
                st.session_state.name = name
                st.session_state.admin = True
                st.rerun()
            else:
                with sqlite3.connect(DB_PATH) as conn:
                    exists = conn.execute("SELECT 1 FROM results WHERE name = ?", (name,)).fetchone()
                if exists:
                    st.error("Name already used. Try a different one.")
                else:
                    st.session_state.name = name
                    st.session_state.admin = False
                    st.session_state.session_id = st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]
                    st.session_state.current_index = 0
                    st.session_state.score = 0
                    st.session_state.total_time = 0
                    st.session_state.selected_option = None
                    st.session_state.answer_submitted = False
                    st.session_state.start_time = time.time()
                    st.rerun()
        return

    if st.session_state.admin:
        admin_panel()
        return

    questions = quiz_data
    idx = st.session_state.current_index

    if idx >= len(questions):
        st.balloons()
        st.title("✅ Quiz Finished!")
        st.success(f"Score: {st.session_state.score} / {len(questions) * 10}")
        st.info(f"Time: {round(st.session_state.total_time, 2)} sec")
        save_result()
        if st.button("Restart"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
        return

    q = questions[idx]
    elapsed = time.time() - st.session_state.start_time
    remaining = MAX_TIME - int(elapsed)

    if not st.session_state.answer_submitted and remaining <= 0:
        st.toast("⏱ Time's up! Auto-submitting.")
        st.session_state.answer_submitted = True

    st.title("🧠 IPL Quiz")
    st.metric("Score", f"{st.session_state.score} / {len(questions)*10}")
    st.warning(f"⏱ Time Left: {max(0, remaining)} sec")
    st.progress((idx + 1) / len(questions))

    st.header(f"Q{idx+1}: {q['question']}")
    st.caption(q.get("information", ""))
    st.markdown("---")

    options = q["options"]
    correct = q["answer"]

    if st.session_state.answer_submitted:
        st.markdown("### You selected:")
        st.info(st.session_state.selected_option or "No answer")
    else:
        for i, opt in enumerate(options):
            if st.button(opt, key=f"opt-{i}"):
                st.session_state.selected_option = opt

    def submit():
        if st.session_state.selected_option == correct:
            st.session_state.score += 10
        st.session_state.answer_submitted = True
        st.session_state.total_time += time.time() - st.session_state.start_time

    def next_q():
        st.session_state.current_index += 1
        st.session_state.selected_option = None
        st.session_state.answer_submitted = False
        st.session_state.start_time = time.time()

    if st.session_state.answer_submitted:
        st.button("➡️ Next", on_click=next_q)
    else:
        st.button("🚀 Submit", on_click=submit)

# ===== MAIN EXECUTION =====
init_db()
populate_questions_table(load_questions())
run_quiz(get_all_questions())
