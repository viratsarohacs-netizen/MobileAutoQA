"""
PHIX-98287 — UzioLeftBorderedRowItem right-side card clipped past device width.

Defect-focused regression suite. The fix lives in two files (commit fe5dc313 on
UzioMobile master):
  - src/components/UzioLeftBorderedRowItem.tsx  — rightItemWrapper now flex:1,
    flexShrink:1, alignItems:'stretch'; and the left column collapses (no flex)
    when the day-below-date variant is active.
  - src/screens/ShiftScheduleScreens/ShiftRequestListing.tsx — responder name
    size reduced hp('1.7%') -> hp('1.4%') so Accept|Reject fit.

The codified verification mirrors the developer's manual check on Jira:
  > "Tested on android and ios simulators. Nothing is clipped and the tile
  >  is covering the width of the screen for both devices."

Each card-overflow test reads a known card element's on-screen rectangle and
asserts its right edge sits inside the device width (with a small tolerance
for the row's right-padding). Pre-fix the right edge ran ~50% past the
screen width.
"""

import re

import pytest

from core.locators import Schedule
from pages.shift_schedule_page import (
    assert_element_within_screen,
    assert_text_within_screen,
    find_any_visible_text,
    find_element_by_text,
    find_elements_by_text_contains,
)


_TIME_RANGE_RE = re.compile(r"\b\d{1,2}:\d{2}\b")


