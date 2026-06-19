# bitBybit ⚡

A Streamlit-based technical quiz portal. Pick a topic, choose a difficulty level, and test your knowledge with LLM-generated multiple-choice questions.

## Features

- Topics: Data Science, Data Engineering, Machine Learning, Gen AI
- Difficulty levels 1 (Easiest) to 5 (Expert)
- LLM generates 15 unique questions per round; 7 are randomly sampled and shown in random order
- Each question has 5 options; correct answer = +5 points
- Answers lock after submission — no changing your mind
- Concept explanation shown after each answer
- Final score out of 35 after question 7
- "New Quiz" resets everything

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/bitBybit.git
   cd bitBybit
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set your Anthropic API key:
   ```bash
   cp .env.example .env
   # edit .env and add your key
   ```

   Or export directly:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

4. Run the app:
   ```bash
   streamlit run app.py
   ```

5. Open the local URL shown in the terminal (usually `http://localhost:8501`).

## Project Structure

```
bitBybit/
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
├── .env.example        # Sample environment file
├── .gitignore
└── README.md
```

## How it works

1. User selects topic + difficulty → "Start Quiz".
2. App calls the Anthropic API with a JSON-only system prompt to generate 15 unique MCQs (with randomized phrasing/angles per call for variety).
3. 7 questions are randomly sampled and shuffled for the session.
4. Each question is answered, locked, and explained one at a time.
5. After question 7, total score is shown with a "New Quiz" reset option.

## Tech Stack

- [Streamlit](https://streamlit.io/) — frontend & app framework
- [Anthropic API](https://docs.claude.com/) — question generation (Claude Sonnet)
