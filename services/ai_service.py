import requests

def _build_context_system_prompt(today_str=None):
    import services.habit_service as habit_service
    import services.journal_service as journal_service
    from utils.date_utils import get_today_date_str
    
    if not today_str:
        today_str = get_today_date_str()
    else:
        today_str = today_str[:10]
    
    # 1. Fetch user gamification and habit data
    try:
        gamification = habit_service.get_gamification_data(today_str)
        habits = habit_service.get_all_habits(today_str)
    except Exception:
        gamification = None
        habits = []
        
    # 2. Fetch journal entries
    try:
        journals = journal_service.get_all_journals()
    except Exception:
        journals = []
        
    # 3. Build stats summary
    stats_summary = ""
    if gamification:
        stats_summary += f"User Level: {gamification.get('level', 1)}, Total XP: {gamification.get('xp', 0)}. "
        stats_summary += f"Unlocked Badges: {gamification.get('unlocked_badges_count', 0)} of {len(gamification.get('badges', []))}. "
        
    if habits:
        stats_summary += f"Currently tracking {len(habits)} habits. "
        completed_today = [h['name'] for h in habits if today_str in h.get('completions', [])]
        pending_today = [h['name'] for h in habits if today_str not in h.get('completions', [])]
        if completed_today:
            stats_summary += f"Completed today: {', '.join(completed_today)}. "
        if pending_today:
            stats_summary += f"Pending check-in today: {', '.join(pending_today)}. "
            
    # 4. Build recent journals summary (up to 3 entries)
    journal_summary = ""
    recent_journals = journals[:3]
    if recent_journals:
        journal_summary += "\nRecent user journal reflections:\n"
        for j in recent_journals:
            mood_indicator = f"Mood: {j.get('mood', 'Neutral')}"
            linked_routines = ""
            if j.get("habit_ids") and habits:
                linked_names = []
                for hid in j["habit_ids"]:
                    habit = next((h for h in habits if h["id"] == hid), None)
                    if habit:
                        linked_names.append(habit["name"])
                if linked_names:
                    linked_routines = f" (Reflecting on: {', '.join(linked_names)})"
            
            journal_summary += f"- [{j['date']}] Title: '{j.get('title', 'Untitled')}' | {mood_indicator}{linked_routines} | Reflection: \"{j.get('content', '')}\"\n"
            
    system_prompt = (
        "You are Aura Coach, a premium productivity and habit advisor. "
        "Provide brief, motivational, and extremely practical advice on "
        "habit formation, consistency, discipline, and routines. "
        "Keep your output readable, encouraging, and clear. "
        "Address the user as a fellow builder of routines."
    )
    
    if stats_summary or journal_summary:
        system_prompt += "\nUse the following real-time context about the user's progress and state to customize your coaching. Reference their achievements, streaks, current mood, or journal logs naturally if relevant, but do not sound overly robotic or read back their data word-for-word:\n"
        system_prompt += stats_summary
        system_prompt += journal_summary
        
    return system_prompt

def get_ai_coach_response(user_message, chat_history=None, today_str=None):
    """
    Generates a response from the google/gemma-3n-e2b-it model acting as Aura Coach.
    """
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "application/json"
    }
    
    system_prompt = _build_context_system_prompt(today_str=today_str)
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append history if present
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    messages.append({"role": "user", "content": user_message})
    
    payload = {
        "model": "google/gemma-3n-e2b-it",
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.20,
        "top_p": 0.70,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": False
    }
    
    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        response.raise_for_status()
        
        res_json = response.json()
        choice = res_json["choices"][0]["message"]
        content = choice.get("content", "")
        reasoning = choice.get("reasoning_content", None)
        
        return {
            "status": "success",
            "content": content,
            "reasoning": reasoning
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
