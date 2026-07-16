# Fairness and robustness report

Status: **not production-ready**.

Automated counterfactual tests verify that changing supported labelled names and email
addresses does not change a deterministic match score, and that an academic “team lead”
phrase does not imply professional management seniority. PII masking, no-PII logging,
keyword-stuffing/hard-negative mechanics, empty evidence abstention, score bounds, and
deterministic inference are also covered by tests.

No authorized real dataset with demographic outcomes was available. Therefore disparate
performance, equalized error rates, intersectional slices, non-traditional education,
career gaps/changes, document formats, OCR noise, and multilingual robustness are not
measured. Protected attributes are excluded from features, but exclusion alone does not
prove fairness because proxies and historical labels may still encode bias.

The smoke candidate is not promoted. Before any organizational use, run the real gold
slices in `docs/EVALUATION.md`, review false positives/negatives with affected stakeholders,
document legal review and human appeal, and preserve SkillMap as decision support rather
than an automatic rejection system.
