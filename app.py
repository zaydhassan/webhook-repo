from flask import Flask, request, jsonify, render_template
from datetime import datetime
from models import events_collection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/webhook", methods=["POST"])
def github_webhook():
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json

    data = None

    if event_type == "push":
        commit = payload.get("head_commit")
        if not commit:
            return jsonify({"status": "ignored"})

        data = {
            "request_id": commit.get("id"),
            "author": commit.get("author", {}).get("name"),
            "action": "PUSH",
            "from_branch": payload.get("ref", "").split("/")[-1],
            "to_branch": payload.get("ref", "").split("/")[-1],
            "timestamp": datetime.utcnow()
        }

    elif event_type == "pull_request":
        pr = payload.get("pull_request")
        action = payload.get("action")

        if not pr or action not in ["opened", "closed"]:
            return jsonify({"status": "ignored"})

        data = {
            "request_id": str(pr.get("id")),
            "author": pr.get("user", {}).get("login"),
            "from_branch": pr.get("head", {}).get("ref"),
            "to_branch": pr.get("base", {}).get("ref"),
            "timestamp": datetime.utcnow()
        }

        if action == "closed" and pr.get("merged"):
            data["action"] = "MERGE"
        else:
            data["action"] = "PULL_REQUEST"

    else:
        return jsonify({"status": "ignored"})

    if data and not events_collection.find_one({"request_id": data["request_id"]}):
        events_collection.insert_one(data)

    return jsonify({"status": "stored"})

@app.route("/events", methods=["GET"])
def get_events():
    result = []

    events = events_collection.find().sort("timestamp", -1).limit(10)

    for event in events:
        time_str = event["timestamp"].strftime("%d %B %Y - %I:%M %p UTC")

        if event["action"] == "PUSH":
            text = f'{event["author"]} pushed to {event["to_branch"]} on {time_str}'
        elif event["action"] == "PULL_REQUEST":
            text = (
                f'{event["author"]} submitted a pull request from '
                f'{event["from_branch"]} to {event["to_branch"]} on {time_str}'
            )
        else:
            text = (
                f'{event["author"]} merged branch '
                f'{event["from_branch"]} to {event["to_branch"]} on {time_str}'
            )

        result.append(text)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)