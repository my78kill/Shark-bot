from flask import Flask
import threading
from bot import start_bot

app = Flask(__name__)

@app.route("/")
def home():
    return "🦈 Shark Game Bot Running!"

def run():
    start_bot()

threading.Thread(target=run).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
