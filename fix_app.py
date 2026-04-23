import re

with open('backend/app.py', 'r') as f:
    content = f.read()

# 1. Replace fail-fast model loading with lazy loading
model_loading_old = """# ── Model loading (fail-fast) ────────────────────────────────────

REQUIRED_ARTIFACTS = [
    "bert_model_name.pkl",
    "kmeans_model.pkl",
    "cluster_names.pkl",
]


def _load_pickle(path: Path) -> Any:
    \"\"\"Load a pickle file. Logs duration.\"\"\"
    t0 = time.time()
    with path.open("rb") as f:
        obj = pickle.load(f)
    ms = round((time.time() - t0) * 1000, 1)
    logger.info("Loaded %s in %sms", path.name, ms)
    return obj


# Validate all artifacts exist
for _art in REQUIRED_ARTIFACTS:
    _art_path = MODEL_DIR / _art
    if not _art_path.exists():
        raise FileNotFoundError(
            f"Missing required model artifact: {_art_path}"
        )

if not CLUSTER_RESULTS_CSV.exists():
    raise FileNotFoundError(
        f"Missing cluster results: {CLUSTER_RESULTS_CSV}"
    )

import joblib

logger.info("Loading model artifacts from %s ...", MODEL_DIR)

bert_model_name: str = joblib.load(MODEL_DIR / "bert_model_name.pkl")
kmeans_model = joblib.load(MODEL_DIR / "kmeans_model.pkl")
cluster_name_source = joblib.load(MODEL_DIR / "cluster_names.pkl")

t0 = time.time()
sentence_model = SentenceTransformer(str(bert_model_name))
logger.info(
    "SentenceTransformer '%s' loaded in %sms",
    bert_model_name,
    round((time.time() - t0) * 1000, 1),
)"""

model_loading_new = """# ── Model loading (graceful + lazy) ──────────────────────────────

import joblib

def _load_pickle(path: Path) -> Any:
    t0 = time.time()
    with path.open("rb") as f:
        obj = pickle.load(f)
    ms = round((time.time() - t0) * 1000, 1)
    logger.info("Loaded %s in %sms", path.name, ms)
    return obj

bert_model_name: str | None = None
kmeans_model = None
cluster_name_source = None

try:
    bert_model_name = joblib.load(MODEL_DIR / "bert_model_name.pkl")
    kmeans_model = joblib.load(MODEL_DIR / "kmeans_model.pkl")
    cluster_name_source = joblib.load(MODEL_DIR / "cluster_names.pkl")
    logger.info("Loaded model artifacts from %s", MODEL_DIR)
except FileNotFoundError as e:
    logger.warning("Model artifacts not found: %s — ML endpoints will be unavailable", e)

_sentence_model = None

def get_sentence_model():
    global _sentence_model
    if _sentence_model is None and bert_model_name:
        t0 = time.time()
        _sentence_model = SentenceTransformer(str(bert_model_name))
        logger.info("SentenceTransformer '%s' loaded in %sms", bert_model_name, round((time.time() - t0) * 1000, 1))
    return _sentence_model"""

content = content.replace(model_loading_old, model_loading_new)


# 2. Make data loading graceful and clear memory
data_loading_old = """# ── Data loading ─────────────────────────────────────────────────

logger.info("Loading data files ...")

resume_df = pd.read_csv(RESUME_CSV, encoding="utf-8-sig", low_memory=False)
cluster_df = pd.read_csv(CLUSTER_RESULTS_CSV, encoding="utf-8-sig")

resume_df["ID"] = resume_df["ID"].astype(str)
cluster_df["ID"] = cluster_df["ID"].astype(str)
cluster_df["cluster"] = cluster_df["cluster"].astype("int16")
cluster_df["cluster_name"] = pd.Categorical(cluster_df["cluster_name"])

merged_df = resume_df.merge(cluster_df, on="ID", how="inner").copy()
merged_df["cluster"] = merged_df["cluster"].astype("int16")"""

data_loading_new = """# ── Data loading ─────────────────────────────────────────────────

merged_df = None

if RESUME_CSV.exists() and CLUSTER_RESULTS_CSV.exists():
    logger.info("Loading data files ...")
    try:
        resume_df = pd.read_csv(RESUME_CSV, encoding="utf-8-sig", low_memory=False)
        cluster_df = pd.read_csv(CLUSTER_RESULTS_CSV, encoding="utf-8-sig")

        resume_df["ID"] = resume_df["ID"].astype(str)
        cluster_df["ID"] = cluster_df["ID"].astype(str)
        cluster_df["cluster"] = cluster_df["cluster"].astype("int16")
        cluster_df["cluster_name"] = pd.Categorical(cluster_df["cluster_name"])

        merged_df = resume_df.merge(cluster_df, on="ID", how="inner").copy()
        merged_df["cluster"] = merged_df["cluster"].astype("int16")

        # Free raw dataframes to save memory
        del resume_df
        del cluster_df
    except Exception as e:
        logger.warning(f"Failed to load data: {e}")
else:
    logger.info("Resume.csv or cluster_results.csv not found — skipping data load")"""

