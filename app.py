import secrets
from flask import Flask, render_template, jsonify
from routes.habit_routes import habit_api
from routes.journal_routes import journal_api

app = Flask(__name__)

# Cryptographically strong secret key to secure sessions if needed.
app.secret_key = secrets.token_hex(24)

# Register REST API Blueprints
app.register_blueprint(habit_api, url_prefix="/api")
app.register_blueprint(journal_api, url_prefix="/api")

# Serve beautiful Premium Glassmorphic Web Dashboard
@app.route("/")
def dashboard():
    """Renders the main AuraHabit tracking dashboard."""
    return render_template("index.html")

# Global JSON error handling for general application errors
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        "status": "error",
        "message": "The requested resource could not be found."
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "status": "error",
        "message": "An unexpected server error occurred. Please contact system support."
    }), 500

if __name__ == "__main__":
    # Start the local development web server
    app.run(debug=True, port=5000)
