"""
Web Modul — Flask Dashboard & API Routen
"""
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    """Webseite zum Am-Laufen-Halten des Bots auf Railway."""
    return "<h1>𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 Bot is Online!</h1>"