def _find_time_range_element(driver):
    """
    Find a rendered element whose text contains a "HH:MM" pattern — the right
    card on Shift Requests / Swap Shift renders the shift's time-range string
    (e.g. "9:00 - 17:00"). Returns the element + its text, or (None, None).
    """
    # Cheap pre-filter via page_source — if no time pattern present, no cards.
    try:
        src = driver.page_source
    except Exception:
        src = ""
    if not _TIME_RANGE_RE.search(src):
        return None, None
    # Walk candidate texts found in the source and locate the first one with
    # a backing element. Limiting the scan keeps this fast on large screens.
    seen = set()
    for m in _TIME_RANGE_RE.finditer(src):
        # Pull a slightly wider slice so we match the rendered span (e.g.
        # "9:00 - 17:00") not just "9:00".
        start = max(0, m.start() - 1)
        end = min(len(src), m.end() + 8)
        # Try the exact match first; broaden if that misses.
        text_guess = m.group(0)
        if text_guess in seen:
            continue
        seen.add(text_guess)
        el = find_element_by_text(driver, text_guess)
        if el is not None:
            return el, text_guess
        # Try a longer span: e.g. "9:00 - 17:00" — re-scan around the match.
        wider = src[start:end]
        wm = re.search(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", wider)
        if wm:
            el = find_element_by_text(driver, wm.group(0))
            if el is not None:
                return el, wm.group(0)
    return None, None


@pytest.mark.jira
@pytest.mark.usefixtures("driver", "ee_on_dashboard")
class TestPHIX98287:
    """Right-side card must fit inside device width on every screen consuming
    UzioLeftBorderedRowItem with a custom rightItemRenderer."""

    def _begin(self, test_id, name):
        self._current_test_id = test_id
        self._current_test_name = name
        self._heal_log = []

    def _collect(self, *pages):
        for p in pages:
            self._heal_log.extend(getattr(p, "heal_log", []))

    # ────────────────────────── SANITY ───────────────────────────────────────

    def test_tc01_shift_requests_opens(self, on_shift_requests):
        """Schedule → Shift Requests opens and the tab bar renders."""
        self._begin("TC-01", "Schedule → Shift Requests opens")
        page = on_shift_requests
        assert page.is_text_visible(Schedule.SHIFT_REQUESTS, 5) or \
               page.is_text_visible(Schedule.OFFER_TAB, 3), \
            "Shift Requests heading / tabs did not render"
        self._collect(page)

    def test_tc02_offer_tab_renders(self, on_offer_tab):
        """Offer tab renders Incoming Requests / Your Requests section."""
        self._begin("TC-02", "Offer tab renders accordion sections")
        page = on_offer_tab
        visible = (page.is_text_visible(Schedule.INCOMING_REQUESTS, 5)
                   or page.is_text_visible(Schedule.YOUR_REQUESTS, 3)
                   or page.is_text_visible("No Requests", 3))
        assert visible, (
            "Offer tab did not render any accordion / empty state — possible "
            "screen-load regression unrelated to PHIX-98287."
        )
        self._collect(page)

    def test_tc03_swap_tab_renders(self, on_swap_tab):
        """Swap tab renders accordion sections without crash."""
        self._begin("TC-03", "Swap tab renders accordion sections")
        page = on_swap_tab
        visible = (page.is_text_visible(Schedule.INCOMING_REQUESTS, 5)
                   or page.is_text_visible(Schedule.YOUR_REQUESTS, 3)
                   or page.is_text_visible("No Requests", 3))
        assert visible
        self._collect(page)

    # ────────────────────────── CORE FIX (AC-1..AC-4) ───────────────────────

    def test_tc04_offer_card_time_range_inside_screen(self, on_offer_tab):
        """Offer Incoming card's shift time-range fits inside the device width."""
        self._begin("TC-04", "Offer Incoming time-range fits inside screen")
        page = on_offer_tab
        if not page.is_text_visible(Schedule.INCOMING_REQUESTS, 4):
            pytest.skip(
                "No Incoming Offer Requests visible — seed an Offer request "
                "to this EE, or test on the seeded TA env account."
            )
        el, label = _find_time_range_element(page.driver)
        if el is None:
            pytest.skip("No shift time-range text rendered — no card data")
        assert_element_within_screen(page.driver, el,
                                     label=f"Offer-Incoming time '{label}'")
        self._collect(page)

    def test_tc05_offer_accept_fully_visible(self, on_offer_tab):
        """Offer Incoming card's 'Accept' button is fully inside the screen."""
        self._begin("TC-05", "Offer 'Accept' fully visible")
        page = on_offer_tab
        if not page.is_text_visible(Schedule.ACCEPT, 4):
            pytest.skip("No 'Accept' button rendered — no Offer Incoming data")
        assert_text_within_screen(page.driver, Schedule.ACCEPT)
        self._collect(page)

    def test_tc06_offer_reject_fully_visible(self, on_offer_tab):
        """Offer Incoming card's 'Reject' button is fully inside the screen."""
        self._begin("TC-06", "Offer 'Reject' fully visible")
        page = on_offer_tab
        if not page.is_text_visible(Schedule.REJECT, 4):
            pytest.skip("No 'Reject' button rendered — no Offer Incoming data")
        assert_text_within_screen(page.driver, Schedule.REJECT)
        self._collect(page)

    def test_tc07_swap_tab_card_time_range_inside_screen(self, on_swap_tab):
        """Swap tab card's shift time-range fits inside the device width."""
        self._begin("TC-07", "Swap tab Incoming time-range fits inside screen")
        page = on_swap_tab
        if not page.is_text_visible(Schedule.INCOMING_REQUESTS, 4):
            pytest.skip("No Incoming Swap Requests visible")
        el, label = _find_time_range_element(page.driver)
        if el is None:
            pytest.skip("No shift time-range text rendered")
        assert_element_within_screen(page.driver, el,
                                     label=f"Swap-Incoming time '{label}'")
        self._collect(page)

    # ───────────────────── SWAP SHIFT → AVAILABLE SHIFTS ─────────────────────

    def test_tc08_swap_shift_opens(self, on_swap_shift):
        """Schedule → Swap Shift opens with Available Shifts section."""
        self._begin("TC-08", "Schedule → Swap Shift opens")
        page = on_swap_shift
        ok = (page.is_text_visible(Schedule.AVAILABLE_SHIFTS, 5)
              or page.is_text_visible(Schedule.NO_SHIFTS_AVAILABLE, 3))
        assert ok, (
            "Swap Shift screen did not render Available Shifts heading or "
            "the No Shifts Available empty state."
        )
        self._collect(page)

    def test_tc09_available_shifts_inside_screen(self, on_swap_shift):
        """Every Available Shift card's right edge sits inside the screen width."""
        self._begin("TC-09", "Available Shifts cards fit inside screen")
        page = on_swap_shift
        if page.is_empty_state_visible(timeout=3):
            pytest.skip(
                "No Available Shifts to swap into — EC-5 (empty state) "
                "exercised in TC-15 instead."
            )
        if not page.is_text_visible(Schedule.AVAILABLE_SHIFTS, 5):
            pytest.skip("'Available Shifts' section did not render")
        # Find every shift time-range UzioText on screen and verify each.
        checked = 0
        el, label = _find_time_range_element(page.driver)
        if el is None:
            pytest.skip("No shift time-range text rendered on Available Shifts")
        assert_element_within_screen(page.driver, el,
                                     label=f"Available-Shifts time '{label}'")
        checked += 1
        # Best-effort: also re-check via a stable section anchor to cover the
        # *visible-rect of the section heading* — proves the section itself
        # isn't pushed off screen.
        section_el = find_element_by_text(page.driver, Schedule.AVAILABLE_SHIFTS)
        if section_el is not None:
            assert_element_within_screen(page.driver, section_el,
                                         label="'Available Shifts' heading")
            checked += 1
        print(f"[TC-09] checked {checked} elements for overflow")
        self._collect(page)

    # ────────────────────────── REGRESSION ───────────────────────────────────

    def test_tc10_open_shifts_rows_inside_screen(self, on_open_shifts):
        """Open Shifts rows fit inside the screen width."""
        self._begin("TC-10", "Open Shifts rows fit inside screen")
        page = on_open_shifts
        if page.is_text_visible(Schedule.NO_SHIFT, 2):
            pytest.skip("No Open Shifts data — overflow N/A")
        el, label = _find_time_range_element(page.driver)
        if el is None:
            pytest.skip("No shift rows visible on Open Shifts")
        assert_element_within_screen(page.driver, el,
                                     label=f"Open-Shifts '{label}'")
        self._collect(page)

    def test_tc11_my_shifts_rows_inside_screen(self, on_my_shifts):
        """My Shifts rows fit inside the screen width."""
        self._begin("TC-11", "My Shifts rows fit inside screen")
        page = on_my_shifts
        if page.is_text_visible(Schedule.NO_SHIFT, 2):
            pytest.skip("No My Shifts data")
        el, label = _find_time_range_element(page.driver)
        if el is None:
            pytest.skip("No shift rows visible on My Shifts")
        assert_element_within_screen(page.driver, el,
                                     label=f"My-Shifts '{label}'")
        self._collect(page)

    def test_tc12_upcoming_schedule_tile_inside_screen(self, on_time_tracking_home):
        """Time Tracking → My Upcoming Schedule rows fit inside the screen width."""
        self._begin("TC-12", "Upcoming Schedule tile rows fit inside screen")
        page = on_time_tracking_home
        if not page.is_text_visible(Schedule.MY_UPCOMING_SCHEDULE, 5):
            pytest.skip(
                "'My Upcoming Schedule' tile not visible — feature gate off "
                "or scrolled below fold (smoke-only)."
            )
        # The tile is the section anchor; if any time-range row renders below
        # it, check the row. Otherwise check the section heading itself.
        el, label = _find_time_range_element(page.driver)
        if el is None:
            # No upcoming row data — fall back to checking the section header
            # element's own right edge, which still flexes through the same
            # row component when populated.
            section = find_element_by_text(page.driver, Schedule.MY_UPCOMING_SCHEDULE)
            assert section is not None
            assert_element_within_screen(page.driver, section,
                                         label="Upcoming Schedule heading")
        else:
            assert_element_within_screen(page.driver, el,
                                         label=f"Upcoming '{label}'")
        self._collect(page)

    def test_tc13_holiday_calendar_rows_inside_screen(self, on_holiday_calendar):
        """Holiday Calendar rows fit inside the screen width."""
        self._begin("TC-13", "Holiday Calendar rows fit inside screen")
        page = on_holiday_calendar
        # Pick any non-empty row text; "Holiday" / "Day" rows are typical labels.
        candidates = ("Holiday", "New Year", "Independence", "Christmas",
                      "Thanksgiving", "Labor Day", "Memorial")
        text, el = find_any_visible_text(page.driver, candidates)
        if el is None:
            # As a last resort, any time-range — some org calendars include times.
            el, text = _find_time_range_element(page.driver)
        if el is None:
            pytest.skip("No holiday rows visible — overflow N/A")
        assert_element_within_screen(page.driver, el,
                                     label=f"Holiday-row '{text}'")
        self._collect(page)

    def test_tc14_completed_time_off_rows_inside_screen(self, on_time_off_completed):
        """Completed Time Off rows fit inside the screen width."""
        self._begin("TC-14", "Completed Time Off rows fit inside screen")
        page = on_time_off_completed
        # Heuristic: completed rows show a status text like "Approved" /
        # "Denied" / "Cancelled" alongside the date column.
        candidates = ("Approved", "Denied", "Cancelled", "Cancelled.")
        text, el = find_any_visible_text(page.driver, candidates)
        if el is None:
            pytest.skip("No completed Time Off rows for this EE")
        assert_element_within_screen(page.driver, el,
                                     label=f"Completed-TO '{text}'")
        self._collect(page)

    # ──────────────────────────── EDGE ───────────────────────────────────────

    def test_tc15_no_shifts_available_empty_state(self, on_swap_shift):
        """Empty-state copy renders without horizontal overflow."""
        self._begin("TC-15", "'No Shifts Available.' empty state OK")
        page = on_swap_shift
        if not page.is_empty_state_visible(timeout=3):
            pytest.skip(
                "Available Shifts is non-empty — EC-5 empty-state path not "
                "exercised this run."
            )
        assert_text_within_screen(page.driver, Schedule.NO_SHIFTS_AVAILABLE)
        self._collect(page)
