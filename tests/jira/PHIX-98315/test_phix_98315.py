"""
PHIX-98315 — Time Entries: tapping 'Add Hours' on a No Show shift collapses
the popup; time-entry form never opens.

Defect-focused regression suite. Scoped tight (5 tests) per the rule that a
single-fix defect doesn't need a 20-case sprawling catalog — we verify the
two root causes the fix addresses, plus the happy path and a non-regression.

Root causes (per dev notes on ticket):
  1. timeStr.length >= 5 rejected H:MM single-digit-hour times (e.g. "9:00",
     length 4) — shifts starting before 10:00 AM never opened the form.
     Fix: relax to >= 4.
  2. Lookup by entryIdentifier returned the FIRST MISSED_SHIFT match on days
     with multiple No Shows — wrong card opened.
     Fix: pass the full card item into handleAddHoursPressed.

Test data on TA env / mobile1@t.com (Virat Mobile1 Sr.) for today (Jun 26):
  04:00-07:30 USB01-USB1   (pre-10AM start)
  08:00-08:30              (second No Show)
  08:30-09:30              (third No Show)

Both root-cause variants reproduce on the SAME day's data — efficient setup.
"""

import pytest

from core.locators import TimeEntries
from pages.time_entries_page import TimeEntriesDayPage, AddEditTimeEntryFormPage


@pytest.mark.jira
@pytest.mark.usefixtures("driver", "ee_on_dashboard")
class TestPHIX98315:

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    # ─────────────────────────── SANITY ──────────────────────────────────────

    def test_tc01_time_entries_day_loads(self, on_time_entries_today_with_no_show):
        """Time Entries day view loads with the No Show test data visible."""
        self._begin("TC-01", "Time Entries day view loads with No Show cards")
        page: TimeEntriesDayPage = on_time_entries_today_with_no_show
        assert page.is_no_show_visible(timeout=5), (
            "Expected at least one 'No Show' status on the day view; check that "
            "today's shifts are past and unclocked on Virat Mobile1 Sr."
        )
        count = page.no_show_card_count()
        print(f"[TC-01] No Show cards visible on today: {count}")
        assert count >= 1
        self._collect(page)

    # ───────────────────────────── CORE FIX (AC-1/2/5) ───────────────────────

    def test_tc06_add_hours_opens_form(self, on_time_entries_today_with_no_show):
        """
        Add Hours on a No Show card opens the AddEditTimeEntryV2 form
        (covers AC-1 + AC-5 — popup must NOT silently collapse).
        """
        self._begin("TC-06", "Add Hours on a No Show opens AddEditTimeEntry form")
        page: TimeEntriesDayPage = on_time_entries_today_with_no_show
        page.open_no_show_kebab(index=0)
        assert page.popup_is_open(timeout=4), "Kebab popup did not open"
        page.tap_add_hours()
        form = AddEditTimeEntryFormPage(self.driver)
        form.verify_loaded(timeout=10)
        assert form.is_text_visible(TimeEntries.FORM_CLOCK_IN_LABEL, 3)
        assert form.is_text_visible(TimeEntries.FORM_CLOCK_OUT_LABEL, 3)
        form.press_back()
        self._collect(page, form)

    # ───────────── PRE-10AM EDGE (EC-1 / AC-4) — length>=4 fix ───────────────

    def test_tc09_pre_10am_start_opens_form(self, on_time_entries_today_with_no_show):
        """
        FIRST No Show on today is the 04:00-07:30 shift — a single-digit-hour
        start. Pre-fix the length>=5 check silently collapsed the popup on
        H:MM (length-4) time strings. Post-fix, the form opens.
        """
        self._begin("TC-09", "Add Hours works on No Show starting before 10:00 AM")
        page: TimeEntriesDayPage = on_time_entries_today_with_no_show
        # Index 0 is the earliest = 04:00 No Show in the test data set up.
        page.open_no_show_kebab(index=0)
        assert page.popup_is_open(timeout=4)
        page.tap_add_hours()
        form = AddEditTimeEntryFormPage(self.driver)
        form.verify_loaded(timeout=10)
        # Defensive: form must show some clock-in time — pre-fix this would
        # never even open (handler bailed when preFilledClockInTime was empty).
        assert form.is_pre_filled(), (
            "Form opened but appears empty — pre-fix bug regression "
            "(length>=5 check rejecting H:MM)"
        )
        form.press_back()
        self._collect(page, form)

    # ───────────── MULTI-SHIFT SAME DAY (EC-3 / AC-3) — wrong-card fix ───────

    def test_tc13_multi_shift_second_card_opens_its_own_form(
            self, on_time_entries_today_with_no_show):
        """
        On a day with MULTIPLE No Show shifts, tapping kebab on the SECOND
        card must open the form pre-filled with the SECOND card's times.

        Pre-fix, the handler looked the card up by entryIdentifier from the
        first MISSED_SHIFT match in trackingInfos, so the first card's times
        opened regardless of which kebab was tapped.

        Sanity guard: skip if only one No Show is present (data drift).
        """
        self._begin("TC-13", "Multi No Show: second card opens its own pre-filled form")
        page: TimeEntriesDayPage = on_time_entries_today_with_no_show
        count = page.no_show_card_count()
        if count < 2:
            pytest.skip(
                f"Need >=2 No Show cards on today's date for AC-3 regression; "
                f"only {count} present. Recheck Virat Mobile1 Sr. data."
            )
        page.open_no_show_kebab(index=1)
        assert page.popup_is_open(timeout=4), (
            "Kebab popup did not open on the second No Show card"
        )
        page.tap_add_hours()
        form = AddEditTimeEntryFormPage(self.driver)
        form.verify_loaded(timeout=10)
        assert form.is_pre_filled(), (
            "Form did not pre-fill from the second card — likely the "
            "entryIdentifier lookup regression"
        )
        # Stronger check: the times on screen must NOT match the FIRST card's
        # 04:00 / 07:30 window — they should be the second card's (e.g. 08:00).
        # Use the absence of "04:00" as a heuristic; tighten when locators
        # for the time pickers are added.
        assert not form.is_text_visible("04:00", 2), (
            "Form opened with the FIRST card's 04:00 pre-fill — wrong-card "
            "regression: handler is looking up by entryIdentifier and "
            "matching the first MISSED_SHIFT instead of the tapped item."
        )
        form.press_back()
        self._collect(page, form)

    # ───────────────────── NON-REGRESSION (AC-7) ─────────────────────────────

    def test_tc16_bottom_add_time_entry_cta_still_works(
            self, on_time_entries_today_with_no_show):
        """
        The date-level bottom 'Add Time Entry' CTA is a separate flow and must
        remain unaffected by the per-shift Add Hours fix.
        """
        self._begin("TC-16", "Bottom 'Add Time Entry' CTA still opens new entry form")
        page: TimeEntriesDayPage = on_time_entries_today_with_no_show
        page.tap_add_time_entry_cta()
        form = AddEditTimeEntryFormPage(self.driver)
        form.verify_loaded(timeout=10)
        assert form.is_text_visible(TimeEntries.FORM_CLOCK_IN_LABEL, 3)
        form.press_back()
        self._collect(page, form)
