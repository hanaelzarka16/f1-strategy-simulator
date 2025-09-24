import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt

# Enable FastF1 cache (downloads data once, then reuses it)
fastf1.Cache.enable_cache('cache')  

# Load a race session (example: 2023 British GP Race)
session = fastf1.get_session(2023, 'British Grand Prix', 'R')
session.load()

# Plot tyre stints for all drivers
fig, ax = plt.subplots(figsize=(12, 6))
fastf1.plotting.plot_stints(session, ax=ax)
plt.title("Tyre Stints - 2023 British GP")
plt.show()
