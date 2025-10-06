# 🤖 GitHub Copilot Guide for the Trending Intelligence Project

**Purpose:**  
To help all developers in this project use GitHub Copilot effectively for writing, maintaining, and extending the AI-driven post analysis system.

---

## 🧠 1️⃣ Philosophy — “Guide the AI, Don’t Expect It to Guess”

Copilot doesn’t think — it _predicts_.  
The clearer your intent, the better your code suggestions.

**Always tell Copilot:**

- 🧩 _What_ this code should do
- 🔢 _Inputs_ and _outputs_
- 🎯 _Constraints_ or _edge cases_

> 💬 Tip: A **good comment is a mini prompt.**  
> A one-line description like “# compute velocity between two snapshots” can save minutes of refactoring.

---

## 🧩 2️⃣ Project Context (So Copilot Understands Your Patterns)

This project is an **AI-driven analysis system** that:

1. Collects post data from a simulated network (trending + latest)
2. Cleans and normalizes the JSON
3. Computes growth, rubric, and strategy analysis
4. Predicts trending probability
5. Sends structured intelligence reports to Discord

Core technologies:

- **Python 3.11**
- **Flask**, **Celery**, **Redis**
- **Pandas**, **NumPy**, **Matplotlib**, **Seaborn**
- **Discord.py**
- **OpenAI / Anthropic / Gemini SDKs**

---

## 🧩 3️⃣ File & Task Patterns (Copilot Learns from These)

| Module                | Responsibility                       | Typical Function                      |
| --------------------- | ------------------------------------ | ------------------------------------- |
| `collector/`          | Fetch data from API/feed             | `def collect_batch()`                 |
| `cleaner/`            | Clean & normalize JSON               | `def clean_data()`                    |
| `growth_tracker.py`   | Compute engagement deltas & velocity | `def update_growth_from_clean()`      |
| `rubric_evaluator.py` | Apply rubric scoring                 | `def evaluate_rubric_from_features()` |
| `strategist/`         | Cluster tags & authors               | `def detect_clusters()`               |
| `predictor/`          | Estimate trending probability        | `def predict_trending()`              |
| `report_builder.py`   | Combine analysis results             | `def build_intelligence_report()`     |
| `discord_notifier.py` | Format & send embed message          | `def send_discord_embed()`            |

> 🧩 Keep consistent naming patterns.  
> Copilot uses previous functions as pattern examples.

---

## ✍️ 4️⃣ Comment Templates for Copilot Prompts

Before you start typing code, describe the _intent_.  
Copilot reads nearby comments first.

### 🔹 Function-level comment

```python
# Step: Compute growth velocity and acceleration for posts
# - Inputs: df_current (DataFrame), df_previous (DataFrame)
# - Outputs: DataFrame with delta_like, delta_reply, velocity_total_per_min
# - Edge cases: handle missing followers and timestamps
```
