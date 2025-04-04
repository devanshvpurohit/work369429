import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from threading import Lock

EXCEL_FILE = 'quiz_scores.xlsx'
LOCK = Lock()

# === UTILITIES ===
@st.cache_data
def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Score", "IP", "TimeTaken", "Date"])

def save_data_row(new_row_df):
    with LOCK:
        if os.path.exists(EXCEL_FILE):
            existing_df = pd.read_excel(EXCEL_FILE)
            full_df = pd.concat([existing_df, new_row_df], ignore_index=True)
        else:
            full_df = new_row_df
        with pd.ExcelWriter(EXCEL_FILE, engine='xlsxwriter') as writer:
            full_df.to_excel(writer, index=False)

def get_client_ip():
    return st.runtime.scriptrunner.get_script_run_ctx().session_id[-6:]  # pseudonymous unique ID

# === QUIZ PAGE ===
def quiz_page():
    st.title("🏏 IPL Quiz")
    name = st.text_input("Enter your name")

    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False

    if st.button("Start Quiz") and name:
        st.session_state.quiz_started = True
        st.session_state.start_time = time.time()

    if st.session_state.quiz_started:
        with st.form("quiz_form"):
            q1 = st.radio("Who won IPL 2023?", ["GT", "CSK", "MI"])
            q2 = st.radio("Who scored most runs in IPL 2023?", ["Shubman Gill", "Virat Kohli", "Ruturaj Gaikwad"])
            submit = st.form_submit_button("Submit")

            if submit:
                end_time = time.time()
                time_taken = round(end_time - st.session_state.start_time, 2)

                score = 0
                if q1 == "CSK": score += 1
                if q2 == "Shubman Gill": score += 1

                today = datetime.now().strftime("%Y-%m-%d")
                ip = get_client_ip()

                new_row = pd.DataFrame([[name, score, ip, time_taken, today]],
                                       columns=["Name", "Score", "IP", "TimeTaken", "Date"])
                save_data_row(new_row)

                st.success(f"✅ {name}, you scored {score}/2")
                st.info(f"⏱️ Time Taken: {time_taken} seconds")

                st.session_state.quiz_started = False

                # Show leaderboard preview
                df = load_data()
                top_df = df.sort_values(by=["Score", "TimeTaken"], ascending=[False, True]).head(10)
                st.subheader("🏆 Top 10 Leaderboard")
                st.dataframe(top_df.reset_index(drop=True))

# === LEADERBOARD PAGE ===
def leaderboard_page():
    st.title("📊 Public Leaderboard")
    df = load_data()

    if df.empty:
        st.warning("No quiz attempts yet.")
        return

    filter_date = st.selectbox("📅 Filter by date:", ["All"] + sorted(df["Date"].dropna().unique().tolist()))
    if filter_date != "All":
        df = df[df["Date"] == filter_date]

    name_filter = st.text_input("🔍 Search name")
    if name_filter:
        df = df[df["Name"].str.contains(name_filter, case=False, na=False)]

    tab1, tab2 = st.tabs(["🏅 Highest Scores", "⚡ Fastest Perfect Scores"])

    with tab1:
        top = df.sort_values(by=["Score", "TimeTaken"], ascending=[False, True]).head(20)
        st.dataframe(top.reset_index(drop=True))

    with tab2:
        perfect = df[df["Score"] == df["Score"].max()]
        fast = perfect.sort_values(by="TimeTaken").head(20)
        st.dataframe(fast.reset_index(drop=True))

# === MAIN APP ===
def main():
    st.set_page_config(page_title="IPL Quiz", layout="centered")
    choice = st.sidebar.radio("📚 Menu", ["Take Quiz", "Leaderboard"])

    if choice == "Take Quiz":
        quiz_page()
    else:
        leaderboard_page()

if __name__ == "__main__":
    main()
