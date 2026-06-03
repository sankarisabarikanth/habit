import io
import json
from flask import Blueprint, request, jsonify, send_file
import services.habit_service as service

habit_api = Blueprint("habit_api", __name__)

@habit_api.route("/habits", methods=["POST"])
def create_habit():
    """Create a new habit."""
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description", "")
    category = data.get("category", "Other")
    
    try:
        new_habit = service.create_habit(name=name, description=description, category=category)
        return jsonify({
            "status": "success",
            "message": "Habit created successfully",
            "data": new_habit
        }), 201
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@habit_api.route("/habits", methods=["GET"])
def get_habits():
    """List all habits."""
    today_str = request.args.get("date")  # Allow passing custom date for sandbox testing
    habits = service.get_all_habits(today_str=today_str)
    return jsonify({
        "status": "success",
        "count": len(habits),
        "data": habits
    }), 200

@habit_api.route("/habits/<habit_id>", methods=["GET"])
def get_habit(habit_id):
    """Get a specific habit by ID."""
    today_str = request.args.get("date")
    habit = service.get_habit_by_id(habit_id, today_str=today_str)
    if not habit:
        return jsonify({
            "status": "error",
            "message": f"Habit with ID {habit_id} not found"
        }), 404
        
    return jsonify({
        "status": "success",
        "data": habit
    }), 200

@habit_api.route("/habits/<habit_id>", methods=["PUT"])
def update_habit(habit_id):
    """Update details of a specific habit."""
    data = request.get_json() or {}
    name = data.get("name")
    description = data.get("description")
    category = data.get("category")
    today_str = request.args.get("date")
    
    try:
        updated = service.update_habit(
            habit_id=habit_id,
            name=name,
            description=description,
            category=category,
            today_str=today_str
        )
        if not updated:
            return jsonify({
                "status": "error",
                "message": f"Habit with ID {habit_id} not found"
            }), 404
            
        return jsonify({
            "status": "success",
            "message": "Habit updated successfully",
            "data": updated
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@habit_api.route("/habits/<habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    """Delete a specific habit."""
    success = service.delete_habit(habit_id)
    if not success:
        return jsonify({
            "status": "error",
            "message": f"Habit with ID {habit_id} not found"
        }), 404
        
    return jsonify({
        "status": "success",
        "message": f"Habit with ID {habit_id} was successfully deleted"
    }), 200

@habit_api.route("/habits/<habit_id>/checkin", methods=["POST"])
def check_in_habit(habit_id):
    """Mark a habit as completed for a given day."""
    data = request.get_json() or {}
    checkin_date = data.get("date") # Optional, defaults to today
    
    try:
        updated = service.check_in_habit(habit_id, checkin_date=checkin_date)
        if not updated:
            return jsonify({
                "status": "error",
                "message": f"Habit with ID {habit_id} not found"
            }), 404
            
        return jsonify({
            "status": "success",
            "message": f"Check-in successful for habit '{updated['name']}'!",
            "data": {
                "id": updated["id"],
                "name": updated["name"],
                "streak_current": updated["streak_current"],
                "streak_longest": updated["streak_longest"],
                "total_checkins": len(updated["completions"]),
                "completion_percentage": updated["completion_percentage"]
            }
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@habit_api.route("/habits/<habit_id>/streak", methods=["GET"])
def get_habit_streak(habit_id):
    """Get streak information for a habit."""
    today_str = request.args.get("date")
    habit = service.get_habit_by_id(habit_id, today_str=today_str)
    if not habit:
        return jsonify({
            "status": "error",
            "message": f"Habit with ID {habit_id} not found"
        }), 404
        
    return jsonify({
        "status": "success",
        "data": {
            "id": habit["id"],
            "name": habit["name"],
            "streak_current": habit["streak_current"],
            "streak_longest": habit["streak_longest"],
            "total_checkins": len(habit["completions"]),
            "completions": habit["completions"]
        }
    }), 200

@habit_api.route("/dashboard", methods=["GET"])
def get_dashboard():
    """Get overall habits dashboard dataset."""
    today_str = request.args.get("date")
    data = service.get_dashboard_data(today_str=today_str)
    return jsonify({
        "status": "success",
        "data": data
    }), 200

@habit_api.route("/analytics", methods=["GET"])
def get_analytics():
    """Get habit tracker analytics."""
    today_str = request.args.get("date")
    data = service.get_analytics_data(today_str=today_str)
    return jsonify({
        "status": "success",
        "data": data
    }), 200

@habit_api.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """Get streaks leaderboard."""
    today_str = request.args.get("date")
    data = service.get_leaderboard(today_str=today_str)
    return jsonify({
        "status": "success",
        "data": data
    }), 200

@habit_api.route("/reminders/simulate", methods=["GET"])
def get_reminders_simulation():
    """Simulate daily reminders for outstanding habits."""
    today_str = request.args.get("date")
    data = service.get_reminders(today_str=today_str)
    return jsonify({
        "status": "success",
        "data": data
    }), 200

@habit_api.route("/habits/export", methods=["GET"])
def export_habits():
    """Export all habits data in memory as a JSON file attachment."""
    today_str = request.args.get("date")
    habits = service.get_all_habits(today_str=today_str)
    
    # Structure data nicely
    export_data = {
        "exported_at": today_str or service.get_today_date_str(),
        "total_habits": len(habits),
        "habits": habits
    }
    
    # Convert dict to string bytes
    json_bytes = json.dumps(export_data, indent=4).encode("utf-8")
    mem_file = io.BytesIO(json_bytes)
    mem_file.seek(0)
    
    return send_file(
        mem_file,
        mimetype="application/json",
        as_attachment=True,
        download_name="habits_export.json"
    )

@habit_api.route("/gamification", methods=["GET"])
def get_gamification():
    """Get user's XP, level, and badge milestones."""
    today_str = request.args.get("date")
    data = service.get_gamification_data(today_str=today_str)
    return jsonify({
        "status": "success",
        "data": data
    }), 200

@habit_api.route("/coach/chat", methods=["POST"])
def ai_coach_chat():
    """Sends user message to the AI coach and returns the answer."""
    import services.ai_service as ai_service
    data = request.get_json() or {}
    message = data.get("message")
    history = data.get("history", [])
    
    if not message or not message.strip():
        return jsonify({
            "status": "error",
            "message": "Message is required."
        }), 400
        
    result = ai_service.get_ai_coach_response(message, chat_history=history)
    if result["status"] == "error":
        return jsonify(result), 500
        
    return jsonify(result), 200
