# ✨ AuraHabit - Modern Glassmorphic Habit Tracker

AuraHabit is a premium, state-of-the-art **Habit Tracker** application built with a **Python & Flask** backend and a beautiful **Glassmorphic & Ambient-lit** frontend dashboard. It features robust streak calculation, history management, and thread-safe in-memory data storage.

---

## 🎯 Business Value & Epic Goals

Building consistent routines is the foundation of personal growth. AuraHabit:
- **Encourages Consistency & Accountability**: Through daily check-ins and visual cues.
- **Provides Measurable Progress**: With a precise daily streak engine.
- **Visualizes Routines**: Via overall dashboard progress and weekly consistency bar charts.

---

## 🚀 Technical Architecture

The codebase is modularized according to industry standard best practices:

- **[`app.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/app.py)**: Application entrypoint. Configures the Flask application, registers blueprints, and handles global HTTP error states.
- **[`routes/habit_routes.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/routes/habit_routes.py)**: Contains the RESTful JSON endpoints serving habits CRUD operations, daily check-ins, analytics, leaderboard, export utility, and reminders.
- **[`services/habit_service.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/services/habit_service.py)**: Core business service layer. Coordinates validation, streak recalculations, dashboard stats compilation, and leaderboard ranking.
- **[`storage.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/storage.py)**: Thread-safe memory storage implementing standard query and modification methods (`InMemoryStorage`) guarded by a `threading.Lock`.
- **[`utils/date_utils.py`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/utils/date_utils.py)**: Math and datetime logic for tracking calendar progressions, calculating current/longest streaks, and overall completion percentages.
- **[`templates/`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/templates)**: Frontend UI templates including `base.html` (layout, global toast notifications, sandbox time selection) and `index.html` (lucide-icons, category filters, sidebar metrics, modifiable habit list, and check-in buttons).

---

## 📋 User Stories & Code Mappings

Here is a traceability matrix mapping the user stories to the corresponding APIs, service functions, and files in the codebase:

### US-001: Create Habit
*As a user, I want to create a new habit so that I can start tracking it.*
- **API Endpoint**: `POST /api/habits` -> [`routes/habit_routes.py:create_habit`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/routes/habit_routes.py#L8-L28)
- **Service Implementation**: [`services/habit_service.py:create_habit`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/services/habit_service.py#L22-L52)
- **Data Storage**: Generates a standard UUID as the `id` and stores the habit in the thread-safe global `db` dictionary inside `storage.py`.

### US-002: View Habits
*As a user, I want to view all my habits so that I can manage them.*
- **API Endpoint**: `GET /api/habits` -> [`routes/habit_routes.py:get_habits`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/routes/habit_routes.py#L29-L39)
- **Service Implementation**: [`services/habit_service.py:get_all_habits`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/services/habit_service.py#L54-L63)
- **Frontend Interactivity**: Rendered dynamically within the dashboard container of `templates/index.html` (lines 235-331).

### US-003: Daily Check-In
*As a user, I want to mark a habit as completed for today so that I can maintain my streak.*
- **API Endpoint**: `POST /api/habits/<habit_id>/checkin` -> [`routes/habit_routes.py:check_in_habit`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/routes/habit_routes.py#L105-L136)
- **Service Implementation**: [`services/habit_service.py:check_in_habit`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/services/habit_service.py#L107-L137)
- **Validation**: Enforces date format (YYYY-MM-DD), ensures check-ins are not before creation date, and prevents duplicate completions on the same day.

### US-004: View Streak
*As a user, I want to see my current streak so that I can stay motivated.*
- **API Endpoint**: `GET /api/habits/<habit_id>/streak` -> [`routes/habit_routes.py:get_habit_streak`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/routes/habit_routes.py#L137-L159)
- **Algorithm**: Implemented in [`utils/date_utils.py:calculate_streaks`](file:///c:/Users/Sankari%20Sabarikanth/Downloads/sankari/utils/date_utils.py#L15-L92). Running consecutive days increases the active count. If yesterday or today are missed, the active streak resets to `0`, while the historical peak remains safely stored as the `longest_streak`.

### US-005: View Completion History
*As a user, I want to view past completions so that I can analyze my consistency.*
- **API Endpoint**: Stored within the `completions` array property of each habit, returned in GET endpoints: `GET /api/habits` and `GET /api/habits/<habit_id>`.
- **Advanced Dashboard Integration**: Served through:
  - `GET /api/dashboard`: Combines active streaks and completion statuses.
  - `GET /api/analytics`: Returns daily completion rates, a 7-day weekly comparison summary, and missed items.
  - `GET /api/leaderboard`: Ranks habits based on current active streaks.

---

## 🔒 Acceptance Criteria Fulfillment

| Criteria | Business Logic Enforcer | Test Assertion Coverage |
| :--- | :--- | :--- |
| **Habit name is required** | `services/habit_service.py` L24-25 | `test_app.py:test_create_habit_validation_failure` |
| **Habit ID is generated automatically** | `services/habit_service.py` L32 (uuid4) | `test_app.py:test_create_habit_success` |
| **User can check in once per day** | `services/habit_service.py` L125-126 | `test_app.py:test_check_in_success` |
| **Duplicate check-in returns error (400)** | `services/habit_service.py` L125-126 (ValueError) | `test_app.py:test_check_in_duplicate_prevention` |
| **Consecutive days increase streak** | `utils/date_utils.py` L50-62 | `test_app.py:test_streak_calculation_basic` |
| **Missing a day resets current streak** | `utils/date_utils.py` L64-75 | `test_app.py:test_streak_calculation_gaps` |
| **Completion history is stored and retrievable** | `storage.py` and `routes/habit_routes.py` | `test_app.py:test_get_habit_by_id` |

---

## 🛠️ Getting Started & Execution

### 1. Requirements
Ensure you have **Python 3.x** and **Flask** installed on your local machine:
```bash
pip install flask
```

### 2. Start the Server
Run the application by executing `app.py`:
```bash
python app.py
```
By default, the server will start at `http://127.0.0.1:5000/`.

### 3. Open the Dashboard
Open your favorite web browser and navigate to:
```text
http://127.0.0.1:5000/
```
You will be greeted with the beautifully responsive, premium glassmorphic dashboard! You can use the **Sandbox Time** control in the navigation bar to travel through time and test consecutive streak accumulations or resets without manually waiting for the calendar to change.

### 4. Run the Unit Test Suite
To execute all 17 automated tests verifying date math, validation, and analytics endpoints:
```bash
python -m unittest test_app.py
```
