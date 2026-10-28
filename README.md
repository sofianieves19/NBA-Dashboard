# NBA Shot Explorer

An interactive web app for exploring NBA shot data. Search for a player, pick a season, and dig into where they shoot from, how efficiently they shoot, and what their shot profile looks like on a court heat map.

Built with [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/python/), and the [`nba_api`](https://github.com/swar/nba_api) package, and packaged with Docker.

<img width="1466" height="832" alt="Screenshot 2026-10-28 at 4 47 26 PM" src="https://github.com/user-attachments/assets/66d7d90e-1250-4a59-abd9-c357ed754a1a" />


## Features

- **Player search:** start typing a name and the dropdown filters to matching players. Nothing loads until you press **Search**.
- **Season and season type:** choose any season from 1996-97 onward, regular season or playoffs.
- **Player header:** headshot, team logo, and the team name(s) for that season. Traded players show each team in the order they played for them.
- **Headline stats:** FG, 3PT, eFG%, and average shot distance.
- **Heat map:** a 2D histogram of shot locations drawn over a court, with an adjustable bin size, a toggle between all attempts and made shots, and a color legend that includes the maximum count.
- **Shot chart:** every made and missed shot plotted on the court, with hover details (shot type and distance).
- **Zone breakdown:** attempts, makes, and FG% for each court zone, plus a bar chart.
- **Custom styling:** dark theme, custom font, styled stat cards, and a landing image before the first search.

## How it works

Shot locations come from NBA.com's `ShotChartDetail` endpoint through `nba_api`. Coordinates are in tenths of a foot with the hoop at `(0, 0)`. The court is drawn in code with Plotly, so the court lines and the shots always share the same coordinate system and line up exactly.

Results are cached with `@st.cache_data`, so switching tabs or moving sliders doesn't re-request data from NBA.com. Failed requests are retried automatically, and seasons with no data show a warning instead of an error.

## Project structure

```
.
├── app.py                  # The Streamlit app
├── nbaCollage.png          # Image shown before the first search
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build instructions
├── docker-compose.yml      # One-command Docker run
├── .dockerignore           # Files excluded from the Docker image
├── .gitignore
├── .streamlit/
│   └── config.toml         # Theme colors and font
└── README.md
```

## Getting started

### Requirements

- Python 3.9 or newer (or just Docker, see below)
- An internet connection (data is fetched from NBA.com)

### Run locally

```bash
git clone https://github.com/sofianieves19/NBA-Dashboard.git
cd NBA-Dashboard
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Your browser opens to `http://localhost:8501`. Press **Ctrl+C** in the terminal to stop the app.

Use the same Python for installing and running. Mixing interpreters (for example Anaconda and a system Python) is the most common cause of `ModuleNotFoundError`.

### Run with Docker

Install and open [Docker Desktop](https://www.docker.com/products/docker-desktop/), then from the project folder:

```bash
docker build -t nba-shot-explorer .
docker run -p 8501:8501 nba-shot-explorer
```

Or with Docker Compose:

```bash
docker compose up --build
```

Then open `http://localhost:8501`. Stop it with **Ctrl+C**, or `docker compose down`.

If you edit the code, rebuild the image (`docker build ...`) for the changes to appear in the container.

## Usage

1. Type a player's name in the **Player** box and select a match.
2. Choose a **Season** and **Season type**.
3. Click **Search**.
4. Explore the **Heat map**, **Shot chart**, and **Zones** tabs.

## Configuration

**Theme:** colors and the base font live in `.streamlit/config.toml`. Extra styling (the custom font, stat cards, button colors) is in the `<style>` block near the top of `app.py`.

**Landing image:** replace `landing.jpg` with your own. If you use a PNG, change `data:image/jpeg` to `data:image/png` in `show_landing()`. Keep the file small, since it is embedded directly into the page.

**Chart font:** `FONT_FAMILY` in `app.py` controls the chart text. Keep it in sync with the font in the CSS block.

## Deploying

The app is a standard container, so it can run anywhere that runs Docker. For AWS, the general path is:

1. Create an Amazon ECR repository.
2. Build the image with `--platform linux/amd64`, tag it, and push it to ECR.
3. Run it with a container service such as Amazon ECS Express Mode (container port `8501`, health check path `/_stcore/health`), or a simpler option like Amazon Lightsail containers.

**Important:** NBA.com often blocks requests from cloud servers, so live API calls may time out once the app is deployed, even though they work on a home network. The usual workaround is to download shot data ahead of time on your own machine, save it as CSV or Parquet files, include them in the image, and have the app load those files instead of calling the API.

Running a container on AWS costs money while it is running. Delete the service when you're done experimenting, and set a billing alert.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Install packages with the same Python you run the app with: `python3 -m pip install -r requirements.txt` |
| `ReadTimeout` from `stats.nba.com` | NBA.com is slow or throttling requests. Wait a minute and press **Search** again. Try a different network or turn off your VPN. |
| A new player is missing from the dropdown | Update the library: `python3 -m pip install --upgrade nba_api` |
| "No shot data" warning | The player didn't play in that season or season type. |
| Old styling after editing CSS | Stop the app with Ctrl+C, rerun it, and hard refresh the browser (Cmd+Shift+R). |
| Port 8501 already in use | An old instance is running. Stop it with `pkill -f streamlit`, or use `-p 8080:8501` with Docker. |
| `docker: command not found` | Open Docker Desktop and make sure its command-line tools are installed (Settings > Advanced), then open a new terminal. |
| `index` / `placeholder` errors | Your Streamlit is out of date: `python3 -m pip install --upgrade streamlit` |

## Known limitations

- NBA.com's API is unofficial and can be slow, rate-limited, or blocked from cloud hosts.
- The season list is generated locally (1996-97 to the current season), so it includes seasons a player may not have played. Those show a "No shot data" message.
- Shot chart data is only available from 1996-97 onward.

## Ideas for future features

- Compare two players or seasons side by side
- Filter by shot type, action type, or game date
- Color the heat map by FG% instead of attempt count
- Filter by team for players traded mid-season
- Pre-downloaded data for offline use and reliable deployment

## Acknowledgments

- [`nba_api`](https://github.com/swar/nba_api) by Swar Patel and contributors
- Data from NBA.com. This project is not affiliated with or endorsed by the NBA.