content = content.replace(data_loading_old, data_loading_new)


# 3. Guard cluster computation
cluster_comp_old = """logger.info("Computing cluster metadata ...")

cluster_counts = (
    merged_df
    .groupby(["cluster", "cluster_name"], observed=True)
    .size()
    .reset_index(name="resume_count")
    .sort_values("cluster")
)"""

cluster_comp_new = """cluster_lookup: dict[int, dict[str, Any]] = {}
cluster_ids: list[int] = []
all_skills: Counter[str] = Counter()
cluster_skill_counter: dict[int, Counter[str]] = defaultdict(Counter)
cluster_sample_resumes: dict[int, list[dict[str, Any]]] = defaultdict(list)

if merged_df is not None:
    logger.info("Computing cluster metadata ...")

    cluster_counts = (
        merged_df
        .groupby(["cluster", "cluster_name"], observed=True)
        .size()
        .reset_index(name="resume_count")
        .sort_values("cluster")
    )"""

content = content.replace(cluster_comp_old, cluster_comp_new)

# 4. Indent the entire block after cluster computation
block_start = "cluster_skill_counter: dict[int, Counter[str]] = defaultdict(Counter)"
block_end = "logger.info(\n    \"Startup complete:"

# We will just replace specific parts
content = content.replace('for cid in merged_df["cluster"].unique():', 'if merged_df is not None:\n    for cid in merged_df["cluster"].unique():')

content = content.replace('for _, row in subset.head(12).iterrows():', '    for _, row in subset.head(12).iterrows():')
content = content.replace('text = str(row.get("Resume_str", ""))', '    text = str(row.get("Resume_str", ""))')
content = content.replace('skills = _legacy_skills(text)', '    skills = _legacy_skills(text)')
content = content.replace('cluster_skill_counter[int(cid)].update(skills)', '    cluster_skill_counter[int(cid)].update(skills)')
content = content.replace('cluster_sample_resumes[int(cid)].append({', '    cluster_sample_resumes[int(cid)].append({')
content = content.replace('"id": str(row.get("ID", "")),', '        "id": str(row.get("ID", "")),')
content = content.replace('"category": row.get("Category", ""),', '        "category": row.get("Category", ""),')
content = content.replace('"snippet": _WS_RE.sub(" ", text[:420]).strip(),', '        "snippet": _WS_RE.sub(" ", text[:420]).strip(),')
content = content.replace('"skills": skills[:10],', '        "skills": skills[:10],')
content = content.replace('})', '    })')
content = content.replace('for _, row in subset.iloc[12:].iterrows():', '    for _, row in subset.iloc[12:].iterrows():')
content = content.replace('skills = _legacy_skills(str(row.get("Resume_str", "")))', '    skills = _legacy_skills(str(row.get("Resume_str", "")))')

content = content.replace('for _, row in cluster_counts.iterrows():', 'if merged_df is not None:\n    for _, row in cluster_counts.iterrows():')
content = content.replace('cid = int(row["cluster"])', '    cid = int(row["cluster"])')
content = content.replace('name = _resolve_name(cid, str(row["cluster_name"]))', '    name = _resolve_name(cid, str(row["cluster_name"]))')
content = content.replace('top_skills = [s for s, _ in cluster_skill_counter[cid].most_common(8)]', '    top_skills = [s for s, _ in cluster_skill_counter[cid].most_common(8)]')
content = content.replace('cluster_lookup[cid] = {', '    cluster_lookup[cid] = {')
content = content.replace('"id": cid,', '        "id": cid,')
content = content.replace('"name": name,', '        "name": name,')
content = content.replace('"resume_count": int(row["resume_count"]),', '        "resume_count": int(row["resume_count"]),')
content = content.replace('"top_skills": top_skills,', '        "top_skills": top_skills,')
content = content.replace('"samples": cluster_sample_resumes.get(cid, []),', '        "samples": cluster_sample_resumes.get(cid, []),')

# Fix logger
log_old = """logger.info(
    "Startup complete: %d resumes, %d clusters, %d unique skills",
    len(merged_df), len(cluster_ids), len(all_skills),
)"""
log_new = """if merged_df is not None:
    logger.info(
        "Startup complete: %d resumes, %d clusters, %d unique skills",
        len(merged_df), len(cluster_ids), len(all_skills),
    )"""
content = content.replace(log_old, log_new)


# 5. Fix usages of sentence_model
content = content.replace('embedding = sentence_model.encode(', 'sentence_model = get_sentence_model()\n    if sentence_model:\n        embedding = sentence_model.encode(')
content = content.replace('embedding = sentence_model.encode(', 'embedding = sentence_model.encode(')

content = content.replace('sentence_model=sentence_model,', 'sentence_model=get_sentence_model(),')


with open('backend/app.py', 'w') as f:
    f.write(content)

print("Done")
