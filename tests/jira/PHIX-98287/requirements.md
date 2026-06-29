# PHIX-98287 — Requirements
# Source: Jira (fetched 2026-06-26)
# Type: Defect (Minor) — Status: Ready for QA, Resolution: Fixed
# Fix Versions: neuron-13.0, neuron-12.4.11
# Sprint: neuron-13.0 Sprint 10
# Mobile screens: Shift Requests (Offer tab, Swap tab), Swap Shift (Available Shifts), Open Shifts, My Shifts, Time Tracking Home (upcoming schedule), Request Time Off Confirm, Holiday Calendar, Completed Time Off Requests
# Fix commits (UzioMobile): fe5dc313 (master), 1288c44a (PHIX_12.4.4.3 — reverted by 1960736b)

## Summary
On the NRS Purple mobile build, every screen that uses the shared
`UzioLeftBorderedRowItem` component with a non-trivial `rightItemRenderer` showed
the right-side card visually clipped at the right edge of the device — roughly
half the card ran off-screen. The date column on the left rendered at a
comfortable size, but the card on the right sized to its content instead of
filling the remaining row width, overflowing past the screen edge. The fix
changes the shared row component so the right item fills (and shrinks within)
the remaining row width, and adjusts a font size on the Shift Requests card so
the right content fits cleanly.

## Functional Requirements
- FR-1: On any screen consuming `UzioLeftBorderedRowItem` with a custom
  `rightItemRenderer`, the right-side card must be fully visible within the
  device width — its right edge must not extend past the screen's right edge.
  — screens: Shift Requests, Swap Shift, Open Shifts, My Shifts, Time Tracking
  Home (upcoming schedule), Request Time Off Confirm, Holiday Calendar,
  Completed Time Off Requests.
- FR-2: The left date column must continue to render at the same size /
  position as before the fix (no shrink, no overflow, no truncation of the date
  text).
- FR-3: When `rightContentAlign='start'` is passed (left side flush with right
  content), behaviour must remain unchanged — the existing
  `leftContentRowNoFlex` path still applies.
- FR-4: On Shift Requests → Offer tab and Swap tab, the responder / employee
  name on the right card must render at the reduced size (`hp('1.4%')` instead
  of `hp('1.7%')`) so the name fits inside the card without pushing
  Accept | Reject off-screen.
- FR-5: On Shift Requests → Offer tab, the `Accept` and `Reject` action
  controls must both be fully visible and tappable inside the row.

## UI Elements Affected
- **Shift Requests** screen header — `Shift Requests` (en.json:1123 `shiftRequests`)
- **Offer tab** and **Swap tab** — labels `Offer` / `Swap` (en.json:1118-1119)
- **Incoming Requests** / **Your Requests** accordions — `Incoming Requests`,
  `Your Requests` (en.json:1124-1125)
- **Offer Incoming row** — card shows shift time range `9:00 - 17:00`,
  responder name (e.g. `Lname, Ein`), and `Accept` | `Reject` action buttons
- **Swap Shift** screen header — `Swap Shift` (en.json:1106)
- **Available Shifts** section — `Available Shifts` (en.json:1107); rows show
  date column + shift card on the right
- **My Upcoming Schedule** tile on Time Tracking Home — uses same row layout
- **Time Off** related rows on Request Time Off Confirm, Holiday Calendar,
  Completed Time Off Requests
- No new strings introduced — purely a layout / styling fix in
  `UzioLeftBorderedRowItem.tsx` + one font-size tweak on
  `ShiftRequestListing.tsx`

## Acceptance Criteria
- AC-1: On Shift Requests → Offer tab (iOS + Android), the
  `9:00 - 17:00 / <responder name> / Accept | Reject` card renders entirely
  inside the device viewport — no clipping at the right edge.
- AC-2: On Shift Requests → Swap tab (iOS + Android), the responder card (e.g.
  `9:00 - 17:00 / Lname, Bale`) renders entirely inside the device viewport.
- AC-3: On Swap Shift → Available Shifts (iOS + Android), every Available Shift
  card (e.g. `Thu 18 Jun`, `Fri 19 Jun`, `Mon 22 Jun`) renders fully within the
  screen width — no overflow on the right.
- AC-4: The Offer-tab `Accept` and `Reject` buttons are both visible and
  tappable from the visible portion of the card (no partial obscuring).
- AC-5: The left-side date column on every affected screen renders at the
  same size as before the fix (no visual regression on the date column).
- AC-6: Screens that pass `rightContentAlign='start'` (existing
  consumers) render unchanged.
- AC-7 (developer-verified, see customfield_17321):
  > "Tested on android and ios simulators. Nothing is clipped and the tile is
  > covering the width of the screen for both devices."
  Each automated test must assert that the right-side card's right edge is at
  or inside the device's right edge (≤ screen width minus the row's right
  padding).

