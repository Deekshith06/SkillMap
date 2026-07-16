# Local annotation app

Create a queue, then run the API locally:

```bash
python scripts/create_annotation_queue.py \
  --input data/processed/unlabelled.jsonl \
  --output data/annotations/review_queue.jsonl \
  --count 500
python tools/annotation_app/app.py
```

Open `http://127.0.0.1:8765/docs`. Two annotators must submit separate files. Measure
agreement and merge only agreements plus independently adjudicated disagreements:

```bash
python scripts/measure_annotator_agreement.py data/annotations/annotations-a.jsonl data/annotations/annotations-b.jsonl
python scripts/merge_annotations.py data/annotations/annotations-a.jsonl data/annotations/annotations-b.jsonl data/annotations/gold_train.jsonl --adjudicated data/annotations/adjudicated.jsonl
```

The app deliberately binds only to loopback and has no authentication. Do not expose it
to a network or place private records in the repository.
