# ✨ AuraHabit - Premium Glassmorphic Habit Tracker & AI Companion

AuraHabit is a state-of-the-art **Habit Tracker** application built with a **Python & Flask** backend and a beautiful **Glassmorphic & Ambient-lit** frontend dashboard. It features robust streak engines, gamified XP leveling, visual analytics (including a GitHub-style heatmap), and a direct integration with a **Google Gemma-3 AI Coach** to guide user habits.

---

## 🚀 Key Feature Pillars

### 1. 📅 Aura Flow Heatmap (GitHub Style)
*   **105-Day Completion Grid**: Visualizes your daily consistency over the last 15 weeks in a high-density contribution grid.
*   **Intensity-Colored Cells**: Automatically highlights success rate percentages:
    *   `cell-lvl-0`: 0% completed (empty)
    *   `cell-lvl-1`: 1% to 25% completed
    *   `cell-lvl-2`: 26% to 50% completed
    *   `cell-lvl-3`: 51% to 75% completed
    *   `cell-lvl-4`: 76% to 100% completed (full brand purple glow)

### 2. 🏆 Aura XP & Achievement Vault (Gamification)
*   **Progression Level System**: Earn experience points (XP) dynamically as you check in:
    *   `+20 XP` per check-in completion.
    *   `+10 XP` bonus per active streak day across habits.
    *   `+100 XP` bonus for unlocking an achievement badge.
*   **Quadratic Level Formula**: `Level = floor(sqrt(XP / 100)) + 1`.
*   **Achievement Badges**: Unlocks dynamic badges based on accomplishments:
    *   `First Step`: Complete any habit check-in.
    *   `Consistency Starter`: Reach a 3-day active streak on any habit.
    *   `Habit Master`: Reach a 7-day active streak on any habit.
    *   `Aura Legend`: Reach a 14-day active streak on any habit.
    *   `Category Explorer`: Complete habits in at least 3 different categories.
    *   `Super Dedicated`: Accumulate 20 total completions across habits.

### 3. 📊 Visual Analytics Suite (Chart.js)
*   **Category Distribution**: An interactive doughnut chart showing the distribution of your habits (Health, fitness, study, reading, work, personal, other).
*   **14-Day Completion Trend**: A line chart tracking your consistency percentage over the last two weeks, highlighting trends in routines.

### 🧠 4. Aura AI Coach (Google Gemma-3 Chat)
*   **Context-Aware Chat**: Talk to a private, motivational productivity coach in the new dashboard panel.
*   **NVIDIA API Integration**: Powered by `google/gemma-3n-e2b-it` model utilizing lightweight `requests` HTTP calls.
*   **Thought Process Toggles**: Exposes the model's step-by-step logical reasoning process inside a dropdown for full transparency.

---

## 🛠️ Technical Architecture

The codebase is modularized according to industry standard best practices:

*   **[`app.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/app.py)**: Configures the Flask application, registers blueprints, and handles global HTTP error states.
*   **[`routes/habit_routes.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/routes/habit_routes.py)**: Contains the RESTful JSON endpoints serving habits CRUD, analytics, leaderboard, export, gamification levels, and chatbot endpoints.
*   **[`services/habit_service.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/services/habit_service.py)**: Service layer for habits creation, deletion, validation, and analytics compiling.
*   **[`services/ai_service.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/services/ai_service.py)**: Connects to the NVIDIA API gateway for generating gemma-3 responses.
*   **[`storage.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/storage.py)**: Thread-safe in-memory data storage guarded by a `threading.Lock`.
*   **[`utils/date_utils.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/utils/date_utils.py)**: Math and datetime logic for tracking progressions and active/longest streaks.
*   **[`templates/base.html`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/templates/base.html)**: Layout template importing Chart.js and Lucide icons, including the global timezone Sandbox Time.
*   **[`templates/index.html`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/templates/index.html)**: Main dashboard with tab toggles, Level Card metrics, habit check-ins, heatmap grid, and chat UI.
*   **[`static/css/style.css`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/static/css/style.css)**: Glassmorphism design tokens, animations, scrollbars, and chat bubble custom rules.

---

## 📋 API Endpoints Matrix

| HTTP Verb | Path | Description |
| :--- | :--- | :--- |
| **POST** | `/api/habits` | Creates a new habit |
| **GET** | `/api/habits` | Retrieves all habits |
| **PUT** | `/api/habits/<id>` | Modifies details of a habit |
| **DELETE** | `/api/habits/<id>` | Deletes a habit |
| **POST** | `/api/habits/<id>/checkin` | Completes check-in for a given day |
| **GET** | `/api/analytics` | Compiles 14-day history, heatmap grids, and levels |
| **GET** | `/api/gamification` | Computes active levels, XP percentages, and unlocked badges |
| **POST** | `/api/coach/chat` | Sends message to Google Gemma-3 AI coach and retrieves reply |
| **GET** | `/api/leaderboard` | Ranks habits based on current active streaks |
| **GET** | `/api/habits/export` | Exports all habits and completions as a JSON file |

---

## ⚡ Getting Started

### 1. Install Requirements
Ensure you have **Python 3.x** and the required libraries installed:
```bash
pip install flask requests openai
```

### 2. Start the Application
Run the application by executing `app.py`:
```bash
python app.py
```
By default, the server will start at `http://127.0.0.1:5000/`.

### 3. Run the Automated Tests
The test suite consists of 20 automated assertions verifying date math, validation limits, streaks, gamification levels, and mocked AI endpoints:
```bash
python -m unittest test_app.py
```

### 4. Sandbox Time (Time Travel)
Use the **Sandbox Time** control in the top-right corner of the dashboard navigation bar to travel through time and test streak accumulations or resets instantly without waiting for the physical calendar date to change.
