import streamlit as st
import sqlite3
import pandas as pd
import time
from datetime import datetime

DB_FILE = "quiz.db"

# === Sample 20 IPL questions and answers ===
QUESTIONS = [
    {"q": "Who won IPL 2023?", "options": ["GT", "CSK", "MI"], "answer": "CSK"},
    {"q": "Who scored most runs in IPL 2023?", "options": ["Shubman Gill", "Virat Kohli", "Ruturaj Gaikwad"], "answer": "Shubman Gill"},
    {"q": "Which team has won the most IPL titles?", "options": ["CSK", "MI", "RCB"], "answer": "MI"},
    {"q": "Who has taken most wickets in IPL history?", "options": ["Lasith Malinga", "Dwayne Bravo", "Yuzvendra Chahal"], "answer": "Yuzvendra Chahal"},
    {"q": "Which team plays at Eden Gardens?", "options": ["KKR", "RR", "PBKS"], "answer": "KKR"},
    {"q": "What does 'DC' stand for?", "options": ["Delhi Capitals", "Delhi Chargers", "Daredevil Capitals"], "answer": "Delhi Capitals"},
    {"q": "Who hit 6 sixes in an over in IPL?", "options": ["Yuvraj Singh", "Kieron Pollard", "Ruturaj Gaikwad"], "answer": "Ruturaj Gaikwad"},
    {"q": "What is the maximum overs a bowler can bowl in an IPL match?", "options": ["4", "5", "10"], "answer": "4"},
    {"q": "Which IPL team is called the 'Orange Army'?", "options": ["SRH", "MI", "CSK"], "answer": "SRH"},
    {"q": "Who was the captain of CSK in 2023?", "options": ["MS Dhoni", "Ruturaj Gaikwad", "Ravindra Jadeja"], "answer": "MS Dhoni"},
    {"q": "Who was the most expensive player in IPL 2023 auction?", "options": ["Sam Curran", "Ben Stokes", "Cameron Green"], "answer": "Sam Curran"},
    {"q": "Who hit the longest six in IPL 2023?", "options": ["Faf du Plessis", "Tim David", "Nicholas Pooran"], "answer": "Faf du Plessis"},
    {"q": "Which Indian bowler took a hat-trick in IPL 2023?", "options": ["Yuzvendra Chahal", "Tushar Deshpande", "Rashid Khan"], "answer": "Rashid Khan"},
    {"q": "What color cap is awarded to highest run scorer?", "options": ["Orange", "Purple", "Green"], "answer": "Orange"},
    {"q": "Which team plays at Wankhede Stadium?", "options": ["MI", "RCB", "DC"], "answer": "MI"},
    {"q": "Who was the youngest player to debut in IPL 2023?", "options": ["Nitish Reddy", "Rinku Singh", "Tilak Varma"], "answer": "Nitish Reddy"},
    {"q": "What does DRS stand for?", "options": ["Decision Review System", "Direct Replay System", "Delhi Replay System"], "answer": "Decision Review System"},
    {"q": "Which team did not qualify for IPL 2023 playoffs?", "options": ["MI", "RCB", "CSK"], "answer": "RCB"},
    {"q": "Which cricketer has played for both CSK and MI?", "options": ["Ambati Rayudu", "Rohit Sharma", "Hardik Pandya"], "answer": "Ambati Rayudu"},
    {"q": "How many foreign players allowed in IPL playing XI?", "options": ["4", "3", "5"], "answer": "4"}
]

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

@st.cache_data(ttl=10)
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql_query("SELECT * FROM scores", conn)

def insert_score(name, score, ip, time_taken):
    date = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO scores (name, score, ip, time_taken, date) VALUES (?, ?, ?, ?, ?)",
                     (name, score, ip, time_taken, date))
        conn.commit()

def get_user_id():
    return st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]

def quiz_page():
    st.title("\U0001F3CF IPL Mega Quiz")
    name = st.text_input("Enter your name")
    password = st.text_input("Enter quiz password", type="password")

    if not password:
        st.warning("Please enter password to start.")
        return

    if password != "ECELL23951":
        st.error("Incorrect password!")
        return

    if name.upper() == "DEVANSH":
        st.markdown("### \U0001F468‍\U0001F4BB Admin Panel (Green & White Theme)")
        st.markdown("""
        <style>
            .admin-box {
                background-color: #e8f5e9;
                border-left: 6px solid #4caf50;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 10px;
                color: #1b5e20;
            }
            .admin-title {
                font-size: 20px;
                font-weight: bold;
            }
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="admin-box">', unsafe_allow_html=True)
        st.markdown('<div class="admin-title">Question Editor</div>', unsafe_allow_html=True)

        if "dynamic_questions" not in st.session_state:
            st.session_state.dynamic_questions = QUESTIONS.copy()

        new_q = st.text_input("New Question")
        new_opts = st.text_input("Options (comma-separated)")
        new_ans = st.text_input("Correct Answer")

        if st.button("➕ Add Question") and new_q and new_opts and new_ans:
            options = [x.strip() for x in new_opts.split(",")]
            st.session_state.dynamic_questions.append({"q": new_q, "options": options, "answer": new_ans})
            st.success("Question added!")

        to_remove = st.selectbox("Select question to remove", [q["q"] for q in st.session_state.dynamic_questions])
        if st.button("❌ Remove Question"):
            st.session_state.dynamic_questions = [q for q in st.session_state.dynamic_questions if q["q"] != to_remove]
            st.success("Question removed.")

        st.markdown('</div>', unsafe_allow_html=True)
        questions_to_ask = st.session_state.dynamic_questions
    else:
        questions_to_ask = QUESTIONS

    if st.button("Start Quiz") and name:
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()

    if st.session_state.get("quiz_started"):
        with st.form("quiz_form"):
            user_answers = []
            for idx, q in enumerate(questions_to_ask):
                answer = st.radio(f"Q{idx+1}: {q['q']}", q["options"], key=f"q_{idx}")
                user_answers.append(answer)
            submit = st.form_submit_button("Submit")

            if submit:
                end_time = time.time()
                time_taken = round(end_time - st.session_state.start_time, 2)
                score = sum(1 for i, ans in enumerate(user_answers) if ans == questions_to_ask[i]["answer"])

                ip = get_user_id()
                insert_score(name, score, ip, time_taken)

                st.success(f"✅ {name}, you scored {score}/{len(questions_to_ask)}")
                st.info(f"⏱️ Time Taken: {time_taken} seconds")
                st.session_state.quiz_started = False
                st.cache_data.clear()

                df = load_data()
                top_df = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
                st.subheader("\U0001F3C6 Top 10 Leaderboard")
                st.dataframe(top_df.reset_index(drop=True))

def leaderboard_page():
    st.title("\U0001F4CA Public Leaderboard")
    df = load_data()

    if df.empty:
        st.warning("No scores recorded yet.")
        return

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
