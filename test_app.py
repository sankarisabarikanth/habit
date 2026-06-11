import unittest
import json
from datetime import datetime, timedelta
from app import app
from storage import db
from utils.date_utils import calculate_streaks, get_today_date_str, get_yesterday_date_str
import services.habit_service as service

class HabitTrackerTestCase(unittest.TestCase):
    def setUp(self):
        """
        Set up the Flask testing client and clear in-memory database.
        """
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        self.client = app.test_client()
        db.clear() # Reset in-memory database before each test

    def tearDown(self):
        """Clear database after each test."""
        db.clear()

    # --- 1. Date & Streak Utility Tests ---
    def test_streak_calculation_basic(self):
        """Verify streak calculation with standard consecutive days."""
        today = get_today_date_str()
        yesterday = get_yesterday_date_str()
        created_at = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Scenario: Checked in yesterday and today
        completions = [yesterday, today]
        metrics = calculate_streaks(completions, created_at, today)
        
        self.assertEqual(metrics["current_streak"], 2)
        self.assertEqual(metrics["longest_streak"], 2)
        self.assertEqual(metrics["total_completions"], 2)
        # 3 days elapsed: created_at, yesterday, today. Completed 2/3.
        self.assertEqual(metrics["completion_percentage"], 66.7)

    def test_streak_calculation_gaps(self):
        """Verify streak calculation with gaps resets current streak but keeps longest streak."""
        today = get_today_date_str()
        two_days_ago = (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        three_days_ago = (datetime.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        created_at = (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        # Scenario: Checked in 3 days ago, 2 days ago, missed yesterday, checked in today
        completions = [three_days_ago, two_days_ago, today]
        metrics = calculate_streaks(completions, created_at, today)
        
        # Yesterday was missed, but completed today, so current streak = 1 (today)
        self.assertEqual(metrics["current_streak"], 1)
        # Longest streak = 2 (three_days_ago + two_days_ago)
        self.assertEqual(metrics["longest_streak"], 2)
        self.assertEqual(metrics["total_completions"], 3)

    def test_streak_calculation_broken(self):
        """Verify streak is 0 if missed yesterday and today."""
        today = get_today_date_str()
        three_days_ago = (datetime.today() - timedelta(days=3)).strftime('%Y-%m-%d')
        created_at = (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        # Scenario: Checked in 3 days ago, missed yesterday and today
        completions = [three_days_ago]
        metrics = calculate_streaks(completions, created_at, today)
        
        self.assertEqual(metrics["current_streak"], 0)
        self.assertEqual(metrics["longest_streak"], 1)

    # --- 2. API Routes / Habits CRUD Tests ---
    def test_create_habit_success(self):
        """Ensure API can create a new habit with valid inputs."""
        payload = {
            "name": "Read a Book",
            "description": "Read 15 pages of philosophy",
            "category": "Reading"
        }
        response = self.client.post("/api/habits", 
                                    data=json.dumps(payload),
                                    content_type="application/json")
        
        self.assertEqual(response.status_code, 201)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["data"]["name"], "Read a Book")
        self.assertEqual(res_data["data"]["category"], "Reading")
        self.assertIn("id", res_data["data"])
        self.assertEqual(res_data["data"]["streak_current"], 0)

    def test_create_habit_validation_failure(self):
        """Ensure API rejects habit creation with empty or missing name."""
        payload = {
            "name": "   ",
            "category": "Study"
        }
        response = self.client.post("/api/habits", 
                                    data=json.dumps(payload),
                                    content_type="application/json")
        
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "error")
        self.assertIn("name is required", res_data["message"])

    def test_get_habits_empty(self):
        """Ensure list endpoint returns empty array when no habits are stored."""
        response = self.client.get("/api/habits")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["count"], 0)
        self.assertEqual(res_data["data"], [])

    def test_get_habit_by_id(self):
        """Verify retrieving details of a specific habit by ID."""
        h = service.create_habit("Exercise", category="Fitness")
        
        response = self.client.get(f"/api/habits/{h['id']}")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["data"]["name"], "Exercise")
        self.assertEqual(res_data["data"]["category"], "Fitness")

    def test_get_habit_not_found(self):
        """Ensure GET details returns 404 for invalid IDs."""
        response = self.client.get("/api/habits/invalid-uuid-string")
        self.assertEqual(response.status_code, 404)

    def test_update_habit_details(self):
        """Ensure API can update details of a habit successfully."""
        h = service.create_habit("Eat Veggies", category="Health")
        
        payload = {
            "name": "Eat Organic Veggies",
            "description": "5 servings per day",
            "category": "Health"
        }
        
        response = self.client.put(f"/api/habits/{h['id']}", 
                                   data=json.dumps(payload),
                                   content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["data"]["name"], "Eat Organic Veggies")
        self.assertEqual(res_data["data"]["description"], "5 servings per day")

    def test_delete_habit_success(self):
        """Verify deleting a habit removes it entirely from storage."""
        h = service.create_habit("Smoke Free", category="Health")
        
        response = self.client.delete(f"/api/habits/{h['id']}")
        self.assertEqual(response.status_code, 200)
        
        # Check details is now 404
        check_response = self.client.get(f"/api/habits/{h['id']}")
        self.assertEqual(check_response.status_code, 404)

    # --- 3. Check-In & Streak Calculation Tests ---
    def test_check_in_success(self):
        """Ensure marking a habit as completed today updates streak and percentage."""
        h = service.create_habit("Coding", category="Study")
        today = get_today_date_str()
        
        payload = {
            "date": today
        }
        response = self.client.post(f"/api/habits/{h['id']}/checkin", 
                                    data=json.dumps(payload),
                                    content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["data"]["streak_current"], 1)
        self.assertEqual(res_data["data"]["streak_longest"], 1)
        self.assertEqual(res_data["data"]["total_checkins"], 1)
        self.assertEqual(res_data["data"]["completion_percentage"], 100.0)

    def test_check_in_duplicate_prevention(self):
        """Verify that multiple check-ins for the same day are rejected with 400."""
        h = service.create_habit("Meditation", category="Health")
        today = get_today_date_str()
        
        # First check-in
        service.check_in_habit(h["id"], checkin_date=today)
        
        # Second duplicate check-in
        payload = {"date": today}
        response = self.client.post(f"/api/habits/{h['id']}/checkin", 
                                    data=json.dumps(payload),
                                    content_type="application/json")
        
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "error")
        self.assertIn("already completed", res_data["message"])

    def test_check_in_before_creation(self):
        """Verify checking in before habit creation date is rejected."""
        today = get_today_date_str()
        yesterday = get_yesterday_date_str()
        
        # Habit created today
        h = service.create_habit("Water Plants", category="Other", created_at=today)
        
        # Try checking in for yesterday
        payload = {"date": yesterday}
        response = self.client.post(f"/api/habits/{h['id']}/checkin", 
                                    data=json.dumps(payload),
                                    content_type="application/json")
        
        self.assertEqual(response.status_code, 400)
        res_data = json.loads(response.data)
        self.assertIn("before habit creation date", res_data["message"])

    # --- 4. Dashboard & Analytics API Tests ---
    def test_dashboard_data_structure(self):
        """Verify structure and calculations of the overall progress dashboard."""
        today = get_today_date_str()
        h1 = service.create_habit("Habit One", category="Study")
        h2 = service.create_habit("Habit Two", category="Fitness")
        
        # Complete h1 today
        service.check_in_habit(h1["id"], checkin_date=today)
        
        response = self.client.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "success")
        
        # Should have 2 items
        items = res_data["data"]
        self.assertEqual(len(items), 2)
        
        # Find h1 in dashboard details
        h1_dashboard = next(x for x in items if x["id"] == h1["id"])
        self.assertEqual(h1_dashboard["total_checkins"], 1)
        self.assertEqual(h1_dashboard["streak_current"], 1)
        self.assertTrue(h1_dashboard["completed_today"])
        
        # Find h2 in dashboard details
        h2_dashboard = next(x for x in items if x["id"] == h2["id"])
        self.assertEqual(h2_dashboard["total_checkins"], 0)
        self.assertEqual(h2_dashboard["streak_current"], 0)
        self.assertFalse(h2_dashboard["completed_today"])

    def test_analytics_metrics(self):
        """Verify advanced analytics calculates compliance rate, missed habits, and champion habit."""
        today = get_today_date_str()
        yesterday = get_yesterday_date_str()
        
        h1 = service.create_habit("Habit A", category="Fitness", created_at=yesterday)
        h2 = service.create_habit("Habit B", category="Study", created_at=yesterday)
        h3 = service.create_habit("Habit C", category="Reading", created_at=yesterday)
        
        # Check-in A for yesterday and today
        service.check_in_habit(h1["id"], checkin_date=yesterday)
        service.check_in_habit(h1["id"], checkin_date=today)
        
        # Check-in B for yesterday (but not today)
        service.check_in_habit(h2["id"], checkin_date=yesterday)
        
        # C has no check-ins
        
        response = self.client.get(f"/api/analytics?date={today}")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        
        analytics = res_data["data"]
        self.assertEqual(analytics["total_habits"], 3)
        # Completed today: h1 is completed today. h2 and h3 are not. Total = 1.
        self.assertEqual(analytics["completed_today"], 1)
        self.assertEqual(analytics["daily_completion_rate"], 33.3)
        
        # Missed today: h2 and h3 are missed today
        missed_names = [x["name"] for x in analytics["missed_today"]]
        self.assertEqual(len(missed_names), 2)
        self.assertIn("Habit B", missed_names)
        self.assertIn("Habit C", missed_names)
        
        # Most consistent champion: h1 has streak_longest=2, h2 has streak_longest=1. h1 is champion!
        self.assertEqual(analytics["most_consistent_habit"]["name"], "Habit A")
        self.assertEqual(analytics["most_consistent_habit"]["streak_longest"], 2)

    def test_streaks_leaderboard(self):
        """Ensure leaderboard ranks habits by active streaks correctly."""
        h1 = service.create_habit("Runner", category="Fitness", created_at=get_yesterday_date_str())
        h2 = service.create_habit("Scholar", category="Study")
        
        # h1 has streak 2
        service.check_in_habit(h1["id"], checkin_date=get_yesterday_date_str())
        service.check_in_habit(h1["id"], checkin_date=get_today_date_str())
        
        # h2 has streak 1
        service.check_in_habit(h2["id"], checkin_date=get_today_date_str())
        
        response = self.client.get("/api/leaderboard")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        
        leaderboard = res_data["data"]
        self.assertEqual(leaderboard[0]["name"], "Runner")
        self.assertEqual(leaderboard[0]["streak_current"], 2)
        self.assertEqual(leaderboard[1]["name"], "Scholar")
        self.assertEqual(leaderboard[1]["streak_current"], 1)

    def test_reminder_simulation_messages(self):
        """Ensure smart reminders provides motivating text alerts for outstanding habits."""
        h = service.create_habit("Floss Teeth", category="Health")
        
        response = self.client.get("/api/reminders/simulate")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        
        reminders = res_data["data"]
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]["name"], "Floss Teeth")
        self.assertIn("Kickstart your streak", reminders[0]["message"])

    def test_gamification_xp_and_badges(self):
        """Test that checking in increases XP and unlocks badges correctly."""
        # Check initial state (no habits, XP should be 0, badges locked)
        response = self.client.get("/api/gamification")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["data"]["xp"], 0)
        self.assertEqual(res_data["data"]["level"], 1)
        
        # Unlocked status of "first_step" should be False
        first_step_badge = next(b for b in res_data["data"]["badges"] if b["id"] == "first_step")
        self.assertFalse(first_step_badge["unlocked"])
        
        # Create a habit and check in
        h = service.create_habit("Read Books", category="Reading")
        service.check_in_habit(h["id"])
        
        # Re-check gamification
        response = self.client.get("/api/gamification")
        res_data = json.loads(response.data)
        gamification = res_data["data"]
        
        # Checkin = 20 XP. Streak (1) = 10 XP bonus. Badge unlock = 100 XP. Total = 130 XP
        self.assertEqual(gamification["xp"], 130)
        self.assertEqual(gamification["level"], 2) # sqrt(130/100) + 1 = 1 + 1 = 2
        
        first_step_badge = next(b for b in gamification["badges"] if b["id"] == "first_step")
        self.assertTrue(first_step_badge["unlocked"])
        
    def test_heatmap_density_and_length(self):
        """Test that analytics API returns heatmap calendar data with correct formatting and density."""
        # Create a habit
        h = service.create_habit("Workout", category="Fitness")
        
        response = self.client.get("/api/analytics")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        
        # Heatmap data must exist and have length of 105 days
        heatmap = res_data["data"]["heatmap_data"]
        self.assertEqual(len(heatmap), 105)
        
        # Initial intensity should be 0 for today
        today_str = service.get_today_date_str()
        today_cell = next(cell for cell in heatmap if cell["date"] == today_str)
        self.assertEqual(today_cell["intensity"], 0)
        
        # Check in for today
        service.check_in_habit(h["id"])
        
        # Re-fetch analytics
        response = self.client.get("/api/analytics")
        res_data = json.loads(response.data)
        heatmap = res_data["data"]["heatmap_data"]
        
        # Today's cell should now have intensity 4 (100% completion rate for active habits today)
        today_cell = next(cell for cell in heatmap if cell["date"] == today_str)
        self.assertEqual(today_cell["intensity"], 4)

    def test_ai_coach_chat_route(self):
        """Test that the AI Coach chat endpoint executes queries and handles mock responses."""
        from unittest.mock import patch, MagicMock
        
        with patch("services.ai_service.requests.post") as mock_post:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Keep pushing forward! Consistency builds mountains.",
                            "reasoning_content": "The user is seeking routine advice. Formulating a concise answer."
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Call API
            response = self.client.post("/api/coach/chat", json={
                "message": "How do I build habits?",
                "history": []
            })
            self.assertEqual(response.status_code, 200)
            res_data = json.loads(response.data)
            
            self.assertEqual(res_data["status"], "success")
            self.assertEqual(res_data["content"], "Keep pushing forward! Consistency builds mountains.")
            self.assertEqual(res_data["reasoning"], "The user is seeking routine advice. Formulating a concise answer.")
            
        # Test error handling when missing message
        response = self.client.post("/api/coach/chat", json={})
        self.assertEqual(response.status_code, 400)

    # --- 5. Journal Feature Tests ---
    def test_create_journal_success(self):
        """Verify that a daily journal entry can be successfully created."""
        # Setup: Create a habit first to link
        h = service.create_habit("Daily Running", category="Fitness")
        
        payload = {
            "date": "2026-06-09",
            "title": "Feeling energetic",
            "content": "Went for a 5k run in the morning.",
            "mood": "Excellent",
            "habit_ids": [h["id"]]
        }
        
        response = self.client.post("/api/journals",
                                    data=json.dumps(payload),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 201)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["data"]["title"], "Feeling energetic")
        self.assertEqual(res_data["data"]["mood"], "Excellent")
        self.assertEqual(res_data["data"]["habit_ids"], [h["id"]])

    def test_create_journal_duplicate_prevention(self):
        """Ensure only one journal entry can exist per date."""
        payload = {
            "date": "2026-06-09",
            "title": "Reflection 1",
            "content": "First entry.",
            "mood": "Good"
        }
        # First entry
        response1 = self.client.post("/api/journals",
                                     data=json.dumps(payload),
                                     content_type="application/json")
        self.assertEqual(response1.status_code, 201)
        
        # Second entry on the same date
        payload2 = {
            "date": "2026-06-09",
            "title": "Reflection 2",
            "content": "Second entry attempt.",
            "mood": "Neutral"
        }
        response2 = self.client.post("/api/journals",
                                     data=json.dumps(payload2),
                                     content_type="application/json")
        self.assertEqual(response2.status_code, 400)
        res_data = json.loads(response2.data)
        self.assertEqual(res_data["status"], "error")
        self.assertIn("already exists", res_data["message"])

    def test_list_journals_and_date_filtering(self):
        """Verify journal listing and querying entries by specific date."""
        # Setup: create two journals on separate days
        payload1 = {
            "date": "2026-06-08",
            "title": "Day 1",
            "content": "Did some reading.",
            "mood": "Good"
        }
        payload2 = {
            "date": "2026-06-09",
            "title": "Day 2",
            "content": "Did some exercise.",
            "mood": "Excellent"
        }
        self.client.post("/api/journals", data=json.dumps(payload1), content_type="application/json")
        self.client.post("/api/journals", data=json.dumps(payload2), content_type="application/json")
        
        # Get all
        response = self.client.get("/api/journals")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["count"], 2)
        # Should be sorted date descending
        self.assertEqual(res_data["data"][0]["date"], "2026-06-09")
        self.assertEqual(res_data["data"][1]["date"], "2026-06-08")
        
        # Filter by date
        filter_response = self.client.get("/api/journals?date=2026-06-08")
        self.assertEqual(filter_response.status_code, 200)
        filter_data = json.loads(filter_response.data)
        self.assertEqual(filter_data["count"], 1)
        self.assertEqual(filter_data["data"][0]["title"], "Day 1")

    def test_update_journal_details(self):
        """Ensure existing journal entry details can be updated."""
        import services.journal_service as journal_service
        # Setup: create journal entry
        j = journal_service.create_journal(
            date="2026-06-09",
            title="Old Title",
            content="Old content",
            mood="Neutral"
        )
        
        payload = {
            "title": "New Title",
            "content": "New content",
            "mood": "Good"
        }
        response = self.client.put(f"/api/journals/{j['id']}",
                                   data=json.dumps(payload),
                                   content_type="application/json")
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["data"]["title"], "New Title")
        self.assertEqual(res_data["data"]["content"], "New content")
        self.assertEqual(res_data["data"]["mood"], "Good")

    def test_delete_journal_entry(self):
        """Ensure deleting a journal removes it from storage."""
        import services.journal_service as journal_service
        j = journal_service.create_journal(
            date="2026-06-09",
            title="To Delete",
            content="Reflections to be removed.",
            mood="Tired"
        )
        
        response = self.client.delete(f"/api/journals/{j['id']}")
        self.assertEqual(response.status_code, 200)
        
        # Check details is now 404
        check_response = self.client.get(f"/api/journals/{j['id']}")
        self.assertEqual(check_response.status_code, 404)

if __name__ == "__main__":
    unittest.main()
