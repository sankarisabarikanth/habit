from datetime import datetime, timedelta

def get_today_date_str():
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.today().strftime('%Y-%m-%d')

def get_yesterday_date_str():
    """Returns yesterday's date in YYYY-MM-DD format."""
    return (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

def parse_date(date_str):
    """Parses YYYY-MM-DD string into a datetime.date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def calculate_streaks(completions, created_at_str, today_str=None):
    """
    Calculates current streak, longest streak, total completions, and completion percentage.
    
    :param completions: List of YYYY-MM-DD date strings when the habit was completed.
    :param created_at_str: ISO string or YYYY-MM-DD string representing when the habit was created.
    :param today_str: Optional YYYY-MM-DD string for 'today'. Defaults to system local today.
    :return: Dict containing streak and completion metrics.
    """
    if not today_str:
        today_str = get_today_date_str()

    today_date = parse_date(today_str)
    
    try:
        created_date = parse_date(created_at_str[:10])
    except Exception:
        created_date = today_date

    # Clean and sort unique valid completion dates
    valid_dates = set()
    for c in completions:
        try:
            valid_dates.add(parse_date(c[:10]))
        except Exception:
            continue
            
    sorted_dates = sorted(list(valid_dates))
    total_completions = len(sorted_dates)

    # 1. Calculate Longest Streak
    longest_streak = 0
    current_temp = 0
    prev_date = None
    
    for d in sorted_dates:
        if prev_date is None:
            current_temp = 1
        elif (d - prev_date).days == 1:
            current_temp += 1
        elif (d - prev_date).days > 1:
            if current_temp > longest_streak:
                longest_streak = current_temp
            current_temp = 1
        prev_date = d
        
    if current_temp > longest_streak:
        longest_streak = current_temp

    # 2. Calculate Current Streak (running backward from today or yesterday)
    yesterday_date = today_date - timedelta(days=1)
    
    has_today = today_date in valid_dates
    has_yesterday = yesterday_date in valid_dates
    
    current_streak = 0
    if has_today or has_yesterday:
        scan_date = today_date if has_today else yesterday_date
        while scan_date in valid_dates:
            current_streak += 1
            scan_date -= timedelta(days=1)

    # 3. Calculate Completion Percentage
    # Days elapsed since creation including today. If created today, days = 1.
    days_elapsed = (today_date - created_date).days + 1
    if days_elapsed < 1:
        days_elapsed = 1
        
    completion_percentage = round((total_completions / days_elapsed) * 100, 1)
    # Ensure range bounds
    completion_percentage = min(100.0, max(0.0, completion_percentage))

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_completions": total_completions,
        "completion_percentage": completion_percentage
    }
