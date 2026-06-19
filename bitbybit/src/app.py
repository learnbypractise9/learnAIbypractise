# Import packages
import streamlit as st
import json
import random
import re
import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
 
# ---------------------------------------------------------
# Configuration variables
# ---------------------------------------------------------
st.set_page_config(page_title="BitByBit", page_icon="⚡", layout="centered")
 
TOPICS = ["Data Science", "Data Engineering", "Machine Learning", "Gen AI"]
DIFFICULTY_LABELS = {
    1: "Easiest",
    2: "Easy",
    3: "Medium",
    4: "Hard",
    5: "Expert",
}
POINTS_PER_QUESTION = 5
TOTAL_QUESTIONS = 7
POOL_SIZE = 15
 
client = Groq()             # Groq LLMs

# ---------------------------------------------------------
# System Prompt Generation
# ---------------------------------------------------------
system_prompt = """You are a technical quiz question generator for a learning app called BitByBit.
 
You MUST respond with ONLY valid JSON, no markdown fences, no preamble, no commentary.
 
Output format:
{
  "questions": [
    {
      "question": "string",
      "options": ["opt1", "opt2", "opt3", "opt4", "opt5"],
      "correct_index": 0,
      "explanation": "short 1-3 sentence explanation of the underlying concept"
    },
    ... (exactly 15 items)
  ]
}
 
Rules:
- Generate exactly 15 UNIQUE multiple choice questions.
- Each question must have exactly 5 options, with exactly one correct answer indicated by correct_index (0-based).
- Vary question phrasing, structure (definition-based, scenario-based, comparison-based, code-output-based, "which of the following" style) so the set does not feel repetitive.
- Do not repeat the same underlying concept twice in the 15 questions.
- Match the difficulty level strictly: levels closer to 1 should test basic definitions/recall, levels closer to 5 should test deep, nuanced, or edge-case understanding.
- The explanation should teach the core concept briefly, regardless of whether the user got it right.
"""

# ---------------------------------------------------------
# Function definitions
# ---------------------------------------------------------
def build_user_prompt(topic: str, difficulty: int):
    seed = random.randint(1, 1_000_000)
    concept_pool = [
        "real-world scenarios",
        "comparisons between related concepts",
        "common misconceptions",
        "practical code or pipeline behavior",
        "definitions and terminology",
        "trade-offs between approaches",
        "debugging or troubleshooting situations",
    ]
    chosen_concept = random.sample(concept_pool, k=3)
    return f"""Generate {POOL_SIZE} unique multiple-choice questions for the topic "{topic}" at difficulty level {difficulty} (1=Easiest, 5=Expert).
    Randomness seed: {seed} (use this to vary question selection/style from prior runs, do not mention the seed in output).
    Create a mix of concepts such as: {", ".join(chosen_concept)}.
    Return ONLY the JSON object described in the system prompt."""

def generate_question_pool(topic: str, difficulty: int):
    user_prompt = build_user_prompt(topic, difficulty)
    response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ],
    model="openai/gpt-oss-120b",
    max_completion_tokens=4000,
    temperature=1.0,
    stream=False
)
    data = json.loads(response.choices[0].message.content)
    questions = data.get("questions", [])
    for i, q in enumerate(questions):
        q["id"] = i
    return questions

# ---------------------------------------------------------
# Set Initial state
# ---------------------------------------------------------
def reset_state():
    st.session_state.stage = "setup"          
    st.session_state.topic = None
    st.session_state.difficulty = None
    st.session_state.questions = []            
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.locked = {}              
    st.session_state.selected_answer = {}       
    st.session_state.answer_correct = {}       

if "stage" not in st.session_state:
    reset_state()

# ---------------------------------------------------------
# UI: Setup Stage
# ---------------------------------------------------------