## Edge Cases & Conditional Behavior
- EC-1: `rightContentAlign='start'` path → unchanged. The fix preserves the
  existing `leftContentRowNoFlex` behaviour for that branch.
- EC-2: `day` prop missing OR `dayBelowDate` truthy → the modified condition
  `(rightContentAlign === 'start' || !(day && !dayBelowDate))` collapses the
  left column with `leftContentRowNoFlex`. Test rows that hide / move the date
  label below the date must continue to render correctly.
- EC-3: Long responder name (very long surname/first name) → name must wrap or
  truncate inside the card; card must not overflow the row width.
- EC-4: Long shift time range / jobcode text → card grows downward (wrap), not
  rightward beyond the row.
- EC-5: Empty / zero Available Shifts list → `No Shifts Available.` message
  shown; no row component rendered, so no overflow to assert (negative case).
- EC-6: Empty Incoming Requests / Your Requests → `No Requests` empty state
  appears (negative case — no row overflow expected).
- EC-7: Multiple consecutive rows (e.g. 3 Available Shifts on different days)
  → every row independently respects the device width.
- EC-8: Small-screen Android device (e.g. ~360dp width) → fix must still
  prevent overflow. Card must shrink (`flexShrink: 1`) rather than overflow.
- EC-9: Larger phones / tablets → card may grow to fill remaining width;
  alignment should still place card content at the row's right side
  (`alignItems: 'stretch'` replaces `flex-end`).

## Platform Notes
- Android-specific: Original defect reproduces on Android Swap tab; fix must
  be verified on Android emulator/device.
- iOS-specific: Original defect reproduces on iOS Offer tab and Swap Shift →
  Available Shifts; fix must be verified on iOS simulator/device.
- Developer confirmed pixel-level fix on both iOS and Android simulators
  (customfield_17321).

## Reproduction Pre-conditions
- App: NRS Purple build (UzioMobile master ≥ commit fe5dc313).
- Test user: `ein@ch.com` (EE, Ein Lname) — has shift requests and available
  shifts to swap.
- The user's employer must have Shift Scheduling enabled so the Schedule →
  Shift Requests / Swap Shift screens are reachable.

## Out of Scope
- Backend / API changes — none. This is a pure RN layout fix.
- Web (Phix) shift screens — defect is mobile-only.
- Changes to row content (no new fields, no copy changes, no new buttons).
- Behaviour / styling of the left date column (must remain unchanged).
- The Accept / Reject business flow itself (taps still go to the existing
  handlers — this ticket only asserts visibility, not the action result).

## Root Cause (reference)
- File: `src/components/UzioLeftBorderedRowItem.tsx`
- Pre-fix:
  - L124 `leftContentRow` had `flex: 1`.
  - L138-139 `rightItemWrapper` had `flex: 0` + `flexShrink: 0` + `alignItems: 'flex-end'`.
- Post-fix (`fe5dc313`):
  - Conditional `leftContentRowNoFlex` applied when
    `rightContentAlign === 'start'` OR `!(day && !dayBelowDate)`.
  - `rightItemWrapper` → `flex: 1`, `flexShrink: 1`, `alignItems: 'stretch'`.
- File: `src/screens/ShiftScheduleScreens/ShiftRequestListing.tsx` L456
  → responder-name `size` reduced `hp('1.7%')` → `hp('1.4%')`.

## New Locators Needed (`core/locators.py`)
Reusing existing strings where present; adding constants for new ones.

- Already present: `SWAP_SHIFT`, `OFFER_SHIFT`, `OPEN_SHIFTS`, `MY_SHIFTS`,
  `ACCEPT`, `REJECT`.
- **Add** (new constants):
  - `SHIFT_REQUESTS = "Shift Requests"` — Schedule entry / header (en.json `shiftRequests`)
  - `OFFER_TAB = "Offer"` — Shift Requests tab (en.json `offer`)
  - `SWAP_TAB = "Swap"` — Shift Requests tab (en.json `swap`)
  - `INCOMING_REQUESTS = "Incoming Requests"` — accordion title (en.json `incomingRequest`)
  - `YOUR_REQUESTS = "Your Requests"` — accordion title (en.json `yourRequest`)
  - `AVAILABLE_SHIFTS = "Available Shifts"` — Swap Shift section header (en.json `availableShifts`)
  - `NO_SHIFTS_AVAILABLE = "No Shifts Available."` — empty-state (en.json `noShiftsAvailable`)
- **No** new buttons, modals, or copy strings introduced by the fix itself —
  the constants above are needed only so the automated tests can navigate to
  each repro screen.
