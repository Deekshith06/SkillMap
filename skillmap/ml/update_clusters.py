import json
import os
from pathlib import Path

# Data paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
POWER_SKILLS_PATH = DATA_DIR / "powerSkills.json"

def load_clusters():
    if not POWER_SKILLS_PATH.exists():
        return {}
    with open(POWER_SKILLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_clusters(clusters):
    with open(POWER_SKILLS_PATH, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=2)

def add_cluster(domain_name, subcategories):
    """
    Adds a new cluster to powerSkills.json after checking if it exists.
    
    Args:
        domain_name (str): The key for the domain (e.g., 'Civil_Engineering').
        subcategories (dict): A dictionary of subcategory keys and lists of skills.
    """
    clusters = load_clusters()
    
    if domain_name in clusters:
        print(f"Cluster '{domain_name}' already exists. Updating subcategories...")
        for sub, skills in subcategories.items():
            if sub in clusters[domain_name]:
                # Merge and unique
                existing_skills = set(clusters[domain_name][sub])
                new_skills = set(skills)
                clusters[domain_name][sub] = sorted(list(existing_skills.union(new_skills)))
            else:
                clusters[domain_name][sub] = sorted(skills)
    else:
        print(f"Adding new cluster: {domain_name}")
        clusters[domain_name] = {sub: sorted(skills) for sub, skills in subcategories.items()}
    
    save_clusters(clusters)
    print(f"Successfully updated '{domain_name}'.")

def expand_dataset():
    """Adds more clusters to broaden the model's scope."""
    
    # 1. Civil Engineering
    add_cluster("Civil_Engineering", {
        "Core": ["structural analysis", "geotechnical engineering", "surveying", "fluid mechanics", "transportation engineering"],
        "Design": ["autocad", "revit", "staad.pro", "civil 3d", "etabs", "sap2000", "bim"],
        "Construction": ["project estimation", "construction management", "site supervision", "safety management", "ms project"]
    })
    
    # 2. Chemical Engineering
    add_cluster("Chemical_Engineering", {
        "Core": ["thermodynamics", "mass transfer", "heat transfer", "fluid dynamics", "chemical kinetics"],
        "Simulation": ["aspen plus", "aspen hysys", "matlab", "comsol", "ansys fluent"],
        "Process": ["process control", "unit operations", "safety engineering", "hazop", "distillation"]
    })
    
    # 3. Legal / Law
    add_cluster("Legal", {
        "Core": ["legal research", "litigation", "contract law", "corporate law", "intellectual property", "compliance"],
        "Skills": ["legal writing", "case analysis", "mediation", "arbitration", "due diligence", "regulatory affairs"],
        "Tools": ["westlaw", "lexisnexis", "clio", "legalzoom"]
    })
    
    # 4. Logistics & Supply Chain
    add_cluster("Logistics_Supply_Chain", {
        "Core": ["supply chain management", "logistics", "procurement", "inventory management", "warehousing", "distribution"],
        "Operations": ["demand forecasting", "vendor management", "strategic sourcing", "six sigma", "lean", "erp"],
        "Tools": ["sap scm", "oracle scm", "tms", "wms"]
    })
    
    # 5. Sales & Business Development
    add_cluster("Sales", {
        "Core": ["sales strategy", "business development", "lead generation", "account management", "negotiation", "closings"],
        "Skills": ["relationship building", "prospecting", "cold calling", "sales forecasting", "market expansion"],
        "Tools": ["salesforce", "hubspot", "pipedrive", "zoho crm"]
    })

    # 6. Aerospace Engineering
    add_cluster("Aerospace_Engineering", {
        "Core": ["aerodynamics", "propulsion", "flight mechanics", "orbital mechanics", "avionics", "structural mechanics"],
        "Tools": ["ansys", "matlab", "stk", "catia", "solidworks"],
        "Degrees": ["b.tech aerospace", "be aerospace", "m.tech aerospace", "ms aerospace"]
    })

    # 7. Biomedical Engineering
    add_cluster("Biomedical_Engineering", {
        "Core": ["biomechanics", "biomaterials", "medical imaging", "biosensors", "tissue engineering", "rehabilitation engineering"],
        "Tools": ["matlab", "labview", "comsol", "mimics"],
        "Degrees": ["b.tech biomedical", "be biomedical", "m.tech biomedical", "ms biomedical"]
    })

    # 8. Industrial Engineering
    add_cluster("Industrial_Engineering", {
        "Core": ["operations research", "supply chain optimization", "quality control", "ergonomics", "production planning", "facilities design"],
        "Tools": ["arena", "flexsim", "minitab", "sap erp"],
        "Degrees": ["b.tech industrial", "be industrial", "m.tech industrial", "ms industrial"]
    })

    # Add degrees to existing clusters too
    add_cluster("Computer_Science_CSE", {
        "Degrees": ["b.tech cse", "be cse", "bca", "mca", "m.tech cse", "ms cs", "bs cs"]
    })
    add_cluster("Electronics_Communication_ECE", {
        "Degrees": ["b.tech ece", "be ece", "m.tech ece", "ms ece"]
    })
    add_cluster("Electrical_Engineering_EEE", {
        "Degrees": ["b.tech eee", "be eee", "m.tech eee", "ms eee"]
    })
    add_cluster("Mechanical_Engineering", {
        "Degrees": ["b.tech mechanical", "be mechanical", "m.tech mechanical", "ms mechanical"]
    })

if __name__ == "__main__":
    expand_dataset()
