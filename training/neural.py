"""Optional heavy teacher lanes; imported only by offline non-smoke runs."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from training.modeling import ranking_metrics


def _revision(config: dict[str, Any], model_name: str) -> str:
    revision = config.get("model_revisions", {}).get(model_name)
    if not revision:
        raise ValueError(f"Pin an immutable Hugging Face revision for {model_name!r}")
    return str(revision)


def _bio_entities(labels: list[int]) -> set[tuple[int, int]]:
    entities = set()
    start = None
    for index, label in enumerate([*labels, 0]):
        if label == 1 or (label == 2 and start is None):
            if start is not None:
                entities.add((start, index))
            start = index
        elif label == 0 and start is not None:
            entities.add((start, index))
            start = None
    return entities


def train_token_classifier(
    model_name: str,
    rows: list[dict[str, Any]],
    output_dir: Path,
    config: dict[str, Any],
) -> dict[str, float]:
    """Train separate SKILL and KNOWLEDGE BIO heads so nested spans remain representable."""

    import numpy as np
    import torch
    from transformers import (
        AutoModelForTokenClassification,
        AutoTokenizer,
        EarlyStoppingCallback,
        Trainer,
        TrainingArguments,
    )

    training = config.get("training", {})
    revision = _revision(config, model_name)
    tokenizer = AutoTokenizer.from_pretrained(  # nosec B615
        model_name, revision=revision, use_fast=True
    )

    class SpanDataset(torch.utils.data.Dataset):
        def __init__(self, source: list[dict[str, Any]], entity_key: str) -> None:
            self.items = []
            for row in source:
                encoded = tokenizer(
                    row["text"],
                    truncation=True,
                    max_length=int(training.get("max_length", 512)),
                    stride=int(training.get("stride", 128)),
                    return_offsets_mapping=True,
                    return_overflowing_tokens=True,
                )
                spans = [(item["start"], item["end"]) for item in row.get(entity_key, [])]
                for index, offsets in enumerate(encoded["offset_mapping"]):
                    labels = []
                    active_span = None
                    for start, end in offsets:
                        if start == end:
                            labels.append(-100)
                            continue
                        match = next(
                            (span for span in spans if start < span[1] and end > span[0]), None
                        )
                        if match is None:
                            labels.append(0)
                            active_span = None
                        else:
                            labels.append(1 if match != active_span else 2)
                            active_span = match
                    self.items.append(
                        {
                            "input_ids": encoded["input_ids"][index],
                            "attention_mask": encoded["attention_mask"][index],
                            "labels": labels,
                        }
                    )

        def __len__(self) -> int:
            return len(self.items)

        def __getitem__(self, index: int) -> dict[str, Any]:
            return self.items[index]

    split_rows = {
        split: [row for row in rows if row.get("official_split") == split]
        for split in ("train", "validation", "test")
    }
    task_scores = {}
    for entity_key in ("skills", "knowledge"):
        task_dir = output_dir / entity_key
        model = AutoModelForTokenClassification.from_pretrained(  # nosec B615
            model_name,
            revision=revision,
            num_labels=3,
            id2label={0: "O", 1: "B", 2: "I"},
            label2id={"O": 0, "B": 1, "I": 2},
        )

        def compute_metrics(evaluation: Any) -> dict[str, float]:
            predictions = np.argmax(evaluation.predictions, axis=-1)
            tp = fp = fn = 0
            for predicted, expected in zip(predictions, evaluation.label_ids, strict=True):
                usable = expected != -100
                gold_entities = _bio_entities(expected[usable].tolist())
                predicted_entities = _bio_entities(predicted[usable].tolist())
                tp += len(gold_entities & predicted_entities)
                fp += len(predicted_entities - gold_entities)
                fn += len(gold_entities - predicted_entities)
            precision = tp / (tp + fp) if tp + fp else 0.0
            recall = tp / (tp + fn) if tp + fn else 0.0
            return {
                "entity_precision": precision,
                "entity_recall": recall,
                "entity_f1": 2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0,
            }

        arguments = TrainingArguments(
            output_dir=str(task_dir),
            learning_rate=float(training.get("learning_rate", 2e-5)),
            per_device_train_batch_size=int(training.get("batch_size", 8)),
            per_device_eval_batch_size=int(training.get("batch_size", 8)),
            num_train_epochs=float(training.get("epochs", 5)),
            weight_decay=float(training.get("weight_decay", 0.01)),
            warmup_ratio=float(training.get("warmup_ratio", 0.1)),
            max_grad_norm=1.0,
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="entity_f1",
            greater_is_better=True,
            save_total_limit=2,
            seed=int(config.get("seed", 42)),
            fp16=bool(training.get("mixed_precision")) and torch.cuda.is_available(),
            report_to=[],
        )
        trainer = Trainer(
            model=model,
            args=arguments,
            train_dataset=SpanDataset(split_rows["train"], entity_key),
            eval_dataset=SpanDataset(split_rows["validation"], entity_key),
            processing_class=tokenizer,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        )
        trainer.train(resume_from_checkpoint=bool(config.get("resume")))
        metrics = trainer.evaluate(
            SpanDataset(split_rows["test"], entity_key), metric_key_prefix="test"
        )
        trainer.save_model(str(task_dir / "best"))
        tokenizer.save_pretrained(str(task_dir / "best"))
        task_scores[entity_key] = float(metrics.get("test_entity_f1", 0.0))
    task_scores["mean_entity_f1"] = sum(task_scores.values()) / len(task_scores)
    return task_scores


def train_biencoder(
    model_name: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    output_dir: Path,
    config: dict[str, Any],
) -> dict[str, float]:
    """Train symmetric resume/job triplets with taxonomy-derived hard negatives."""

    from sentence_transformers import InputExample, SentenceTransformer, losses
    from torch.utils.data import DataLoader

    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in train_rows:
        grouped[row["group_id"]]["negative" if row.get("hard_negative") else "positive"] = row
    examples = []
    groups = [value for value in grouped.values() if "positive" in value and "negative" in value]
    for index, value in enumerate(groups):
        positive, negative = value["positive"], value["negative"]
        examples.append(
            InputExample(
                texts=[positive["resume_text"], positive["job_text"], negative["job_text"]]
            )
        )
        other_resume = groups[(index + 1) % len(groups)]["positive"]["resume_text"]
        examples.append(
            InputExample(texts=[positive["job_text"], positive["resume_text"], other_resume])
        )
    model = SentenceTransformer(model_name, revision=_revision(config, model_name))
    loader = DataLoader(
        examples, shuffle=True, batch_size=int(config.get("training", {}).get("batch_size", 8))
    )
    model.fit(
        train_objectives=[(loader, losses.TripletLoss(model=model))],
        epochs=int(config.get("training", {}).get("epochs", 3)),
        warmup_steps=max(1, math.ceil(len(loader) * 0.1)),
        output_path=str(output_dir),
        checkpoint_path=str(output_dir / "checkpoints"),
        checkpoint_save_steps=max(1, len(loader)),
        show_progress_bar=True,
    )
    resume_embeddings = model.encode(
        [row["resume_text"] for row in test_rows], normalize_embeddings=True, convert_to_numpy=True
    )
    job_embeddings = model.encode(
        [row["job_text"] for row in test_rows], normalize_embeddings=True, convert_to_numpy=True
    )
    scores = [
        float((resume_embeddings[index] * job_embeddings[index]).sum())
        for index in range(len(test_rows))
    ]
    return ranking_metrics(test_rows, scores)


def train_cross_encoder_teacher(
    model_name: str,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    output_dir: Path,
    config: dict[str, Any],
) -> tuple[list[float], list[float]]:
    """Train an offline pair-scoring teacher and return train/test soft labels."""

    from sentence_transformers import CrossEncoder, InputExample
    from torch.utils.data import DataLoader

    examples = [
        InputExample(
            texts=[row["resume_text"], row["job_text"]],
            label=float(row["final_score"]) / 100,
        )
        for row in train_rows
    ]
    model = CrossEncoder(
        model_name,
        num_labels=1,
        max_length=int(config.get("training", {}).get("max_length", 512)),
        automodel_args={"revision": _revision(config, model_name)},
        tokenizer_args={"revision": _revision(config, model_name)},
    )
    loader = DataLoader(
        examples,
        shuffle=True,
        batch_size=int(config.get("training", {}).get("batch_size", 8)),
    )
    model.fit(
        train_dataloader=loader,
        epochs=int(config.get("training", {}).get("epochs", 3)),
        warmup_steps=max(1, math.ceil(len(loader) * 0.1)),
        output_path=str(output_dir),
        save_best_model=True,
        show_progress_bar=True,
    )
    train_scores = list(
        map(
            float,
            model.predict([(row["resume_text"], row["job_text"]) for row in train_rows]),
        )
    )
    test_scores = list(
        map(
            float,
            model.predict([(row["resume_text"], row["job_text"]) for row in test_rows]),
        )
    )
    return train_scores, test_scores
