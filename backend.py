from flask import Flask, jsonify, request
from flask_cors import CORS
import fastf1
from fastf1.ergast import Ergast
import fastf1.plotting
import pandas as pd

app = Flask(__name__)
CORS(app)

# Enable cache for faster loading
fastf1.Cache.enable_cache("cache")
ergast = Ergast()

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
        session.load(laps=False, telemetry=False, weather=False)
        
        # Use fillna to prevent empty strings from breaking the logic
        results_df = session.results.fillna("")
        data = []
        for _, d in results_df.iterrows():
            # Fallback for TeamColor if missing
            team_color = d.get("TeamColor")
            if not team_color or team_color == "":
                team_color = fastf1.plotting.get_team_color(d["TeamName"], session)
            
            data.append({
                "DriverNumber": str(d.get("DriverNumber", "")),
                "BroadcastName": str(d.get("BroadcastName", "")),
                "Abbreviation": str(d.get("Abbreviation", "")),
                "TeamName": str(d.get("TeamName", "")),
                "TeamColor": f"#{team_color}" if not str(team_color).startswith("#") else team_color,
                "Position": str(d.get("Position", "")),
                "Status": str(d.get("Status", "")),
                "Points": str(d.get("Points", "0")),
                "Laps": str(d.get("Laps", "0"))
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/standings/drivers/<year>")
def wdc(year):
    try:
        standings = ergast.get_driver_standings(season=int(year))
        df = standings.content[0]
        
        # Reference a session to get the team colors for the UI
        try:
            ref_session = fastf1.get_session(int(year), 1, 'R')
            ref_session.load(laps=False, telemetry=False, weather=False)
        except: ref_session = None

        data = []
        for _, r in df.iterrows():
            team_name = r['constructorNames'][0] if r['constructorNames'] else ""
            color = "ffffff"
            if ref_session:
                try: color = fastf1.plotting.get_team_color(team_name, ref_session)
                except: pass

            data.append({
                "Position": str(r['position']),
                "Driver": f"{r['givenName']} {r['familyName']}".upper(),
                "Team": team_name.upper(),
                "TeamColor": f"#{color}" if not str(color).startswith("#") else color,
                "Points": str(r['points']),
                "Wins": str(r['wins'])
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/standings/constructors/<year>")
def wcc(year):
    try:
        standings = ergast.get_constructor_standings(season=int(year))
        df = standings.content[0]
        
        try:
            ref_session = fastf1.get_session(int(year), 1, 'R')
            ref_session.load(laps=False, telemetry=False, weather=False)
        except: ref_session = None

        data = []
        for _, r in df.iterrows():
            team_name = r['constructorName']
            color = "ffffff"
            if ref_session:
                try: color = fastf1.plotting.get_team_color(team_name, ref_session)
                except: pass
                
            data.append({
                "Position": str(r['position']),
                "Team": team_name.upper(),
                "TeamColor": f"#{color}" if not str(color).startswith("#") else color,
                "Points": str(r['points']),
                "Wins": str(r['wins'])
            })
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
