import uuid
from datetime import datetime, timedelta
from storage import db
from utils.date_utils import calculate_streaks, get_today_date_str, parse_date

def _sync_habit_streaks(habit, today_str=None):
    """Recalculates and updates streaks for a habit based on current date."""
    if not today_str:
        today_str = get_today_date_str()
        
    streak_info = calculate_streaks(
        completions=habit.get("completions", []),
        created_at_str=habit["created_at"],
        today_str=today_str
    )
    
    habit["streak_current"] = streak_info["current_streak"]
    habit["streak_longest"] = streak_info["longest_streak"]
    habit["completion_percentage"] = streak_info["completion_percentage"]
    return db.save(habit)

def create_habit(name, description="", category="Other", created_at=None):
    """Creates a new habit in the data store."""
    if not name or not name.strip():
        raise ValueError("Habit name is required.")
        
    valid_categories = ["Health", "Study", "Fitness", "Reading", "Work", "Personal", "Other"]
    clean_category = category.strip() if category else "Other"
    if clean_category not in valid_categories:
        clean_category = "Other"
        
    habit_id = str(uuid.uuid4())
    
    # Allow custom created_at for testing purposes
    if not created_at:
        created_at = get_today_date_str()
    else:
        created_at = created_at[:10]
        
    habit = {
        "id": habit_id,
        "name": name.strip(),
        "description": description.strip() if description else "",
        "category": clean_category,
        "created_at": created_at,
        "completions": [],
        "streak_current": 0,
        "streak_longest": 0,
        "completion_percentage": 0.0
    }
    
    return db.save(habit)

def get_all_habits(today_str=None):
    """Retrieves all habits and syncs their streaks."""
    if not today_str:
        today_str = get_today_date_str()
        
    habits = db.get_all()
    synced_habits = []
    for h in habits:
        synced_habits.append(_sync_habit_streaks(h, today_str))
    return synced_habits

def get_habit_by_id(habit_id, today_str=None):
    """Retrieves a single habit by ID and syncs its streaks."""
    if not today_str:
        today_str = get_today_date_str()
        
    habit = db.get_by_id(habit_id)
    if not habit:
        return None
    return _sync_habit_streaks(habit, today_str)

def update_habit(habit_id, name=None, description=None, category=None, today_str=None):
    """Updates habit details (name, description, category)."""
    if not today_str:
        today_str = get_today_date_str()
        
    habit = db.get_by_id(habit_id)
    if not habit:
        return None
        
    if name is not None:
        if not name.strip():
            raise ValueError("Habit name cannot be empty.")
        habit["name"] = name.strip()
        
    if description is not None:
        habit["description"] = description.strip()
        
    if category is not None:
        valid_categories = ["Health", "Study", "Fitness", "Reading", "Work", "Personal", "Other"]
        clean_category = category.strip()
        if clean_category in valid_categories:
            habit["category"] = clean_category
        else:
            habit["category"] = "Other"
            
    # Sync and save
    return _sync_habit_streaks(habit, today_str)

def delete_habit(habit_id):
    """Deletes a habit from the store."""
    return db.delete(habit_id)

def check_in_habit(habit_id, checkin_date=None):
    """Marks a habit as completed for a specific day (defaults to today)."""
    if not checkin_date:
        checkin_date = get_today_date_str()
    else:
        checkin_date = checkin_date[:10]
        
    # Basic format check
    try:
        parse_date(checkin_date)
    except Exception:
        raise ValueError("Invalid check-in date format. Must be YYYY-MM-DD.")
        
    habit = db.get_by_id(habit_id)
    if not habit:
        return None
        
    # Prevent duplicate check-ins for the same day
    if checkin_date in habit["completions"]:
        raise ValueError(f"Habit '{habit['name']}' was already completed on {checkin_date}.")
        
    # Prevent checking in before the habit's creation date
    if checkin_date < habit["created_at"]:
        raise ValueError(f"Cannot check in on {checkin_date} before habit creation date {habit['created_at']}.")
        
    habit["completions"].append(checkin_date)
    habit["completions"].sort()
    
    # Recalculate streaks using the checked in date as 'today' to keep streaks in sync
    return _sync_habit_streaks(habit, checkin_date)

