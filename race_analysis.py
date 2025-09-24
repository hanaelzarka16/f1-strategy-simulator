import fastf1
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Enable cache
fastf1.Cache.enable_cache('cache')

# Load a race session
session = fastf1.get_session(2023, 'British Grand Prix', 'R')
session.load()

# Define tyre colours manually (FIA standard)
compound_colors = {
    'SOFT': 'red',
    'MEDIUM': 'yellow',
    'HARD': 'white',
    'INTERMEDIATE': 'green',
    'WET': 'blue'
}

# Get driver list with abbreviations
drivers = [session.get_driver(drv)["Abbreviation"] for drv in session.drivers]

# Create a plot
fig, ax = plt.subplots(figsize=(12, 8))

for drv in drivers:
    laps = session.laps.pick_drivers(drv)

    # Group laps by stint and compound
    stints = laps.groupby(['Stint', 'Compound'])['LapNumber'].agg(['min', 'max']).reset_index()

    for _, row in stints.iterrows():
        color = compound_colors.get(row['Compound'].upper(), 'grey')
        ax.barh(drv, row['max'] - row['min'] + 1,
                left=row['min'],
                color=color,
                edgecolor='black')

ax.set_xlabel("Lap")
ax.set_ylabel("Driver")
ax.set_title("Tyre Stints - 2023 British GP")

# Add a legend
legend_elements = [Patch(facecolor=color, edgecolor='black', label=compound)
                   for compound, color in compound_colors.items()]
ax.legend(handles=legend_elements, title="Tyre Compounds", loc='upper right')

plt.tight_layout()
plt.savefig("stints.png", dpi=300)

plt.show()
