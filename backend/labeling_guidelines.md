Labeling Guidelines — Law Detection Project

Purpose
- Provide concise, consistent instructions for human labelers to produce high-quality labels for training a multiclass classifier.

High-level labels (use `category`):
- Criminal — incidents involving theft, assault, murder, sexual offences, cheating/fraud, etc.
- Civil — defamation, contract disputes, torts (non-criminal injuries/losses).
- Administrative — regulatory or licensing matters.
- Uncategorized — ambiguous or insufficient facts; request follow-up.

Laws field (`laws`)
- Provide an array of objects: {"code":"IPC XXX","desc":"Short title"}.
- If multiple plausible sections exist, include the top 2–4 most relevant.
- Prefer canonical section codes where possible (e.g., `IPC 302` for murder).

Defenses (`defenses`)
- Short strings: common defenses to consider (e.g., "Self-defence", "Alibi", "Insufficient evidence").
- Include at least two when obvious; otherwise one or empty list.

Reasons (`reasons`)
- Map each law code included to a 1–2 sentence reason explaining why it applies to the case text.
- Keep concise and factual: cite the key trigger in the case text (e.g., "death occurred after assault; check intent").

FollowUps (`followUps`)
- 1–6 short, specific yes/no or short-answer questions the system should ask to disambiguate (e.g., "Was a weapon used (yes/no)?").

Labeling rules & quality
- Always base labels on explicit facts in the `caseText`. Don't infer unstated motivations unless naturally implied.
- If ambiguous, mark `category` as `Uncategorized` and add a `reasons` note specifying what additional facts are required.
- Use neutral language; avoid legal conclusions beyond mapping to likely sections.
- Keep JSON clean and valid; arrays and objects must be well-formed.

Examples
- Case: "Someone stole my gold while I was away."
  - category: Criminal
  - laws: [{"code":"IPC 378","desc":"Theft"}]
  - defenses: ["Mistaken identity","Alibi"]
  - reasons: {"IPC 378":"Property taken without consent (theft)."}
  - followUps: ["Was there forced entry (yes/no)?","Approximate value (low/medium/high)?"]

- Case: "He hit and pushed another person; the victim later died."
  - category: Criminal
  - laws: [{"code":"IPC 302","desc":"Murder"}]
  - defenses: ["Self-defence","Provocation"]
  - reasons: {"IPC 302":"Death occurred after assault; check intent."}
  - followUps: ["Was there intent to cause death (yes/no)?"]

Workflow notes
- Use `backend/collect_dataset.py --interactive` for manual entry or append to `backend/dataset_template.csv` and convert.
- Use `backend/auto_label.py` to generate LLM proposals (requires `OPENAI_API_KEY`) and `backend/review_labels.py` to accept/edit proposals.
- After collecting reviewed labels, run `backend/retrain_classifier.py` to retrain the model.

Acceptance criteria for training data
- Each example must have a non-empty `caseText` and a `category` plus at least one `laws` item.
- Aim for 200–500 examples per major category before expecting a reliable classifier.

Privacy & safety
- Do not include real personal identifiers in training data (replace with placeholders) unless you have legal consent to store them.

Contact
- For questions about ambiguous labels or new label types, open an issue in the repo or contact the project owner.