def get_dashboard_data(today_str=None):
    """Prepares structured progress dashboard data."""
    if not today_str:
        today_str = get_today_date_str()
        
    habits = get_all_habits(today_str)
    dashboard_items = []
    
    for h in habits:
        completions = h.get("completions", [])
        dashboard_items.append({
            "id": h["id"],
            "name": h["name"],
            "description": h["description"],
            "category": h["category"],
            "created_at": h["created_at"],
            "streak_current": h["streak_current"],
            "streak_longest": h["streak_longest"],
            "completion_percentage": h["completion_percentage"],
            "total_checkins": len(completions),
            "completed_today": today_str in completions
        })
        
    return dashboard_items

def get_analytics_data(today_str=None):
    """Calculates comprehensive habit tracking statistics."""
    if not today_str:
        today_str = get_today_date_str()
        
    habits = get_all_habits(today_str)
    total_habits = len(habits)
    
    # 1. Daily completions stats
    completed_today_count = sum(1 for h in habits if today_str in h.get("completions", []))
    daily_completion_rate = round((completed_today_count / total_habits) * 100, 1) if total_habits > 0 else 0.0
    
    # 2. Weekly progress summary (last 7 days)
    today_date = parse_date(today_str)
    weekly_summary = []
    
    # Scan backward for 7 days
    for i in range(6, -1, -1):
        target_date = today_date - timedelta(days=i)
        target_str = target_date.strftime('%Y-%m-%d')
        day_name = target_date.strftime('%a') # Mon, Tue, etc.
        
        # Count habits active on or before target_date
        active_habits_count = sum(1 for h in habits if h["created_at"] <= target_str)
        completed_on_day = sum(1 for h in habits if target_str in h.get("completions", []))
        
        completion_pct = round((completed_on_day / active_habits_count) * 100, 1) if active_habits_count > 0 else 0.0
        
        weekly_summary.append({
            "date": target_str,
            "day_name": day_name,
            "completed_count": completed_on_day,
            "total_count": active_habits_count,
            "percentage": completion_pct
        })
        
    # 3. Missed habits today
    missed_today = []
    for h in habits:
        if today_str not in h.get("completions", []):
            missed_today.append({
                "id": h["id"],
                "name": h["name"],
                "category": h["category"],
                "streak_current": h["streak_current"]
            })
            
    # 4. Most consistent habit (highest longest_streak, then total check-ins)
    most_consistent = None
    if habits:
        # Sort habits by streak_longest descending, then len(completions) descending
        sorted_by_consistency = sorted(
            habits, 
            key=lambda x: (x["streak_longest"], len(x.get("completions", []))), 
            reverse=True
        )
        best = sorted_by_consistency[0]
        most_consistent = {
            "id": best["id"],
            "name": best["name"],
            "category": best["category"],
            "streak_longest": best["streak_longest"],
            "total_checkins": len(best.get("completions", []))
        }

    # 5. Heatmap calendar progress (last 105 days = 15 weeks)
    heatmap_data = []
    for i in range(104, -1, -1):
        target_date = today_date - timedelta(days=i)
        target_str = target_date.strftime('%Y-%m-%d')
        day_name = target_date.strftime('%a')
        day_of_week = int(target_date.strftime('%w')) # 0 = Sunday, ..., 6 = Saturday
        
        active_habits_count = sum(1 for h in habits if h["created_at"] <= target_str)
        completed_on_day = sum(1 for h in habits if target_str in h.get("completions", []))
        
        completion_pct = round((completed_on_day / active_habits_count) * 100, 1) if active_habits_count > 0 else 0.0
        
        # Calculate intensity: 0 to 4
        intensity = 0
        if completed_on_day > 0:
            if completion_pct <= 25.0:
                intensity = 1
            elif completion_pct <= 50.0:
                intensity = 2
            elif completion_pct <= 75.0:
                intensity = 3
            else:
                intensity = 4
                
        heatmap_data.append({
            "date": target_str,
            "day_name": day_name,
            "day_of_week": day_of_week,
            "completed_count": completed_on_day,
            "total_count": active_habits_count,
            "percentage": completion_pct,
            "intensity": intensity
        })

    return {
        "today": today_str,
        "total_habits": total_habits,
        "completed_today": completed_today_count,
        "daily_completion_rate": daily_completion_rate,
        "weekly_summary": weekly_summary,
        "missed_today": missed_today,
        "most_consistent_habit": most_consistent,
        "heatmap_data": heatmap_data,
        "gamification": get_gamification_data(today_str)
    }

