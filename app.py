import os
from flask import Flask, render_template, jsonify, request
from espn_api.football import League
from openai import OpenAI

app = Flask(__name__, template_folder="templates")

# Load environment variables
LEAGUE_ID = int(os.getenv("LEAGUE_ID", "505229264"))   # your ESPN league id
YEAR = int(os.getenv("SEASON_YEAR", "2025"))
TEAM_ID = int(os.getenv("TEAM_ID", "8"))  # your team ID in ESPN
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize ESPN league
league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/team-overview")
def team_overview():
    my_team = league.teams[TEAM_ID - 1]
    data = {
        "name": my_team.team_name,
        "record": f"{my_team.wins}-{my_team.losses}",
        "standing": my_team.standing,
        "points_for": my_team.points_for,
        "waiver_rank": my_team.waiver_rank,
    }
    return jsonify(data)


@app.route("/api/top-performers")
def top_performers():
    my_team = league.teams[TEAM_ID - 1]
    players = sorted(my_team.roster, key=lambda p: p.points, reverse=True)[:3]
    out = []
    for p in players:
        out.append({
            "name": p.name,
            "position": p.position,
            "team": p.proTeam,
            "last_week": p.points,
            "proj": p.projected_points
        })
    return jsonify(out)


@app.route("/api/projections")
def projections():
    my_team = league.teams[TEAM_ID - 1]

    weeks = []
    actuals = []
    projected = []

    for matchup in league.schedule:
        if my_team in [matchup.home_team, matchup.away_team]:
            week = matchup.week
            weeks.append(f"Week {week}")

            if matchup.home_team == my_team:
                actuals.append(matchup.home_score)
                projected.append(matchup.home_projected)
            else:
                actuals.append(matchup.away_score)
                projected.append(matchup.away_projected)

    return jsonify({"weeks": weeks, "actuals": actuals, "projected": projected})


@app.route("/api/chat", methods=["POST"])
def chat():
    msg = request.json["message"]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a fantasy football co-manager. Give waiver, trade, and lineup advice."},
            {"role": "user", "content": msg}
        ]
    )
    return jsonify({"reply": response.choices[0].message.content})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
