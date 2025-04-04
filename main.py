import streamlit as st
import time

# === Placeholder: Replace with your actual question list ===
QUESTIONS = [
    {"q": "Who won the IPL 2023?", "options": ["GT", "MI", "CSK", "RR"], "answer": "CSK"},
    {"q": "Who holds the orange cap in IPL 2023?", "options": ["Gill", "Kohli", "Warner", "Buttler"], "answer": "Gill"},
    # Add more static questions here...
]

# === Placeholder: Replace with your actual functions ===
def get_user_id():
    return "IP_PLACEHOLDER"

def insert_score(name, score, ip, time_taken):
    print(f"Inserted: {name}, {score}, {ip}, {time_taken}")

def load_data():
    import pandas as pd
    # Simulate leaderboard data
    return pd.DataFrame([
        {"name": "Player1", "score": 15, "time_taken": 42.5},
        {"name": "Player2", "score": 17, "time_taken": 38.2},
        {"name": "Player3", "score": 16, "time_taken": 40.1},
    ])

# === MAIN QUIZ FUNCTION ===
def quiz_page():
    st.title("🏏 IPL Mega Quiz")

    name = st.text_input("Enter your name")
    email = st.text_input("Enter your Gmail (for verification)")
    password = st.text_input("Enter quiz password", type="password")

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if "global_questions" not in st.session_state:
        st.session_state.global_questions = QUESTIONS.copy()

    if not password:
        st.warning("Please enter the quiz password to proceed.")
        return

    if password != "ECELL23951":
        st.error("Incorrect password!")
        return

    if email and not email.endswith("@gmail.com"):
        st.warning("Please use a valid Gmail address ending with @gmail.com")
        return

    # === ADMIN PANEL ===
    if name.strip().upper() == "DEVANSH":
        st.markdown("### 👨‍💻 Admin Panel")
        st.markdown(
            """
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
            """,
            unsafe_allow_html=True
        )
        st.markdown('<div class="admin-box">', unsafe_allow_html=True)
        st.markdown('<div class="admin-title">Question Editor</div>', unsafe_allow_html=True)

        new_q = st.text_input("New Question")
        new_opts = st.text_input("Options (comma-separated)")
        new_ans = st.text_input("Correct Answer")

        if st.button("➕ Add Question") and new_q and new_opts and new_ans:
            options = [opt.strip() for opt in new_opts.split(",")]
            st.session_state.global_questions.append({"q": new_q, "options": options, "answer": new_ans})
            st.success("✅ Question added for all users!")

        if st.session_state.global_questions:
            to_remove = st.selectbox("Select question to remove", [q["q"] for q in st.session_state.global_questions])
            if st.button("❌ Remove Selected Question"):
                st.session_state.global_questions = [
                    q for q in st.session_state.global_questions if q["q"] != to_remove
                ]
                st.success("🗑️ Question removed globally.")

        st.markdown('</div>', unsafe_allow_html=True)

    # === Start Quiz Button ===
    if st.button("Start Quiz") and name and email:
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()

    # === Quiz Form ===
    if st.session_state.quiz_started:
        questions = st.session_state.global_questions

        with st.form("quiz_form"):
            user_answers = []
            for idx, q in enumerate(questions):
                answer = st.radio(f"Q{idx+1}: {q['q']}", q["options"], key=f"q_{idx}")
                user_answers.append(answer)

            submit = st.form_submit_button("Submit")

            if submit:
                end_time = time.time()
                time_taken = round(end_time - st.session_state.start_time, 2)
                score = sum(1 for i, ans in enumerate(user_answers) if ans == questions[i]["answer"])

                ip = get_user_id()
                insert_score(name, score, ip, time_taken)

                st.success(f"✅ {name}, you scored {score}/{len(questions)}")
                st.info(f"⏱️ Time Taken: {time_taken} seconds")

                st.session_state.quiz_started = False
                st.cache_data.clear()

                # Show leaderboard
                df = load_data()
                top_df = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
                st.subheader("🏆 Top 10 Leaderboard")
                st.dataframe(top_df.reset_index(drop=True))

# === Run the App ===
quiz_page()
