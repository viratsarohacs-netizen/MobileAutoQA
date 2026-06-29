# Requirements Agent

**Role:** Reads a Jira ID and extracts mobile-app requirements into a structured spec.

This is **Agent 1 of 5** in the MobileAutoQA pipeline:
> **Requirements Agent** → Test Generation Agent → Execution Agent → Self-Healing Agent → Reporting Agent

---

## Usage

```
/mobile-requirements-agent PHIX-97533
/mobile-requirements-agent PHIX-97533 --paste     ← paste description manually if no Jira access
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

## Step 4 — Reconcile With the App Code (RECOMMENDED — the code is authoritative)

The ticket says WHAT; the UzioMobile RN code says the exact text and screens. Read it.

**4a — find the developer's mobile commits for this ticket** (reveals the exact RN
screens changed — more reliable than the ticket prose):
```bash
git -C "C:/code/master/UzioMobile" log --all --oneline -i --grep="PHIX-XXXXX"
git -C "C:/code/master/UzioMobile" show <SHA> --stat --no-patch   # changed screens
```
If no commits: fall back to searching `src/screens/` by feature keyword.

**4b — resolve real UI text** against `core/locators.py` and the UzioMobile repo:
- For any button/label/heading the ticket references, find its `t('key')` and resolve
  the English value in `src/i18n/locales/en.json` (the app has no testIDs — text IS
  the locator). Record the exact string.
- Note feature-flag gates (`PERM_FEATURE_*`, `isEmployeeManager`) → which role/employer
  the requirement applies to.
- If a NEW UI element is introduced, flag that `core/locators.py` needs a new constant.

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

Next: /mobile-test-generation-agent {JIRA-ID}
```

---

## Notes
- This agent does NOT write test cases — that's the Test Generation Agent's job.
- Keep requirements implementation-agnostic (what, not how).
- Always cite the acceptance criteria verbatim where possible (they become assertions).
