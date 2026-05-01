from pydantic import BaseModel, Field, validator
from typing import Literal, List, Optional
from datetime import datetime
import pandas as pd

class ResumeDatasetSchema(BaseModel):
    resume_id: str
    raw_text: str
    domain: Literal["engineering_cse", "engineering_eee", "engineering_ece", "engineering_mech", 
                    "management", "medical", "finance", "design"]
    sub_domain: str
    experience_years: float
    experience_level: Literal["entry", "mid", "senior", "lead", "executive"]
    extracted_skills: List[str]
    skill_labels: dict[str, float]
    ats_score_ground_truth: Optional[float]
    sections_present: List[str]
    cluster_id: Optional[int]
    cluster_label: Optional[str]
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

def check_minimum_counts(df: pd.DataFrame) -> None:
    if "domain" not in df.columns or "sub_domain" not in df.columns:
        raise ValueError("DataFrame missing required columns: domain, sub_domain")
        
    counts = df.groupby(["domain", "sub_domain"]).size()
    failed = counts[counts < 500]
    
    if not failed.empty:
        raise ValueError(f"Data validation failed. The following sub-domains have < 500 records:\n{failed}")
    print("Dataset validation passed! All domains have minimum 500 resumes.")
