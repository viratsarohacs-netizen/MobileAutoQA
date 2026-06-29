# PHIX-98287 — Mobile Test Spec
# Defect: UzioLeftBorderedRowItem right-side card clipped past device width
# Affected screens: Shift Requests (Offer + Swap), Swap Shift (Available Shifts),
#                   Open Shifts, My Shifts, Time Tracking Home (Upcoming Schedule),
#                   Holiday Calendar, Completed Time Off Requests
# Fix commit (UzioMobile master): fe5dc313
# Role: EE — mobile1@t.com (or any EE with at least one schedulable shift)
# Run context: noReset session, local device OR BrowserStack;
#              works on iOS + Android — overflow is asserted on whichever the
#              run uses, since the defect reproduced on BOTH per the ticket.

> **Core assertion shared by every card-overflow test:**
> Locate a known text element on the right-side card; read its bounding rect
> via Appium; assert `rect.x + rect.width <= window_width + tolerance`
> (where tolerance = 4% of width to absorb row right-padding + sub-pixel
> rounding). This is the codified form of the developer's verification:
> *"Tested on android and ios simulators. Nothing is clipped and the tile
> is covering the width of the screen for both devices."*

---

## SETUP (run once per class)

```
launch app
dismiss permissions if present
dismiss onboarding if present
if not on dashboard:
    login as employee   # config.credential('employee_username'/'employee_password')
dismiss App Lock        # tap "I'll do it later"
verify any of: "Time Tracking" | "Benefits" | "Time Off" is visible
```

---

## TEST CASES

### TC-01 — Schedule → Shift Requests opens (sanity, P2)
```
SETUP
TEST
    tap tab "Schedule"
    wait for "Shift Requests"
    tap "Shift Requests"
    verify "Shift Requests" is visible        # heading
    verify any of: "Offer" | "Swap" is visible   # tab bar rendered
TEARDOWN
    press back
```

### TC-02 — Offer tab renders Incoming Requests / Your Requests section (sanity, P2)
```
SETUP + TC-01
TEST
    tap "Offer"
    verify any of: "Incoming Requests" | "Your Requests" | "No Requests" is visible
TEARDOWN
    press back
```

### TC-03 — Swap tab renders without crash (sanity, P2)
```
SETUP + TC-01
TEST
    tap "Swap"
    verify any of: "Incoming Requests" | "Your Requests" | "No Requests" is visible
TEARDOWN
    press back
```

### TC-04 — Offer Incoming card: shift time-range text fits inside screen (FIX, P1)
```
SETUP + TC-02
TEST
    # If there is no incoming Offer request, SKIP (no data).
    if not text contains "Incoming Requests":
        skip "No Incoming Offer requests for this EE — set up data and rerun"
    find first time-range text in the Incoming section (matches "AM" or "PM" or ":")
    assert element rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-05 — Offer Incoming card: "Accept" button fully visible (FIX, P1)
```
SETUP + TC-02
TEST
    if not text "Accept" is visible:
        skip "No Incoming Offer requests with Accept action"
    assert element('Accept') rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-06 — Offer Incoming card: "Reject" button fully visible (FIX, P1)
```
SETUP + TC-02
TEST
    if not text "Reject" is visible:
        skip "No Incoming Offer requests with Reject action"
    assert element('Reject') rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-07 — Swap tab card: shift time-range text fits inside screen (FIX, P1)
```
SETUP + TC-03
TEST
    if not text contains "Incoming Requests":
        skip "No Incoming Swap requests for this EE"
    find first time-range text in Incoming section
    assert element rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-08 — Schedule → Swap Shift opens (sanity, P2)
```
SETUP
TEST
    tap tab "Schedule"
    if not text "Swap Shift" is visible:
        skip "Swap Shift tile not present (no swap-eligible shifts)"
    tap "Swap Shift"
    verify any of: "Swap Shift" | "Available Shifts" | "No Shifts Available." is visible
TEARDOWN
    press back
```

