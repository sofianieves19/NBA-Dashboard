# IMPORTS AND DATA LOADING
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, shotchartdetail

st.set_page_config(page_title="NBA Shot Explorer", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&display=swap');

html, body, .stApp, .stApp p, .stApp label, .stApp button,
.stApp input, h1, h2, h3, h4, h5, h6,
[data-testid="stMetric"] *, [data-baseweb="select"] *, [data-baseweb="tab"] {
    font-family: 'Oswald', sans-serif !important;
}

.block-container {padding-top: 2rem;}
h1 {font-weight: 700; letter-spacing: -1px;}
[data-testid="stMetric"] {
    background: #000435;
    border-left: 4px solid #E86100;
    border-radius: 12px;
    padding: 14px 18px;
}

/* Page title */
h1 {font-size: 3rem;}

/* Player name (info.header) and team line (info.subheader) */
h2 {font-size: 2.2rem;}
h3 {font-size: 1.4rem;}

/* Caption under the team (season and season type) */
[data-testid="stCaptionContainer"] {font-size: 1.1rem;}

/* Stat cards: the big number and the label above it */
[data-testid="stMetricValue"] {font-size: 1.5rem !important;}
[data-testid="stMetricLabel"] p {font-size: 1.5rem !important;}

/* Tab names */
button[data-baseweb="tab"] p {font-size: 1.1rem;}

/* Labels above dropdowns, radios, and sliders */
[data-testid="stWidgetLabel"] p {font-size: 1rem;}

/* Search button text */
.stButton button p {font-size: 1.1rem;}

/* General body text */
.stApp p {font-size: 1rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_player_list():
    return pd.DataFrame(players.get_players())


from datetime import date

def get_seasons(player_id=None):
    today = date.today()
    last = today.year if today.month >= 10 else today.year - 1
    return [f"{y}-{str(y + 1)[-2:]}" for y in range(last, 1995, -1)]


import time

@st.cache_data(show_spinner=False)
def get_shots(player_id, season, season_type):
    last_error = None
    for attempt in range(3):
        try:
            shots = shotchartdetail.ShotChartDetail(
                team_id=0,
                player_id=player_id,
                season_nullable=season,
                season_type_all_star=season_type,
                context_measure_simple="FGA",
                timeout=30,
            )
            return shots.get_data_frames()[0]
        except Exception as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
    raise last_error


### COURT DRAWING AND STYLING
def arc(cx, cy, r, a0, a1, n=100):
    t = np.linspace(np.radians(a0), np.radians(a1), n)
    return cx + r * np.cos(t), cy + r * np.sin(t)


def court_traces(color="#F0F0F0", width=2):
    y3 = np.sqrt(237.5**2 - 220**2)                 # where corner 3 meets the arc
    theta = np.degrees(np.arctan2(y3, 220))
    shapes = [
        ([-250, 250, 250, -250, -250], [-47.5, -47.5, 422.5, 422.5, -47.5]),  # boundary
        ([-80, -80, 80, 80], [-47.5, 142.5, 142.5, -47.5]),                   # outer paint
        ([-60, -60, 60, 60], [-47.5, 142.5, 142.5, -47.5]),                   # inner paint
        ([-30, 30], [-7.5, -7.5]),                                            # backboard
        arc(0, 0, 7.5, 0, 360),                                               # rim
        arc(0, 0, 40, 0, 180),                                                # restricted area
        arc(0, 142.5, 60, 0, 360),                                            # free throw circle
        ([-220, -220], [-47.5, y3]),                                          # left corner 3
        ([220, 220], [-47.5, y3]),                                            # right corner 3
        arc(0, 0, 237.5, theta, 180 - theta),                                 # 3-point arc
        arc(0, 422.5, 60, 180, 360),                                          # half-court circle
    ]
    return [
        go.Scatter(x=x, y=y, mode="lines", hoverinfo="skip", showlegend=False,
                   line=dict(color=color, width=width))
        for x, y in shapes
    ]

FONT_FAMILY = "Oswald, sans-serif"

def style(fig, title):
    fig.update_layout(
        title=dict(text=title, font=dict(size=22, family=FONT_FAMILY, color="white"), x=0.5,xanchor="center"),
        height=720,
        plot_bgcolor="#000435",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family=FONT_FAMILY, size=14),
        xaxis=dict(range=[-250, 250], visible=False, title="Shot Zone", tickangle=0),
        yaxis=dict(range=[-47.5, 422.5], visible=False, scaleanchor="x"),
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
    )
    return fig


# function for displaying collage image
import base64

@st.cache_data
def load_landing_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def show_landing():
    data = load_landing_b64("nbaCollage.png")
    st.markdown(f"""
    <style>
    .landing-img {{
        position: fixed !important;
        left: 0 !important;
        right: 0 !important;
        bottom: -2px !important;
        width: 100% !important;
        aspect-ratio: 1813/644;
        background-image: url("data:image/png;base64,{data}");
        background-size: 101% 101%;
        background-position: center bottom;
        background-repeat: no-repeat;
        z-index: 0;
        pointer-events: none;
    }}
    </style>
    <div class="landing-img"></div>
    """, unsafe_allow_html=True)


### INTERFACE
st.title("NBA Shot Analyzer")

plist = get_player_list()
plist = plist[plist["is_active"]]

# ---- Controls ----
col_a, col_b, col_c = st.columns([2, 1, 1])

pick = col_a.selectbox(
    "Player",
    sorted(plist["full_name"]),
    index=None,                              # starts empty
    placeholder="Type a player name...",
)

if pick is None:
    st.info("Search for a player to get started.")
    show_landing()
    st.stop()

pick_id = int(plist.loc[plist["full_name"] == pick, "id"].iloc[0])
pick_season = col_b.selectbox("Season", get_seasons(pick_id))
pick_type = col_c.radio("Season type", ["Regular Season", "Playoffs"], horizontal=True)

# ---- Search button: save the choices only when clicked ----
if st.button("Search", type="primary"):
    st.session_state["query"] = {
        "name": pick,
        "player_id": pick_id,
        "season": pick_season,
        "season_type": pick_type,
    }

if "query" not in st.session_state:
    show_landing()
    st.stop()

q = st.session_state["query"]
name, player_id = q["name"], q["player_id"]
season, season_type = q["season"], q["season_type"]


# ---- Load shots ----
with st.spinner("Loading shots from NBA.com..."):
    try:
        df = get_shots(player_id, season, season_type)
    except Exception:
        st.error("NBA.com didn't respond. Wait a minute and press Search again.")
        st.stop()

# ---- Stop here if there's nothing to show ----
if df.empty:
    st.warning(f"{name} has no {season_type.lower()} shot data for {season}.")
    st.stop()

# ---- Header (only runs when df has shots) ----
ordered = df.sort_values("GAME_DATE")
team_names = ordered["TEAM_NAME"].drop_duplicates().tolist()
team_ids = ordered["TEAM_ID"].drop_duplicates().tolist()
teams_text = " → ".join(team_names)

head, logo, info = st.columns([1, 1, 4])
head.image(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png")
if team_ids:
    logo.image(f"https://cdn.nba.com/logos/nba/{team_ids[-1]}/global/L/logo.svg", width=120)
info.header(name)
info.subheader(teams_text)
info.caption(f"{season} · {season_type}")



# ---- Headline stats ----
fga, fgm = len(df), int(df["SHOT_MADE_FLAG"].sum())
threes = df[df["SHOT_TYPE"] == "3PT Field Goal"]
fg3a, fg3m = len(threes), int(threes["SHOT_MADE_FLAG"].sum())
efg = (fgm + 0.5 * fg3m) / fga * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("FG", f"{fgm}/{fga}", f"{fgm / fga * 100:.1f}%", delta_color="off")
c2.metric("3PT", f"{fg3m}/{fg3a}", f"{fg3m / fg3a * 100:.1f}%" if fg3a else "n/a", delta_color="off")
c3.metric("eFG%", f"{efg:.1f}%")
c4.metric("Avg shot distance", f"{df['SHOT_DISTANCE'].mean():.1f} ft")

tab_heat, tab_chart, tab_zones = st.tabs(["Heat map", "Shot chart", "Zones"])

# ---- Heat map ----
with tab_heat:
    metric = st.radio("Show", ["All attempts", "Made shots only"], horizontal=True)
    bin_size = st.slider("Bin size", 10, 40, 15, step=5)
    data = df if metric == "All attempts" else df[df["SHOT_MADE_FLAG"] == 1]

    counts, _, _ = np.histogram2d(
    data["LOC_X"], data["LOC_Y"],
    bins=[np.arange(-250, 250 + bin_size, bin_size),
          np.arange(-47.5, 422.5 + bin_size, bin_size)],
    )
    max_count = int(counts.max())

    # Pick a tick spacing that suits the data, then end on the max
    step = 10 if max_count > 20 else 5 if max_count > 10 else 1
    ticks = list(range(0, max_count + 1, step))
    if ticks[-1] == max_count:
        labels = [str(t) for t in ticks]
    else:
        if max_count - ticks[-1] < step / 2:   # too close to the max, drop it
            ticks.pop()
        ticks.append(max_count)
        labels = [str(t) for t in ticks]
        labels[-1] = f"{max_count} (max)"


    fig = go.Figure()
    fig.add_trace(go.Histogram2d(
        x=data["LOC_X"], y=data["LOC_Y"],
        xbins=dict(start=-250, end=250, size=bin_size),
        ybins=dict(start=-47.5, end=422.5, size=bin_size),
        colorscale=[[0, "rgba(0,0,0,0)"], [0.03, "#ffffe0"],[0.2, "#ffff00"], [0.5, "#ff8000"], [0.7, "#ff4000"], [1, "#ff0000"]],
        zmin=0,
        zmax=max_count,
        colorbar=dict(title="Shots", tickvals=ticks, ticktext=labels),
        opacity=0.85,
    ))
    for t in court_traces():
        fig.add_trace(t)
    st.plotly_chart(style(fig, f"{name}'s Heat Map, {season}"), use_container_width=True)

# ---- Shot chart ----
with tab_chart:
    fig = go.Figure()
    for t in court_traces():
        fig.add_trace(t)
    for flag, label, color, symbol in [(0, "Missed", "red", "x"), (1, "Made", "green", "circle")]:
        d = df[df["SHOT_MADE_FLAG"] == flag]
        fig.add_trace(go.Scatter(
            x=d["LOC_X"], y=d["LOC_Y"], mode="markers", name=label,
            marker=dict(color=color, symbol=symbol, size=8, opacity=0.7),
            customdata=d[["ACTION_TYPE", "SHOT_DISTANCE"]],
            hovertemplate="%{customdata[0]}<br>%{customdata[1]} ft<extra>" + label + "</extra>",
        ))
    st.plotly_chart(style(fig, f"{name} shot chart, {season}"), use_container_width=True)

# ---- Zone breakdown ----
with tab_zones:
    zone = (
        df.groupby("SHOT_ZONE_BASIC")
        .agg(FGA=("SHOT_MADE_FLAG", "size"), FGM=("SHOT_MADE_FLAG", "sum"))
        .assign(**{"FG%": lambda d: (d["FGM"] / d["FGA"] * 100).round(1)})
        .sort_values("FGA", ascending=False)
        .rename_axis("Shot Zone")
    )
    st.dataframe(zone, use_container_width=True)

    # break long names onto two lines so flat labels don't overlap
    #labels = [z.replace(" ", "<br>", 1) if len(z) > 10 else z for z in zone.index]

    fig = go.Figure(go.Bar(
        x=zone.index,
        y=zone["FG%"],
        marker_color="#F58426",
        text=zone["FG%"].astype(str) + "%",
        textposition="outside",
        hovertemplate="%{customdata}<br>FG%: %{y}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="FG% by zone", x=0.5, xanchor="center",
                   font=dict(family=FONT_FAMILY, size=22, color="white")),
        plot_bgcolor="#002766",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color="white"),
        xaxis=dict(title="Shot Zone", tickangle=0),
        yaxis=dict(title="FG%", gridcolor="#F0F0F0", range=[0, 110]),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)