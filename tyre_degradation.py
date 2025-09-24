import fastf1
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# Enable cache
fastf1.Cache.enable_cache('cache')

# Load race session
session = fastf1.get_session(2023, 'British Grand Prix', 'R')
session.load()

# Tyre colours
compound_colors = {
    'HARD': 'grey',
    'MEDIUM': 'yellow',
    'SOFT': 'red'
}

# Top 3 finishers
drivers = ["VER", "NOR", "HAM"]

# Store slope results
results = []

# Create subplots (1 row, 3 columns)
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

for ax, driver in zip(axes, drivers):
    laps = session.laps.pick_drivers(driver).pick_quicklaps()

    for compound in laps['Compound'].unique():
        comp_laps = laps[laps['Compound'] == compound]
        x = comp_laps['LapNumber'].values.reshape(-1, 1)
        y = comp_laps['LapTime'].dt.total_seconds().values

        # Scatter plot
        ax.scatter(
            x, y,
            color=compound_colors.get(compound.upper(), 'black'),
            alpha=0.6,
            label=f"{compound}"
        )

        # Regression line + slope
        if len(x) > 1:
            model = LinearRegression().fit(x, y)
            slope = model.coef_[0]  # degradation rate in s/lap
            y_pred = model.predict(x)

            ax.plot(
                x, y_pred,
                color=compound_colors.get(compound.upper(), 'black'),
                linestyle='--',
                label=f"{compound} ({slope:+.3f}s/lap)"
            )

            # Save slope result
            results.append({
                "Driver": driver,
                "Compound": compound,
                "Degradation (s/lap)": slope
            })

    ax.set_title(f"{driver} – 2023 British GP")
    ax.set_xlabel("Lap Number")
    ax.legend()

axes[0].set_ylabel("Lap Time (s)")
plt.suptitle("Lap Time Degradation – Top 3 Finishers – 2023 British GP", fontsize=16)
plt.tight_layout()
plt.savefig("tyre_degradation_subplots.png", dpi=300)
plt.show()

# Create summary table
df_results = pd.DataFrame(results)
summary = df_results.pivot(index="Driver", columns="Compound", values="Degradation (s/lap)").round(3)

# Replace NaN with dash for readability
summary_clean = summary.fillna("–")

print("\n=== Degradation Rates (s/lap) ===\n")
print(summary_clean)

print("\n=== Markdown Table (for README.md) ===\n")
print(summary_clean.to_markdown())
