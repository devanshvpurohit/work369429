def quiz_page():
    st.title("🏏 IPL Mega Quiz")

    name = st.text_input("Enter your name")
    password = st.text_input("Enter quiz password", type="password")

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if not password:
        st.warning("Please enter password to start.")
        return

    if password != "ECELL23951":
        st.error("Incorrect password!")
        return

    # === ADMIN MODE ===
    if name.upper() == "DEVANSH":
        st.markdown("### 👨‍💻 Admin Panel (Green & White Theme)")
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

        if "dynamic_questions" not in st.session_state:
            st.session_state.dynamic_questions = QUESTIONS.copy()

        # Add new question
        new_q = st.text_input("New Question")
        new_opts = st.text_input("Options (comma-separated)")
        new_ans = st.text_input("Correct Answer")

        if st.button("➕ Add Question") and new_q and new_opts and new_ans:
            options = [x.strip() for x in new_opts.split(",")]
            st.session_state.dynamic_questions.append({"q": new_q, "options": options, "answer": new_ans})
            st.success("Question added!")

        # Remove existing question
        to_remove = st.selectbox("Select question to remove", [q["q"] for q in st.session_state.dynamic_questions])
        if st.button("❌ Remove Question"):
            st.session_state.dynamic_questions = [q for q in st.session_state.dynamic_questions if q["q"] != to_remove]
            st.success("Question removed.")

        st.markdown('</div>', unsafe_allow_html=True)

        questions_to_ask = st.session_state.dynamic_questions

    else:
        questions_to_ask = QUESTIONS  # original 20 questions

    if st.button("Start Quiz") and name:
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()

    if st.session_state.quiz_started:
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

                # Show leaderboard preview
                df = load_data()
                top_df = df.sort_values(by=["score", "time_taken"], ascending=[False, True]).head(10)
                st.subheader("🏆 Top 10 Leaderboard")
                st.dataframe(top_df.reset_index(drop=True))