### TC-09 — Available Shifts cards fit inside screen (FIX, P1)
```
SETUP + TC-08
TEST
    if text "No Shifts Available." is visible:
        # EC-5 — empty state path
        verify "No Shifts Available." is visible
        skip "Available Shifts list is empty — overflow is non-applicable"
    find each row's time-range / job text (UzioText size hp('1.85%') or hp('1.2%'))
    for each found card text: assert rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-10 — Open Shifts rows fit inside screen (regression, P2)
```
SETUP
TEST
    tap tab "Schedule"
    if not text "Open Shifts" is visible:
        skip "Open Shifts not present for this employer"
    tap "Open Shifts"
    if text "No Shift" is visible OR rows-not-found:
        skip "No Open Shifts data"
    find first row's time-range or status text
    assert rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-11 — My Shifts rows fit inside screen (regression, P2)
```
SETUP
TEST
    tap tab "Schedule"
    if not text "My Shifts" is visible:
        skip
    tap "My Shifts"
    if text "No Shift" is visible:
        skip "EE has no scheduled shifts"
    assert first card right-edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-12 — Time Tracking Home "My Upcoming Schedule" tile rows fit inside screen (regression, P2)
```
SETUP
TEST
    tap tab "Time Tracking"
    scroll to "My Upcoming Schedule"
    if "My Upcoming Schedule" is not visible:
        skip "Upcoming schedule tile not enabled for this EE"
    find first upcoming-schedule row's date/time text
    assert rect.right_edge <= window.width + tolerance
TEARDOWN
```

### TC-13 — Holiday Calendar rows fit inside screen (regression, P3)
```
SETUP
TEST
    open drawer
    scroll to "Holiday Calendar"
    if not visible:
        skip "Holiday Calendar not in this EE's drawer"
    tap "Holiday Calendar"
    if no holiday rows render within 5s:
        skip "No holidays in calendar — overflow N/A"
    find first holiday name on a card
    assert rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

### TC-14 — Completed Time Off rows fit inside screen (regression, P3)
```
SETUP
TEST
    tap tab "Time Off"
    if not text "Completed" is visible:
        skip "Time Off Completed accordion not present"
    tap "Completed"
    if no completed-request rows render within 5s:
        skip "EE has no completed time-off requests"
    find first completed-request's type/date text
    assert rect.right_edge <= window.width + tolerance
TEARDOWN
```

### TC-15 — "No Shifts Available." empty state renders without overflow (edge, P3)
```
SETUP
TEST
    tap tab "Schedule"
    tap "Swap Shift"
    if not text "No Shifts Available." is visible:
        skip "EE has available shifts — empty-state path not exercised this run"
    # The empty-state message itself is centered text, not a row component, but
    # it must still fit within the screen width.
    assert element('No Shifts Available.') rect.right_edge <= window.width + tolerance
TEARDOWN
    press back
```

---

## NOTES — Why this suite is tight rather than 20+ cases

Per agent guidance M3 (every screen + modal touched = its own case): there are
**eight** screens that consume `UzioLeftBorderedRowItem`, and each is covered.
The fix has no new modals, no new copy, no role split — so a sprawling matrix
adds noise. Modal / role / cross-account E2E cases (M5, M6, M11) don't apply
to a layout-only defect. This matches the precedent set by PHIX-98315's
defect-focused suite (5 cases for a single-fix defect).

## NOTES — Data assumptions

- The EE under test must have, ideally, at least one Incoming Shift Request
  (Offer or Swap) on the Shift Requests screen AND at least one Available
  Shift on the Swap Shift screen. Cases skip cleanly if the data isn't there
  (it is a regression suite, not a setup suite).
- Run order matters only for shared fixtures (login + dashboard). Individual
  cases are independent and back out after themselves.

## OUT OF SCOPE

- Accept / Reject business logic (this ticket only asserts visibility).
- Web (Phix) shift screens.
- Performance / scroll behaviour.
- Backend / API changes — none in this fix.
