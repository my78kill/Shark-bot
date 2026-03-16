from flask import Flask
from bot import start_bot

app = Flask(__name__)

@app.route("/")
def home():
    return "🦈 Shark Game Bot Running!"

if __name__ == "__main__":
    start_bot()
