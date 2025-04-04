import streamlit as st
import json
from pathlib import Path
import time
import os

# ==== App Setup ====
st.set_page_config(page_title="🧠 Quiz Master", page_icon="❓", layout="centered")

# ==== Load Quiz Data ====
QUIZ_PATH = Path("quiz_data.json")

if not QUIZ_PATH.exists():
    st.error("❌ 'quiz_data.json' not found. Please upload it to the same folder as 'main.py'.")
    st.stop()

with QUIZ_PATH.open(encoding="utf-8") as f:
    quiz_data = json.load(f)

# ==== Initialize State ====
default_values = {
    'current_index': 0,
    'score': 0,
    'selected_option': None,
    'answer_submitted': False,
    'start_time': time.time()
}
for key, val in default_values.items():
    st.session_state.setdefault(key, val)

def restart_quiz():
    for key in default_values:
        st.session_state[key] = default_values[key]

def submit_answer(auto=False):
    st.session_state.answer_submitted = True
    if st.session_state.selected_option == quiz_data[st.session_state.current_index]['answer']:
        st.session_state.score += 10
    if auto:
        st.toast("⏳ Time's up! Auto-submitted.", icon="⏰")

def next_question():
    st.session_state.current_index += 1
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    st.session_state.start_time = time.time()

# ==== Completion Check ====
if st.session_state.current_index >= len(quiz_data):
    st.balloons()
    st.title("🎉 Quiz Completed!")
    st.success(f"Your final score is {st.session_state.score} / {len(quiz_data) * 10}")
    if st.button("🔁 Restart Quiz"):
        restart_quiz()
    st.stop()

# ==== Question Logic ====
question = quiz_data[st.session_state.current_index]
elapsed = round(time.time() - st.session_state.start_time)
remaining = 30 - elapsed

if not st.session_state.answer_submitted and remaining <= 0:
    submit_answer(auto=True)
    time.sleep(1)
    st.experimental_rerun()

# ==== UI Layout ====
st.title("🧠 Streamlit Quiz")
st.metric("Score", f"{st.session_state.score} / {len(quiz_data)*10}")
st.progress((st.session_state.current_index + 1) / len(quiz_data))

st.header(f"Question {st.session_state.current_index + 1}")
st.subheader(question["question"])
st.caption(question.get("information", ""))
st.markdown("---")

st.warning(f"⏱ Time Left: {max(0, remaining)} seconds")

# ==== Options ====
options = question["options"]
correct_answer = question["answer"]

if st.session_state.answer_submitted:
    for option in options:
        if option == correct_answer:
            st.success(f"✅ {option}")
        elif option == st.session_state.selected_option:
            st.error(f"❌ {option}")
        else:
            st.write(option)
else:
    for i, option in enumerate(options):
        if st.button(option, key=f"opt-{i}", use_container_width=True):
            st.session_state.selected_option = option

st.markdown("---")

# ==== Navigation Buttons ====
if st.session_state.answer_submitted:
    if st.session_state.current_index < len(quiz_data) - 1:
        st.button("➡️ Next", on_click=next_question)
    else:
        st.button("✅ Finish", on_click=next_question)
else:
    st.button("🚀 Submit", on_click=submit_answer)

# ==== Custom Button Styling ====
st.markdown("""
<style>
div.stButton > button {
    margin: 5px auto;
    width: 100%;
    font-size: 18px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)
