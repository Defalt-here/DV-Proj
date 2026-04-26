# Renewable Energy Worldwide Dashboard

This project is an interactive data visualization dashboard built with Streamlit, Plotly, and pandas. It presents renewable electricity generation and capacity data from Our World in Data in an interactive web app.

## What it is

- A Streamlit dashboard for exploring renewable energy trends globally.
- Uses data files stored in the `Data/` directory.
- Includes filters for year, year range, renewable sources, country comparisons, and energy mix views.
- Shows maps, trend charts, rankings, heatmaps, and capacity vs production insights.

## What it can do

- Display a world map of renewable energy production and renewable electricity share.
- Show trend charts for renewable generation over time.
- Rank countries by renewable energy production.
- Compare renewable sources such as wind, hydro, solar, and other bio/geothermal energy.
- Visualize country-level energy mix and capacity data.

## How to run it

1. Activate the project virtual environment:

```bash
source .venv/bin/activate
```

2. Install dependencies if needed:

```bash
pip install -r requirements.txt
```

3. Start the Streamlit app:

```bash
streamlit run app.py
```

4. Open the local URL shown in the terminal (usually `http://localhost:8502`).

## Project files

- `app.py` — main Streamlit application code.
- `requirements.txt` — pinned Python dependencies.
- `.gitignore` — ignore rules for the virtual environment, caches, and Python artifacts.
- `Data/` — CSV datasets used by the app.

## Data files included

The `Data/` directory includes renewable energy datasets such as:

- renewable share of energy
- renewable share of electricity
- renewable production by source
- installed solar and wind capacity
- hydropower and biofuel production

## What we can do next

- Add a `README` screenshot or sample dashboard images.
- Include a `requirements-dev.txt` and a test suite for validation.
- Add a `setup.sh` or `Makefile` to automate environment setup and app launch.
- Improve the app by adding more drill-down analysis, export options, or data download links.
- Add a short project report summarizing findings, methodology, and insights.

## Report creation support

To help create a project report, we can:

- Summarize the main dashboard findings.
- Describe the dataset sources and cleaning assumptions.
- Document the usage of Streamlit, Plotly, and pandas.
- Add visual examples of the dashboard sections.
- Provide recommendations for next analysis steps or data improvements.
