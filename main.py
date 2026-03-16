from flask import Flask
import threading
from bot import start_bot

app = Flask(__name__)

@app.route("/")
def home():
    return "🦈 Shark Game Bot Running!"

def run_bot():
    start_bot()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)
