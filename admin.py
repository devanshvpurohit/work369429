import streamlit as st
import sqlite3
import json
from pathlib import Path

# ===== CONFIG =====
DB_PATH = "quiz.db"
QUIZ_PATH = Path("quiz_data.json")
ADMIN_PASSWORD = "ipl2025"  # Set a secure password here

st.set_page_config(page_title="🛠️ Admin Panel", layout="wide")

# ===== AUTH =====
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.title("🔐 Admin Login")
    pwd = st.text_input("Enter Admin Password", type="password")
    if st.button("Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.success("Access granted")
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    st.stop()

# ===== UTILS =====
def load_quiz():
    if QUIZ_PATH.exists():
        with QUIZ_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_quiz(data):
    with QUIZ_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def fetch_leaderboard():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS results (
                name TEXT PRIMARY KEY,
                score INTEGER,
                total_time REAL,
                timestamp TEXT,
                session_id TEXT
            )""")
            rows = conn.execute("""
                SELECT name, score, total_time, timestamp
                FROM results
                ORDER BY score DESC, total_time ASC
            """).fetchall()
        return rows
    except Exception as e:
        st.error(f"Error fetching leaderboard: {e}")
        return []

# ===== TABS =====
tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard", "📝 Edit Questions", "➕ Add Question"])

# ===== TAB 1: LEADERBOARD =====
with tab1:
    st.subheader("🏆 Live Leaderboard")
    data = fetch_leaderboard()
    if data:
        st.table([{"Name": r[0], "Score": r[1], "Time (s)": round(r[2], 2), "Timestamp": r[3]} for r in data])
    else:
        st.info("No entries yet.")

# ===== TAB 2: EDIT QUESTIONS =====
with tab2:
    st.subheader("✏️ Edit or Delete Questions")
    quiz_data = load_quiz()

    if not quiz_data:
        st.warning("No questions found.")
    else:
        for idx, q in enumerate(quiz_data):
            with st.expander(f"Q{idx+1}: {q['question'][:60]}..."):
                question = st.text_area("Question", q["question"], key=f"q-{idx}")
                info = st.text_area("Information", q.get("information", ""), key=f"info-{idx}")
                opts = [st.text_input(f"Option {i+1}", q["options"][i], key=f"opt-{idx}-{i}") for i in range(4)]
                answer = st.selectbox("Correct Answer", opts, index=opts.index(q["answer"]), key=f"ans-{idx}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save", key=f"save-{idx}"):
                        quiz_data[idx] = {
                            "question": question.strip(),
                            "information": info.strip(),
                            "options": opts,
                            "answer": answer
                        }
                        save_quiz(quiz_data)
                        st.success("✅ Saved")
                        st.rerun()
                with col2:
                    if st.button("❌ Delete", key=f"del-{idx}"):
                        quiz_data.pop(idx)
                        save_quiz(quiz_data)
                        st.warning("🗑️ Deleted")
                        st.rerun()

# ===== TAB 3: ADD QUESTIONS =====
with tab3:
    st.subheader("➕ Add New Question")
    new_q = st.text_area("Question")
    new_opts = [st.text_input(f"Option {i+1}", key=f"new-opt-{i}") for i in range(4)]
    new_ans = st.selectbox("Correct Answer", new_opts, key="new-answer")
    new_info = st.text_area("Information (optional)", key="new-info")

    if st.button("✅ Add"):
        if not new_q or any(opt.strip() == "" for opt in new_opts):
            st.error("Please fill in all fields.")
        else:
            quiz_data = load_quiz()
            quiz_data.append({
                "question": new_q.strip(),
                "options": new_opts,
                "answer": new_ans,
                "information": new_info.strip()
            })
            save_quiz(quiz_data)
            st.success("Question added.")
            st.rerun()
