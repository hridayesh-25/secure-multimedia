import csv
import matplotlib.pyplot as plt
from collections import defaultdict

# Store data per mode
data = defaultdict(lambda: {"size": [], "total": [], "overhead": []})

with open("results/hybrid_results.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        mode = row["Mode"]
        size_mb = int(row["File Size (bytes)"]) / (1024 * 1024)
        total_time = float(row["Total Time"])
        overhead = float(row["Overhead (%)"])

        data[mode]["size"].append(size_mb)
        data[mode]["total"].append(total_time)
        data[mode]["overhead"].append(overhead)


# -------------------------------
# Graph 1: File Size vs Total Time
# -------------------------------
plt.figure()

for mode in data:
    plt.plot(data[mode]["size"], data[mode]["total"], label=mode)

plt.xlabel("File Size (MB)")
plt.ylabel("Total Processing Time (s)")
plt.title("File Size vs Total Processing Time (Mode Comparison)")
plt.legend()
plt.grid(True)
plt.show()


# -------------------------------
# Graph 2: File Size vs Overhead %
# -------------------------------
plt.figure()

for mode in data:
    plt.plot(data[mode]["size"], data[mode]["overhead"], label=mode)

plt.xlabel("File Size (MB)")
plt.ylabel("Security Overhead (%)")
plt.title("File Size vs Security Overhead (Mode Comparison)")
plt.legend()
plt.grid(True)
plt.show()