def get_gamification_data(today_str=None):
    """Calculates user level, XP, progress, and achievement badges status."""
    import math
    if not today_str:
        today_str = get_today_date_str()
        
    habits = get_all_habits(today_str)
    
    # 1. Calculate completions and streaks
    total_checkins = 0
    max_streak = 0
    categories_used = set()
    
    for h in habits:
        total_checkins += len(h.get("completions", []))
        if h["streak_longest"] > max_streak:
            max_streak = h["streak_longest"]
        if len(h.get("completions", [])) > 0:
            categories_used.add(h["category"])
            
    # 2. XP Calculations
    # - 20 XP per completion
    # - 10 XP bonus per day of longest streak
    xp = (total_checkins * 20) + (max_streak * 10)
    
    # Badges definition
    badges_def = [
        {
            "id": "first_step",
            "name": "First Step",
            "description": "Check in to any habit for the first time",
            "icon": "zap",
            "unlocked": total_checkins >= 1
        },
        {
            "id": "consistency_starter",
            "name": "Consistency Starter",
            "description": "Achieve a 3-day active streak on any habit",
            "icon": "flame",
            "unlocked": any(h["streak_current"] >= 3 for h in habits)
        },
        {
            "id": "habit_master",
            "name": "Habit Master",
            "description": "Achieve a 7-day active streak on any habit",
            "icon": "award",
            "unlocked": any(h["streak_current"] >= 7 for h in habits)
        },
        {
            "id": "aura_legend",
            "name": "Aura Legend",
            "description": "Achieve a 14-day active streak on any habit",
            "icon": "crown",
            "unlocked": any(h["streak_current"] >= 14 for h in habits)
        },
        {
            "id": "explorer",
            "name": "Category Explorer",
            "description": "Complete habits in at least 3 different categories",
            "icon": "compass",
            "unlocked": len(categories_used) >= 3
        },
        {
            "id": "super_dedicated",
            "name": "Super Dedicated",
            "description": "Accumulate 20 total completions across all habits",
            "icon": "sparkles",
            "unlocked": total_checkins >= 20
        }
    ]
    
    # Add 100 XP bonus for each unlocked badge
    unlocked_badges_count = sum(1 for b in badges_def if b["unlocked"])
    xp += unlocked_badges_count * 100
    
    # 3. Level Progression Curve
    # Level 1: 0 - 99 XP
    # Level 2: 100 - 399 XP
    # Level 3: 400 - 899 XP...
    # Formula: level = math.floor(math.sqrt(xp / 100)) + 1
    level = math.floor(math.sqrt(xp / 100)) + 1 if xp > 0 else 1
    
    current_level_base_xp = ((level - 1) ** 2) * 100
    next_level_base_xp = (level ** 2) * 100
    
    xp_in_level = xp - current_level_base_xp
    xp_for_next_level = next_level_base_xp - current_level_base_xp
    
    progress_pct = round((xp_in_level / xp_for_next_level) * 100, 1) if xp_for_next_level > 0 else 100.0
    progress_pct = min(100.0, max(0.0, progress_pct))
    
    return {
        "xp": xp,
        "level": level,
        "xp_in_level": xp_in_level,
        "xp_for_next_level": xp_for_next_level,
        "progress_percentage": progress_pct,
        "badges": badges_def,
        "unlocked_badges_count": unlocked_badges_count
    }

def get_leaderboard(today_str=None):
    """Ranks habits based on active and historical streaks."""
    if not today_str:
        today_str = get_today_date_str()
        
    habits = get_all_habits(today_str)
    # Rank by streak_current, then streak_longest, then total completions
    ranked_habits = sorted(
        habits, 
        key=lambda x: (x["streak_current"], x["streak_longest"], len(x.get("completions", []))), 
        reverse=True
    )
    
    leaderboard = []
    for idx, h in enumerate(ranked_habits, 1):
        leaderboard.append({
            "rank": idx,
            "id": h["id"],
            "name": h["name"],
            "category": h["category"],
            "streak_current": h["streak_current"],
            "streak_longest": h["streak_longest"],
            "total_checkins": len(h.get("completions", []))
        })
        
    return leaderboard

def get_reminders(today_str=None):
    """Finds missed habits today and generates encouragement reminders."""
    if not today_str:
        today_str = get_today_date_str()
        
    analytics = get_analytics_data(today_str)
    missed = analytics["missed_today"]
    
    reminders = []
    for m in missed:
        streak = m["streak_current"]
        if streak > 0:
            message = f"🔥 Don't let your {streak}-day streak slip! Tap check-in for '{m['name']}' now!"
        else:
            message = f"🌱 Kickstart your streak for '{m['name']}' today! Small steps make big changes."
            
        reminders.append({
            "id": m["id"],
            "name": m["name"],
            "category": m["category"],
            "streak_current": streak,
            "message": message
        })
        
    return reminders
