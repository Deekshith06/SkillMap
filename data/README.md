# Data layout

- `raw/`: immutable downloaded archives/extractions
- `interim/`: deduplicated and transformed working data
- `processed/`: canonical training/validation records
- `synthetic/`: generated augmentation, never real evaluation
- `annotations/`: local queues and annotator outputs
- `evaluation/`: challenge sets and local gold links
- `manifests/`: committed provenance, licence, version, and hash registry

Generated records and private data are ignored by Git. Only manifests, documentation, and
directory placeholders are committed.
