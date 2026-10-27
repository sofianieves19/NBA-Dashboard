
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats

player = players.find_players_by_full_name('Stephon Castle')

print(player)


career = playercareerstats.PlayerCareerStats(
    player_id=1642264
)

career_df = career.get_data_frames()[0]

career_df.head()


# Obtaining shot data for the heat chart

from nba_api.stats.endpoints import shotchartdetail
import pandas as pd

player_id = 1642264  # Stephon

shots = shotchartdetail.ShotChartDetail(
    team_id=0,
    player_id=player_id,
    season_nullable='2025-26',
    context_measure_simple='FGA'
)

df = shots.get_data_frames()[0]

#print(df.head())
#print(len(df))

# using image for heat map

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

court = mpimg.imread("halfcourt.png")

h, w = court.shape[0], court.shape[1]
left_px = right_px = 75
top_px = bottom_px = 55   

sx = 500 / (w - left_px - right_px)
sy = 470 / (h - top_px - bottom_px)

extent = [-250 - left_px*sx, 250 + right_px*sx,
          -52.5 - bottom_px*sy, 417.5 + top_px*sy]

fig, ax = plt.subplots(figsize=(10,9))


ax.imshow(court, extent=extent, aspect="auto", origin="lower")

heat = ax.hexbin(
    df["LOC_X"], df["LOC_Y"],
    gridsize=30,
    extent=(-250, 250, -52.5, 417.5),
    cmap="YlOrRd",
    mincnt=1,
    alpha=0.8
)

plt.colorbar(heat, label="Shot Attempts")

ax.set_xlim(extent[0], extent[1])
ax.set_ylim(extent[2], extent[3])

ax.axis("off")

plt.title("Castle Shot Heat Map")
plt.show()

# Plot chart

def plot_shot_chart(shot_df, player_name):

    # Separate makes and misses
    made = shot_df[shot_df["SHOT_MADE_FLAG"] == 1]
    missed = shot_df[shot_df["SHOT_MADE_FLAG"] == 0]


    fig, ax = plt.subplots(figsize=(10, 9))


    # 1. Put court image in background
    ax.imshow(
        court,
        extent=[-250, 250, -50, 420],
        aspect="auto"
    )


    # 2. Plot missed shots
    ax.scatter(
        missed.LOC_X,
        missed.LOC_Y,
        color="red",
        marker="x",
        s=50,
        alpha=.6,
        label="Missed"
    )


    # 3. Plot made shots
    ax.scatter(
        made.LOC_X,
        made.LOC_Y,
        color="green",
        s=50,
        alpha=.8,
        label="Made"
    )


    # 4. Match NBA coordinate system
    ax.set_xlim(-250, 250)
    ax.set_ylim(-50, 420)

    ax.axis("off")

    ax.legend()

    plt.title(f"Castle Shot Chart")

    plt.show()

plot_shot_chart(df, "Stephon Castle")
