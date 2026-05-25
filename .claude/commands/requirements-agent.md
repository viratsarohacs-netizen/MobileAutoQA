# Requirements Agent

**Role:** Reads a Jira ID and extracts mobile-app requirements into a structured spec.

This is **Agent 1 of 5** in the MobileAutoQA pipeline:
> **Requirements Agent** → Test Generation Agent → Execution Agent → Self-Healing Agent → Reporting Agent

---

## Usage

```
/requirements-agent PHIX-97533
/requirements-agent PHIX-97533 --paste     ← paste description manually if no Jira access
```

---

## Step 1 — Fetch the Jira Ticket

```bash
curl -s -u "$JIRA_USERNAME:$JIRA_PASSWORD" \
  "https://jira.uzio.com/rest/api/2/issue/PHIX-XXXXX?expand=renderedFields" \
  | python -m json.tool
```

Extract:
- **Summary** — feature/bug title
- **Description** — full requirement text
- **Acceptance Criteria** — explicit pass conditions (in description or comments)
- **Issue type** — Bug / Story / Sub-task (affects test depth)
- **Components / Labels** — Mobile, Time Tracking, Time Off, I-9, E-Verify, etc.
- **Linked issues** — parent story, related defects
- **Attachments** — screenshots/designs (describe what they show)
- **Comments** — QA/dev notes that clarify expected behavior

If Jira credentials aren't available, ask the user to paste the ticket text.

---

## Step 2 — Filter for Mobile Relevance

The UZIO platform is web + mobile. Determine if/how this ticket touches mobile:
- Does the Summary/Description mention "Mobile", "app", a mobile screen, or a mobile flow?
- Which app screens are affected? Map to known screens:
  - **Login** (`src/screens/Login/Login.tsx`)
  - **Time Tracking** (`timesheetScreens/timesheetMainScreen.tsx`) — Clock In/Out, Break, attestation
  - **Time Off** (`TimeOffSceens/TimeOffHome.tsx`)
  - **Benefits**, **Schedule**, **Inbox** (bottom nav)
  - **Drawer** (hamburger menu — logout, switch company, documents)
- If the ticket is **web-only**, say so and stop: "PHIX-XXXXX appears web-only. No mobile requirements extracted."

---

## Step 3 — Extract Structured Requirements

Write `tests/jira/{JIRA-ID}/requirements.md`:

```markdown
# {JIRA-ID} — Requirements
# Source: Jira (fetched {date})
# Type: Bug | Story | Sub-task
# Mobile screens: {comma-separated}

## Summary
{one-paragraph plain-English summary of what the ticket requires}

## Functional Requirements
- FR-1: {requirement} — screen: {screen}
- FR-2: ...

## UI Elements Affected
- {new/changed button, label, modal, validation message} — exact text if known

## Acceptance Criteria
- AC-1: {testable condition}
- AC-2: ...

## Edge Cases & Conditional Behavior
- EC-1: {condition} → {expected behavior}
- (e.g. "attestation popup appears only when clock-out returns HTTP 428")

## Platform Notes
- Android-specific: {if any}
- iOS-specific: {if any}

## Out of Scope
- {anything explicitly not part of this ticket}
```

---

## Step 4 — Reconcile With the App (optional but recommended)

Cross-check requirement text against the real app strings in
`core/locators.py` and the UzioMobile repo (`C:\code\master\UzioMobile`):
- If the ticket references a button/label, find its real i18n string in
  `src/i18n/locales/en.json` and note it (the app has no testIDs — text is the locator).
- If a new UI element is introduced, flag that `core/locators.py` will need a new constant.

---

## Step 5 — Handoff

Print:

```
✅ Requirements extracted — {JIRA-ID}

Type        : {Bug|Story}
Mobile screens: {list}
Functional reqs: {N}
Acceptance criteria: {N}
Edge cases  : {N}
New locators needed: {list or "none"}

File: tests/jira/{JIRA-ID}/requirements.md

Next: /test-generation-agent {JIRA-ID}
```

---

## Notes
- This agent does NOT write test cases — that's the Test Generation Agent's job.
- Keep requirements implementation-agnostic (what, not how).
- Always cite the acceptance criteria verbatim where possible (they become assertions).
