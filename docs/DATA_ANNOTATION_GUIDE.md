# Data annotation guide

## Unit and workflow

Annotate the smallest complete evidence span in the original text. Two annotators work
independently; an adjudicator resolves disagreements without seeing model suggestions as
ground truth. Keep offsets in Unicode code points and preserve the source text. Do not
overlap labels unless using the separate SKILL and KNOWLEDGE heads required for SkillSpan's
nested examples.

Use the categories `SKILL`, `HARD_SKILL`, `SOFT_SKILL`, `KNOWLEDGE`, `TOOL`,
`PROGRAMMING_LANGUAGE`, `FRAMEWORK`, `DATABASE`, `CLOUD_PLATFORM`, `CERTIFICATION`,
`DEGREE`, `FIELD_OF_STUDY`, `OCCUPATION`, `EXPERIENCE_DURATION`, `SENIORITY`,
`RESPONSIBILITY`, and `ACHIEVEMENT`.

## Decisions and examples

| Text | Label | Rationale |
| --- | --- | --- |
| “built REST APIs” | `HARD_SKILL`: “built REST APIs” | Applied capability, not merely a keyword |
| “Python” | `PROGRAMMING_LANGUAGE` | Named language |
| “stakeholder negotiation” | `SOFT_SKILL` | Interpersonal capability with evidence |
| “thermodynamics” | `KNOWLEDGE` | Body of technical knowledge |
| “AWS” | `CLOUD_PLATFORM` | Named platform |
| “AWS Certified Solutions Architect” | `CERTIFICATION` | Credential, not a skill span |
| “led migration for a university capstone” | `RESPONSIBILITY`; not professional `SENIORITY` | Academic scope cannot establish management seniority |
| “improved latency by 35%” | `ACHIEVEMENT` | Measurable outcome |
| “excellent communicator” | no label without contextual evidence | Self-description is weak evidence |
| “interested in Kubernetes” | no demonstrated hard skill | Interest is not experience |

For aliases, annotate source text exactly, then map separately: `REST APIs` may map to
`RESTful API development`. If canonicalization confidence is below threshold or candidates
are ambiguous, keep the taxonomy ID null. Never force a mapping.

## Matching labels

Annotators label components before the final class: required-skill coverage,
preferred-skill coverage, relevant experience, seniority, occupation relevance,
education, certification, transferable evidence, and critical missing requirements.
Use `STRONG_MATCH`, `POTENTIAL_MATCH`, `WEAK_MATCH`, or `NOT_MATCH`; record evidence and
uncertainty. A mandatory legal licence that is absent requires manual review and cannot be
overridden by vocabulary similarity.

## Quality control

- Remove/mask PII before annotation and never use protected attributes as features.
- Assign related source documents, synthetic families, and duplicate clusters to one split.
- Never edit gold-test labels solely because a model disagrees.
- Measure Cohen's kappa for categorical labels and span-level exact/partial agreement for
  extraction.
- Review rare occupations, long spans, ambiguous soft skills, hard negatives, and
  high-impact disagreements first.

See `tools/annotation_app/README.md` for queue, agreement, and adjudication commands.
