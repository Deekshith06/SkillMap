# Datasets and licences

The machine-readable source of truth is
[`data/manifests/dataset_registry.yaml`](../data/manifests/dataset_registry.yaml). A dataset
is usable only for the purposes whose approval flags are true. Local presence does not
imply approval.

## Selected sources

| Dataset | Verified version | Licence/reuse | Approved use |
| --- | --- | --- | --- |
| [SkillSpan](https://github.com/kris927b/SkillSpan) | commit `2ccf3de5b5af7a5409b8dd814fb1315dd6e0ae1b` | MIT; paper citation required | Training, validation, and testing with official boundaries |
| [ESCO](https://esco.ec.europa.eu/en/use-esco/download) | 1.2.1, current on 2026-07-17 | Commission Decision 2011/833/EU; EU-owned content CC BY 4.0 unless noted | Taxonomy reference and training features, not outcome labels |
| [O*NET Database](https://www.onetcenter.org/database.html) | 30.3, May 2026 | CC BY 4.0 with USDOL/ETA attribution and modification notice | Taxonomy/occupation reference and training features, not outcome labels |
| Local gold data | not created | Restricted; operator must establish legal basis | Validation/test only after PII audit, two annotations, adjudication, and immutable hashes |

SkillSpan contains expert span annotations for SKILL and KNOWLEDGE. It does not directly
provide a trustworthy hard-versus-soft label for every span. The two released sources are
de-identified; the official train/development/test boundaries must remain unchanged.

Use this O*NET attribution when information is published:

> This product includes information from the O*NET 30.3 Database by the U.S. Department
> of Labor, Employment and Training Administration, used under CC BY 4.0. O*NET® is a
> trademark of USDOL/ETA. SkillMap modifications have not been approved, endorsed, or
> tested by USDOL/ETA.

Use this ESCO acknowledgement:

> This service uses the ESCO classification of the European Commission.

## Rejected or restricted sources

`Resume.csv` is excluded from all new training and evaluation. Its original source,
licence, and label process are unknown. The audit measured 280 records, 18 exact duplicate
texts, 386 pairs at or above 0.8 character/word-shingle similarity in the deeper audit,
only seven distinct 40-character prefixes, and exactly 40 records in each top-level
category. Direct-identifier regexes found no email, URL, or phone, but that does not prove
de-identification. Its hash is
`c96d8b308453004586ed486d4ce4921cf4ad8842ba751758c9ca30aa5ed743e3`.

The ConFit IntelliPro and AliYun data are excluded because public dataset use and
redistribution terms were not established. SkillMap implements the paper's contrastive,
augmentation, symmetric retrieval, and hard-negative ideas without assuming access to its
private labels.

Unlicensed Kaggle/Hugging Face resume corpora, unredacted personal resumes, scraped job
posts without terms, and model-generated suitability scores are rejected by default.

## Local restricted data

Place authorized records under `data/private/`; this path is ignored by Git. Update the
registry with source, legal basis/licence, immutable hash, PII status, annotation method,
and record counts. Never commit private resumes, gold records, downloaded archives, or
provider credentials.
