import os
import subprocess
import datetime
import time
import pickle
import matplotlib.pyplot as plt
from collections import defaultdict

# Define the state file
STATE_FILE = "state.pkl"

# Load state or initialize if state file doesn't exist
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'rb') as f:
            return pickle.load(f)
    return {
        'outages': []
    }

# Save state to file
def save_state(state):
    with open(STATE_FILE, 'wb') as f:
        pickle.dump(state, f)

# Ping a website and return whether it's reachable
def ping_website(website):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", website],  # Modified for Windows compatibility
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception:
        return False

# Record outages
def record_outage(state, current_time, unreachable_percentage):
    state['outages'].append((current_time, unreachable_percentage))

# Generate outage graph and save to the appropriate folder
def generate_outage_graph(state, interval, folder):
    times = [entry[0] for entry in state['outages']]
    percentages = [entry[1] for entry in state['outages']]

    plt.figure(figsize=(10, 6))
    plt.plot(times, percentages, marker='o', linestyle='-', color='r')
    plt.title(f'Website Outage Percentages Over Time ({interval})')
    plt.xlabel('Time')
    plt.ylabel('Outage Percentage (%)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    if not os.path.exists(folder):
        os.makedirs(folder)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H")
    plt.savefig(f"{folder}/outage_report_{interval}_{current_time}.pdf")
    plt.close()

# Calculate approximate bandwidth usage
def calculate_bandwidth(website_count):
    # Approximate size of a single ping packet (64 bytes) and response (64 bytes)
    packet_size = 128  # bytes
    total_bandwidth = website_count * packet_size / 1024  # convert to KB
    return total_bandwidth

# Main function
def main():
    state = load_state()
    while True:
        # Read websites from file
        with open("websites.txt", "r") as file:
            websites = [line.strip() for line in file if line.strip()]

        current_time = datetime.datetime.now()
        unreachable = []

        # Ping each website
        for website in websites:
            if not ping_website(website):
                unreachable.append(website)

        # Calculate outage percentage
        total_websites = len(websites)
        if total_websites > 0:
            unreachable_percentage = (len(unreachable) / total_websites) * 100

            # Record outage if more than 50% unreachable
            if unreachable_percentage > 50:
                record_outage(state, current_time, unreachable_percentage)

            # Save state
            save_state(state)

            # Generate graphs for different intervals
            day_folder = current_time.strftime("reports/%Y/%m/%d")
            week_folder = current_time.strftime("reports/%Y/week_%U")
            month_folder = current_time.strftime("reports/%Y/%m")
            year_folder = current_time.strftime("reports/%Y")

            if current_time.minute == 0:
                generate_outage_graph(state, "hour", day_folder)
            if current_time.hour == 0 and current_time.minute == 0:
                generate_outage_graph(state, "day", day_folder)
            if current_time.weekday() == 0 and current_time.hour == 0 and current_time.minute == 0:
                generate_outage_graph(state, "week", week_folder)
            if current_time.day == 1 and current_time.hour == 0 and current_time.minute == 0:
                generate_outage_graph(state, "month", month_folder)
            if current_time.month == 1 and current_time.day == 1 and current_time.hour == 0 and current_time.minute == 0:
                generate_outage_graph(state, "year", year_folder)

        # Calculate and display bandwidth usage
        bandwidth_usage = calculate_bandwidth(total_websites)
        print(f"[{current_time}] Total Websites: {total_websites}, Unreachable: {len(unreachable)}, Outage Percentage: {unreachable_percentage:.2f}%")
        print(f"[{current_time}] Approximate Bandwidth Usage: {bandwidth_usage:.2f} KB")

        # Wait for 1 minute
        time.sleep(60)

if __name__ == "__main__":
    main()
