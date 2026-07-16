# Privacy

## Data handled

SkillMap accepts PDF, DOCX, and UTF-8 TXT resumes and job descriptions. The application
extracts text to identify supported skills, experience evidence, and lexical similarity.

## Processing and retention

- Uploaded bytes are read with strict size limits and processed in memory.
- Uploaded files and extracted text are not written to application storage.
- Session state may retain extracted text in backend memory until it is cleared, expires,
  or the process restarts.
- Render's persistent disk is not used.
- Batch CSV exports contain filenames, result metadata, and skills, not resume bodies.

## Logging

Structured logs are restricted to request ID, operation, outcome, duration, parser type,
scoring mode, model version, file size, and safe error category. Resume text, job text,
document bytes, names, email addresses, and phone numbers must never be logged.

## Personal information

Common email addresses, phone numbers, URLs, labelled names/addresses, dates of birth,
government identifiers, and labelled protected attributes are masked before runtime
inference. Job-relevant employment dates are retained. The
runtime vocabulary does not score name, gender, photograph, age, nationality, address,
religion, marital status, or other unrelated personal characteristics. Automated redaction
is not perfect—especially for unlabelled names and free-form addresses—so users should
provide only documents they are authorized to process. Processed training data fails when
supported PII patterns remain; high-risk data still requires human privacy review.

Downloaded and private training data stay outside Git. External synthetic providers accept
only records explicitly marked synthetic; real resumes must never be sent to them.

## User controls

Users can cancel current analysis and clear uploaded session data from the interface.
Production operators should configure short session retention and avoid external request
body logging at reverse proxies.

## Incident handling

Operational errors include a request ID such as `SM-8F31C2`. Use that ID to correlate
metadata without asking a user to place resume content in an issue or log message.