def inital_setup():
    st.title("⚡ BitByBit")
    st.caption("Pick a topic, choose your difficulty and test your knowledge.")
    topic = st.selectbox("Select a topic", TOPICS)
    diff_level = st.select_slider(f"Select difficulty level for {topic}",
                                  options = list(DIFFICULTY_LABELS.keys()),
                                  format_func=lambda x: DIFFICULTY_LABELS[x],
                                  value = 1)
    if st.button("Start Quiz", type="primary"):
        with st.spinner("Generating your quiz..."):
            try:
                pool = generate_question_pool(topic, diff_level)
                st.text(pool)
            except Exception as e:
                st.error(f"Failed to generate questions: {e}")
                return
            sampled_questions = random.sample(pool, TOTAL_QUESTIONS)
            random.shuffle(sampled_questions)
            st.session_state.topic = topic
            st.session_state.difficulty = diff_level
            st.session_state.questions = sampled_questions
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.locked = {q["id"]: False for q in sampled_questions}
            st.session_state.selected_answer = {q["id"]: None for q in sampled_questions}
            st.session_state.answer_correct = {q["id"]: False for q in sampled_questions}
            st.session_state.stage = "quiz"
            st.rerun()
# ---------------------------------------------------------
# UI: Quiz Stage
# ---------------------------------------------------------
def start_quiz():
    idx = st.session_state.current_index
    questions = st.session_state.questions
    q = questions[idx]
    qid = q["id"]

    st.subheader(f"{st.session_state.topic} • {DIFFICULTY_LABELS[st.session_state.difficulty]}")
    st.progress((idx) / TOTAL_QUESTIONS, text=f"Question {idx + 1} of {TOTAL_QUESTIONS}")
    st.markdown(f"### {q['question']}")

    is_locked = st.session_state.locked[qid]

    selected_ans = st.radio(
        "Choose answer:",
        options=list(range(len(q["options"]))),
        format_func=lambda i: q["options"][i],
        index=st.session_state.selected_answer[qid],
        disabled=is_locked,
        key=f"radio_{qid}",
    )
    if not is_locked:
        if st.button("Submit", type="primary"):
            st.session_state.selected_answer[qid] = selected_ans
            correct = selected_ans == q["correct_index"]
            st.session_state.answer_correct[qid] = correct
            if correct:
                st.session_state.score += POINTS_PER_QUESTION
            st.session_state.locked[qid] = True
            st.rerun()
    else:
        correct_idx = q["correct_index"]
        if st.session_state.answer_correct[qid]:
            st.success(f"Correct! ✅ (+{POINTS_PER_QUESTION} points)")
        else:
            st.error(f"Incorrect. The correct answer was: **{q['options'][correct_idx]}**")
 
        st.info(f"**Concept:** {q['explanation']}")

        if idx + 1 < TOTAL_QUESTIONS:
            if st.button("Next Question →"):
                st.session_state.current_index += 1
                st.rerun()
        else:
            if st.button("See Final Score →"):
                st.session_state.stage = "result"
                st.rerun()

# ---------------------------------------------------------
# UI: Result Stage
# ---------------------------------------------------------
def display_result():
    st.title("🏁 Quiz Complete!")
    max_score = TOTAL_QUESTIONS * POINTS_PER_QUESTION
    score = st.session_state.score
 
    st.metric("Final Score", f"{score} / {max_score}")
    st.progress(score / max_score)
 
    pct = score / max_score
    if pct == 1.0:
        st.balloons()
        st.success("Perfect score! Outstanding work. 🎉")
    elif pct >= 0.7:
        st.success("Great job! Solid understanding of the topic.")
    elif pct >= 0.4:
        st.warning("Decent effort — review the explanations and try again.")
    else:
        st.error("Keep practicing — revisit the basics and try another round.")
 
    if st.button("🔄 New Quiz", type="primary"):
        reset_state()
        st.rerun()

if st.session_state.stage == "setup":
    inital_setup()
elif st.session_state.stage == "quiz":
    start_quiz()
elif st.session_state.stage == "result":
    display_result()