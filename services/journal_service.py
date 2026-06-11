import uuid
from storage import db
from utils.date_utils import parse_date, get_today_date_str

def create_journal(date, title="", content="", mood="Neutral", habit_ids=None):
    """
    Creates a daily journal entry.
    Restricts to one journal entry per date.
    """
    if not date:
        date = get_today_date_str()
    else:
        date = date[:10]
        
    try:
        parse_date(date)
    except Exception:
        raise ValueError("Invalid date format. Must be YYYY-MM-DD.")
        
    # Check if a journal already exists for this date
    existing_journals = db.get_all_journals()
    for j in existing_journals:
        if j["date"] == date:
            raise ValueError(f"A journal entry already exists for {date}.")
            
    # Check linked habits exist
    valid_habit_ids = []
    if habit_ids:
        for hid in habit_ids:
            if db.get_by_id(hid) is not None:
                valid_habit_ids.append(hid)
                
    journal_id = str(uuid.uuid4())
    journal = {
        "id": journal_id,
        "date": date,
        "title": title.strip() if title else "",
        "content": content.strip() if content else "",
        "mood": mood.strip() if mood else "Neutral",
        "habit_ids": valid_habit_ids,
        "created_at": get_today_date_str()
    }
    return db.save_journal(journal)

def get_all_journals(today_str=None):
    """
    Retrieves all journal entries sorted by date descending.
    """
    journals = db.get_all_journals()
    # Sort by date descending
    return sorted(journals, key=lambda x: x["date"], reverse=True)

def get_journal_by_id(journal_id):
    """
    Retrieves a journal entry by ID.
    """
    return db.get_journal_by_id(journal_id)

def update_journal(journal_id, date=None, title=None, content=None, mood=None, habit_ids=None):
    """
    Updates details of an existing journal entry.
    """
    journal = db.get_journal_by_id(journal_id)
    if not journal:
        return None
        
    if date is not None:
        date = date[:10]
        try:
            parse_date(date)
        except Exception:
            raise ValueError("Invalid date format. Must be YYYY-MM-DD.")
        # Check if changing the date conflicts with another entry
        if date != journal["date"]:
            existing_journals = db.get_all_journals()
            for j in existing_journals:
                if j["date"] == date:
                    raise ValueError(f"A journal entry already exists for {date}.")
            journal["date"] = date
            
    if title is not None:
        journal["title"] = title.strip()
        
    if content is not None:
        journal["content"] = content.strip()
        
    if mood is not None:
        journal["mood"] = mood.strip() if mood.strip() else "Neutral"
        
    if habit_ids is not None:
        valid_habit_ids = []
        for hid in habit_ids:
            if db.get_by_id(hid) is not None:
                valid_habit_ids.append(hid)
        journal["habit_ids"] = valid_habit_ids
        
    return db.save_journal(journal)

def delete_journal(journal_id):
    """
    Deletes a journal entry.
    """
    return db.delete_journal(journal_id)
