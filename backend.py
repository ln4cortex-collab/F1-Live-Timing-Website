from flask import Flask, jsonify, request
from flask_cors import CORS
import fastf1
import pandas as pd

app = Flask(__name__)
CORS(app)

# Enable cache to speed up loading
fastf1.Cache.enable_cache("cache")

def format_time(td):
    """Converts Timedelta to a string format like 1:23.456"""
    if pd.isna(td) or td == "":
        return ""
    try:
        total_seconds = td.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}" if minutes > 0 else f"{seconds:06.3f}"
    except:
        return ""

@app.route("/api/calendar/<year>")
def calendar(year):
    try:
        schedule = fastf1.get_event_schedule(int(year))
        races = [event["EventName"] for _, event in schedule.iterrows()]
        return jsonify(races)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/results")
def results():
    year = int(request.args.get("year"))
    gp = request.args.get("gp")
    session_type = request.args.get("session")

    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load()
        
        # fillna prevents JSON errors by replacing NaN with empty strings
        results_df = session.results.fillna("")

        data = []
        for _, d in results_df.iterrows():
            # Safely handle TeamColor
            team_hex = str(d.get("TeamColor", "ffffff"))
            
            # SAFE POSITION CONVERSION:
            # Check if position is a number or a non-empty string before converting
            pos = d.get("Position")
            display_pos = int(pos) if (isinstance(pos, (int, float)) or (isinstance(pos, str) and pos.isdigit())) else ""

            row = {
                "DriverNumber": str(d.get("DriverNumber", "")),
                "BroadcastName": str(d.get("BroadcastName", "")),
                "TeamName": str(d.get("TeamName", "")),
                "TeamColor": f"#{team_hex}" if team_hex else "#ffffff",
                "Position": display_pos,
                "Status": str(d.get("Status", "")),
            }

            if session_type == "Q":
                row["Q1"] = format_time(d.get("Q1"))
                row["Q2"] = format_time(d.get("Q2"))
                row["Q3"] = format_time(d.get("Q3"))
            else:
                row["Points"] = d.get("Points", 0)
                row["Laps"] = d.get("Laps", 0)

            data.append(row)

        return jsonify(data)
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
