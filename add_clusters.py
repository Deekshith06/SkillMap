import json

path = "skillmap/ml/data/powerSkills.json"
with open(path, "r") as f:
    data = json.load(f)

data["Product_Experience_Design"] = {
    "Design": ["figma", "sketch", "invision", "adobe xd", "wireframing"],
    "UX": ["user research", "a/b testing", "hci", "interaction design"],
    "Product": ["product management", "sprint planning", "user stories", "roadmap"]
}

data["Cloud_DevOps_Infrastructure"] = {
    "Cloud": ["aws", "azure", "gcp", "cloud architecture", "serverless"],
    "DevOps": ["docker", "kubernetes", "terraform", "jenkins", "ci/cd", "ansible"],
    "SRE": ["site reliability", "monitoring", "datadog", "prometheus", "grafana"]
}

data["Cybersecurity_GRC"] = {
    "Offensive": ["penetration testing", "ethical hacking", "metasploit", "red team"],
    "Defensive": ["soc", "incident response", "firewalls", "siem", "blue team"],
    "Compliance": ["iso 27001", "soc2", "gdpr", "hipaa", "risk assessment", "grc"]
}

data["Data_Science_MLOps"] = {
    "AI": ["deep learning", "neural networks", "transformers", "llms", "huggingface"],
    "Data": ["data engineering", "etl", "spark", "hadoop", "snowflake"],
    "MLOps": ["mlflow", "kubeflow", "model deployment", "model registry", "sagemaker"]
}

data["Revenue_Operations_RevOps"] = {
    "Marketing": ["performance marketing", "seo", "sem", "growth hacking"],
    "Sales_Tech": ["salesforce", "hubspot", "crm administration", "outreach"],
    "Analytics": ["cac", "ltv", "funnel optimization", "revenue forecasting"]
}

data["Supply_Chain_Logistics_Tech"] = {
    "Systems": ["sap erp", "oracle scm", "wms", "tms", "netsuite"],
    "Analytics": ["inventory forecasting", "demand planning", "vendor management"],
    "Operations": ["warehouse automation", "procurement", "six sigma", "lean"]
}

data["Human_Capital_People_Analytics"] = {
    "Acquisition": ["talent acquisition", "sourcing", "greenhouse", "lever", "workday"],
    "Analytics": ["retention metrics", "dei metrics", "headcount planning", "hris"],
    "Culture": ["employee engagement", "organizational design", "change management"]
}

data["Executive_Leadership_Strategy"] = {
    "Management": ["p&l management", "cross-functional leadership", "board reporting"],
    "Strategy": ["m&a integration", "business strategy", "corporate development", "scaling"],
    "Operations": ["change management", "okrs", "kpi development", "vendor negotiation"]
}

with open(path, "w") as f:
    json.dump(data, f, indent=2)

print("Added 8 new clusters.")
