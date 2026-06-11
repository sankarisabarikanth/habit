from flask import Blueprint, request, jsonify
import services.journal_service as service

journal_api = Blueprint("journal_api", __name__)

@journal_api.route("/journals", methods=["POST"])
def create_journal():
    """Create a new journal entry."""
    data = request.get_json() or {}
    date = data.get("date")
    title = data.get("title", "")
    content = data.get("content", "")
    mood = data.get("mood", "Neutral")
    habit_ids = data.get("habit_ids", [])
    
    try:
        new_journal = service.create_journal(
            date=date,
            title=title,
            content=content,
            mood=mood,
            habit_ids=habit_ids
        )
        return jsonify({
            "status": "success",
            "message": "Journal entry created successfully",
            "data": new_journal
        }), 201
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@journal_api.route("/journals", methods=["GET"])
def get_journals():
    """List journal entries, optionally filtered by date."""
    target_date = request.args.get("date")
    journals = service.get_all_journals()
    
    if target_date:
        target_date = target_date[:10]
        journals = [j for j in journals if j["date"] == target_date]
        
    return jsonify({
        "status": "success",
        "count": len(journals),
        "data": journals
    }), 200

@journal_api.route("/journals/<journal_id>", methods=["GET"])
def get_journal(journal_id):
    """Get a specific journal entry by ID."""
    journal = service.get_journal_by_id(journal_id)
    if not journal:
        return jsonify({
            "status": "error",
            "message": f"Journal entry with ID {journal_id} not found"
        }), 404
        
    return jsonify({
        "status": "success",
        "data": journal
    }), 200

@journal_api.route("/journals/<journal_id>", methods=["PUT"])
def update_journal(journal_id):
    """Update details of a specific journal entry."""
    data = request.get_json() or {}
    date = data.get("date")
    title = data.get("title")
    content = data.get("content")
    mood = data.get("mood")
    habit_ids = data.get("habit_ids")
    
    try:
        updated = service.update_journal(
            journal_id=journal_id,
            date=date,
            title=title,
            content=content,
            mood=mood,
            habit_ids=habit_ids
        )
        if not updated:
            return jsonify({
                "status": "error",
                "message": f"Journal entry with ID {journal_id} not found"
            }), 404
            
        return jsonify({
            "status": "success",
            "message": "Journal entry updated successfully",
            "data": updated
        }), 200
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@journal_api.route("/journals/<journal_id>", methods=["DELETE"])
def delete_journal(journal_id):
    """Delete a specific journal entry."""
    success = service.delete_journal(journal_id)
    if not success:
        return jsonify({
            "status": "error",
            "message": f"Journal entry with ID {journal_id} not found"
        }), 404
        
    return jsonify({
        "status": "success",
        "message": f"Journal entry with ID {journal_id} was successfully deleted"
    }), 200
