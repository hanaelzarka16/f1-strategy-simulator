# ============================================================
# F1 Pit Stop Delta Calculator
# Add this notebook to your f1-strategy-simulator repo
# Uses degradation rates already computed in your simulator
# ============================================================

import fastf1
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

fastf1.Cache.enable_cache('cache')

# ── 1. CONFIG ────────────────────────────────────────────────
# Change these to analyse any race/scenario
YEAR        = 2023
RACE        = 'British Grand Prix'
DRIVER      = 'VER'          # Driver to analyse
COMPOUND_A  = 'MEDIUM'       # Current compound (on track)
COMPOUND_B  = 'HARD'         # Alternative compound (after pit)
PIT_LOSS    = 22.0           # Pit stop time loss in seconds (typical ~20-25s)
CURRENT_LAP = 25             # Lap you are considering pitting
STINT_LAPS  = 30             # How many laps remain in the stint

# ── 2. LOAD SESSION DATA ─────────────────────────────────────
session = fastf1.get_session(YEAR, RACE, 'R')
session.load()

laps = session.laps.pick_driver(DRIVER).copy()
laps = laps[laps['PitOutTime'].isna()]        # remove out-laps
laps = laps[laps['PitInTime'].isna()]         # remove in-laps
laps['LapTime_s'] = laps['LapTime'].dt.total_seconds()
laps = laps.dropna(subset=['LapTime_s', 'Compound', 'TyreLife'])

# ── 3. COMPUTE DEGRADATION RATES ─────────────────────────────
def degradation_rate(laps_df, compound):
    """Linear regression of lap time vs tyre age for a compound."""
    data = laps_df[laps_df['Compound'] == compound].copy()
    data = data[
        (data['LapTime_s'] < data['LapTime_s'].mean() + 2 * data['LapTime_s'].std())
    ]
    if len(data) < 3:
        return None, None
    x = data['TyreLife'].values
    y = data['LapTime_s'].values
    coeffs = np.polyfit(x, y, 1)          # [slope, intercept]
    return coeffs[0], coeffs[1]           # deg_rate (s/lap), base_time

deg_A, base_A = degradation_rate(laps, COMPOUND_A)
deg_B, base_B = degradation_rate(laps, COMPOUND_B)

print(f"\n{'='*50}")
print(f"  {RACE} {YEAR}  |  Driver: {DRIVER}")
print(f"{'='*50}")
print(f"  {COMPOUND_A:8s}  deg rate: {deg_A:+.4f} s/lap  |  base: {base_A:.2f} s")
print(f"  {COMPOUND_B:8s}  deg rate: {deg_B:+.4f} s/lap  |  base: {base_B:.2f} s")
print(f"{'='*50}\n")

# ── 4. PROJECT LAP TIMES OVER REMAINING STINT ────────────────
laps_ahead = np.arange(1, STINT_LAPS + 1)

# Stay out on COMPOUND_A — tyre life continues from current lap
tyre_age_A = CURRENT_LAP + laps_ahead
proj_A = base_A + deg_A * tyre_age_A

# Pit now onto COMPOUND_B — fresh tyre, plus pit loss on lap 1
tyre_age_B = laps_ahead                   # fresh tyres after pit
proj_B = base_B + deg_B * tyre_age_B
proj_B[0] += PIT_LOSS                     # pit loss on the lap you pit

# Cumulative time delta: positive = staying out is faster
# negative = pitting is faster (undercut viable)
cum_delta = np.cumsum(proj_A - proj_B)

# ── 5. FIND CROSSOVER LAP ────────────────────────────────────
crossover = None
for i, delta in enumerate(cum_delta):
    if delta < 0:
        crossover = CURRENT_LAP + laps_ahead[i]
        break

print(f"  Pit loss assumed:     {PIT_LOSS} s")
print(f"  Analysing from lap:   {CURRENT_LAP}")
print(f"  Laps projected:       {STINT_LAPS}")

if crossover:
    print(f"\n  >> UNDERCUT VIABLE from lap {crossover}")
    print(f"     Pit on lap {CURRENT_LAP} -- {COMPOUND_B} recovers pit loss by lap {crossover}")
else:
    print(f"\n  >> Undercut NOT viable in the next {STINT_LAPS} laps")
    print(f"     Staying on {COMPOUND_A} is faster over this window")
print()

# ── 6. PLOT ──────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.suptitle(
    f'{RACE} {YEAR}  |  {DRIVER}  |  Pit Delta: {COMPOUND_A} vs {COMPOUND_B}\n'
    f'Pit loss = {PIT_LOSS}s  |  Analysed from lap {CURRENT_LAP}',
    fontsize=13, fontweight='bold', color='#1A1A2E'
)

lap_axis = CURRENT_LAP + laps_ahead

# -- Top: projected lap times
axes[0].plot(lap_axis, proj_A, label=f'Stay out ({COMPOUND_A})',
             color='#2E4057', linewidth=2)
axes[0].plot(lap_axis, proj_B, label=f'Pit to {COMPOUND_B}',
             color='#C0392B', linewidth=2, linestyle='--')
axes[0].set_ylabel('Projected Lap Time (s)', fontsize=11)
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)
axes[0].yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

# -- Bottom: cumulative delta
axes[1].axhline(0, color='black', linewidth=1, linestyle='-')
axes[1].fill_between(lap_axis, cum_delta, 0,
                     where=(cum_delta < 0), alpha=0.25,
                     color='#C0392B', label='Pit is faster (undercut viable)')
axes[1].fill_between(lap_axis, cum_delta, 0,
                     where=(cum_delta >= 0), alpha=0.2,
                     color='#2E4057', label='Stay out is faster')
axes[1].plot(lap_axis, cum_delta, color='#1A1A2E', linewidth=2)

if crossover:
    axes[1].axvline(crossover, color='#C0392B', linestyle=':', linewidth=1.5,
                    label=f'Crossover lap {crossover}')

axes[1].set_xlabel('Race Lap', fontsize=11)
axes[1].set_ylabel('Cumulative Time Delta (s)\n(negative = pit is faster)', fontsize=10)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'pit_delta_{DRIVER}_{COMPOUND_A}_vs_{COMPOUND_B}_lap{CURRENT_LAP}.png',
            dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved.")
