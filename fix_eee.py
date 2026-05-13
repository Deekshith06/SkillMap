import json

path = "skillmap/ml/data/powerSkills.json"
with open(path, "r") as f:
    data = json.load(f)

# Update EEE
data["Electrical_Engineering_EEE"] = {
    "Core": [
      "power systems",
      "control systems",
      "electrical machines",
      "network analysis",
      "electromagnetics",
      "electrical engineering",
      "circuit design",
      "circuit analysis"
    ],
    "Power_Electronics": [
      "power electronics",
      "inverters",
      "converters",
      "motor drives",
      "smart grid",
      "renewable energy"
    ],
    "Automation": [
      "plc",
      "scada",
      "industrial automation",
      "instrumentation",
      "embedded systems",
      "iot"
    ],
    "Tools": [
      "matlab",
      "autocad electrical",
      "autocad",
      "python",
      "c programming"
    ],
    "Degrees": [
      "b.tech eee",
      "be eee",
      "m.tech eee",
      "ms eee",
      "b.tech in eee"
    ]
}

# Also ensure "c programming" is handled (it's often just extracted as "c" or "c programming")
data["Computer_Science_CSE"]["Core"].append("c programming")

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print("Updated powerSkills.json for EEE.")
