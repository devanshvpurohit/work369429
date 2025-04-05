import streamlit as st
from pathlib import Path
import ast

# === PATH TO QUIZ FILE ===
QUIZ_FILE = Path(__file__).parent / "quiz_data.json"

# === LOAD QUIZ DATA ===
def load_quiz_data():
    with open(QUIZ_FILE, "r") as f:
        return ast.literal_eval(f.read())

# === SAVE QUIZ DATA ===
def save_quiz_data(data):
    with open(QUIZ_FILE, "w") as f:
        f.write(str(data))  # Store as valid Python list syntax

# === ADMIN PAGE ===
def admin_page():
    st.set_page_config(page_title="Admin | Edit Quiz", layout="centered")
    st.title("🛠 Admin Quiz Editor")

    password = st.text_input("Enter Admin Password", type="password")
    if password != "ecell_696969":
        st.warning("🔒 Access Denied")
        return

    quiz_data = load_quiz_data()

    # === ADD NEW QUESTION ===
    st.subheader("➕ Add New Question")
    new_question = st.text_input("Question")
    new_options = st.text_area("Options (comma separated)")
    new_answer = st.text_input("Correct Answer (must match one of the options)")

    if st.button("Add Question"):
        options = [opt.strip() for opt in new_options.split(",") if opt.strip()]
        if new_question and options and new_answer in options:
            quiz_data.append({"question": new_question, "options": options, "answer": new_answer})
            save_quiz_data(quiz_data)
            st.success("✅ Question added!")
            st.rerun()
        else:
            st.error("❌ Please ensure all fields are filled correctly.")

    # === EDIT EXISTING QUESTIONS ===
    st.subheader("✏️ Edit Existing Questions")
    for i, q in enumerate(quiz_data):
        with st.expander(f"Q{i+1}: {q['question']}"):
            updated_question = st.text_input(f"Edit Question {i+1}", value=q["question"], key=f"q{i}")
            updated_options = st.text_area(f"Edit Options {i+1}", value=", ".join(q["options"]), key=f"opts{i}")
            updated_answer = st.text_input(f"Edit Answer {i+1}", value=q["answer"], key=f"ans{i}")

            col1, col2 = st.columns(2)
            if col1.button("💾 Save", key=f"save{i}"):
                opts = [o.strip() for o in updated_options.split(",") if o.strip()]
                if updated_answer in opts:
                    quiz_data[i] = {
                        "question": updated_question,
                        "options": opts,
                        "answer": updated_answer
                    }
                    save_quiz_data(quiz_data)
                    st.success("✅ Question updated!")
                    st.rerun()
                else:
                    st.error("❌ Answer must be in options.")

            if col2.button("🗑 Delete", key=f"delete{i}"):
                quiz_data.pop(i)
                save_quiz_data(quiz_data)
                st.warning("❌ Question deleted.")
                st.rerun()

    st.info(f"📦 Total Questions: {len(quiz_data)}")

# === MAIN ===
if __name__ == "__main__":
    admin_page()
