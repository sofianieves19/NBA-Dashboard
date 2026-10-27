# IMPORTS AND DATA LOADING
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, shotchartdetail

st.set_page_config(page_title="NBA Shot Explorer", layout="wide")


@st.cache_data
def get_player_list():
    return pd.DataFrame(players.get_players())


@st.cache_data(show_spinner=False)
def get_seasons(player_id):
    df = playercareerstats.PlayerCareerStats(
        player_id=player_id, timeout=60
    ).get_data_frames()[0]
    return df["SEASON_ID"].unique().tolist()[::-1]   # newest first


@st.cache_data(show_spinner=False)
def get_shots(player_id, season, season_type):
    shots = shotchartdetail.ShotChartDetail(
        team_id=0,
        player_id=player_id,
        season_nullable=season,
        season_type_all_star=season_type,
        context_measure_simple="FGA",
        timeout=60,
    )
    return shots.get_data_frames()[0]


### COURT DRAWING AND STYLING
def arc(cx, cy, r, a0, a1, n=100):
    t = np.linspace(np.radians(a0), np.radians(a1), n)
    return cx + r * np.cos(t), cy + r * np.sin(t)


def court_traces():
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
                   line=dict(color="black", width=2))
        for x, y in shapes
    ]


def style(fig, title):
    fig.update_layout(
        title=title, height=720, plot_bgcolor="white",
        xaxis=dict(range=[-250, 250], visible=False),
        yaxis=dict(range=[-47.5, 422.5], visible=False, scaleanchor="x"),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


### INTERFACE
st.title("NBA Shot Explorer")

# ---- Sidebar controls ----
plist = get_player_list()
active_only = st.sidebar.checkbox("Active players only", value=True)
if active_only:
    plist = plist[plist["is_active"]]

name = st.sidebar.selectbox("Player", sorted(plist["full_name"]))
player_id = int(plist.loc[plist["full_name"] == name, "id"].iloc[0])

season = st.sidebar.selectbox("Season", get_seasons(player_id))
season_type = st.sidebar.radio("Season type", ["Regular Season", "Playoffs"])

# ---- Load shots ----
with st.spinner("Loading shots from NBA.com..."):
    df = get_shots(player_id, season, season_type)

if df.empty:
    st.warning("No shot data for that player, season and season type.")
    st.stop()

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
    bin_size = st.slider("Bin size (1 unit = 0.1 ft)", 10, 40, 20, step=5)
    data = df if metric == "All attempts" else df[df["SHOT_MADE_FLAG"] == 1]

    fig = go.Figure()
    fig.add_trace(go.Histogram2d(
        x=data["LOC_X"], y=data["LOC_Y"],
        xbins=dict(start=-250, end=250, size=bin_size),
        ybins=dict(start=-47.5, end=422.5, size=bin_size),
        colorscale=[[0, "white"], [0.15, "#ffffb2"], [0.5, "#fd8d3c"], [1, "#bd0026"]],
        colorbar=dict(title="Shots"),
        opacity=0.85,
    ))
    for t in court_traces():
        fig.add_trace(t)
    st.plotly_chart(style(fig, f"{name} heat map, {season}"), use_container_width=True)

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
    )
    st.dataframe(zone, use_container_width=True)
    st.bar_chart(zone["FG%"])