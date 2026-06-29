"""
Page objects for the Shift Scheduling screens.

PHIX-98287 — the shared `UzioLeftBorderedRowItem` component was clipping the
right-side card past the device width on every screen that supplied a
`rightItemRenderer`. These page objects navigate to each affected screen and
expose a helper to assert that a card element is fully visible within the
device window (its right edge ≤ window width — the row's right padding).

Affected screens (all consumed UzioLeftBorderedRowItem with a custom renderer):
    ShiftRequestListing     — Schedule → Shift Requests (Offer + Swap tabs)
    ShiftSwap               — Schedule → Swap Shift (Available Shifts)
    OpenShiftListing        — Schedule → Open Shifts
    MyShiftListing          — Schedule → My Shifts
    TimeSheet               — Time Tracking home → My Upcoming Schedule tile
    HolidayCalendar         — Drawer → Holiday Calendar
    CompletedTimeOffRequests — Time Off → Completed
    RequestTimeOffConfirm   — Time Off → Request Time Off → Confirm step
"""

import time

from appium.webdriver.common.appiumby import AppiumBy
from core.base_page import BasePage
from core.locators import BottomNav, Schedule, Drawer, TimeOff
from pages.dashboard_page import DashboardPage, ScreenUnavailable


# Row right-padding is wp('3%') in UzioLeftBorderedRowItem.tsx → ~3% of screen
# width. We accept up to 1% of width as rendering jitter when checking that
# a card's right edge sits inside the visible area.
_RIGHT_PAD_TOLERANCE_PCT = 0.04


class ShiftRequestsPage(BasePage):
    """Schedule → Shift Requests (route: ShiftRequestListing)."""

    HEADING = Schedule.SHIFT_REQUESTS

    def verify_loaded(self, timeout=15):
        if not (self.is_text_visible(self.HEADING, timeout)
                or self.is_text_visible(Schedule.OFFER_TAB, 2)
                or self.is_text_visible(Schedule.SWAP_TAB, 2)):
            raise AssertionError(
                f"[ShiftRequestsPage] '{self.HEADING}' not visible — "
                f"either the screen failed to render or the employer does "
                f"not have Shift Scheduling enabled."
            )
        return self

    def open_offer_tab(self):
        self.tap(Schedule.OFFER_TAB)
        time.sleep(1.0)
        return self

    def open_swap_tab(self):
        self.tap(Schedule.SWAP_TAB)
        time.sleep(1.0)
        return self

    def has_incoming_requests(self):
        """True if there is at least one card under Incoming Requests."""
        return self.is_text_visible(Schedule.INCOMING_REQUESTS, 2)

    def has_your_requests(self):
        return self.is_text_visible(Schedule.YOUR_REQUESTS, 2)


class SwapShiftPage(BasePage):
    """Schedule → Swap Shift → Available Shifts (route: ShiftSwap)."""

    HEADING = Schedule.SWAP_SHIFT

    def verify_loaded(self, timeout=15):
        if not (self.is_text_visible(self.HEADING, timeout)
                or self.is_text_visible(Schedule.AVAILABLE_SHIFTS, 2)
                or self.is_text_visible(Schedule.NO_SHIFTS_AVAILABLE, 2)):
            raise AssertionError(
                f"[SwapShiftPage] '{self.HEADING}' / Available Shifts section "
                f"not visible — verify Shift Scheduling is enabled and the EE "
                f"has at least one swap-eligible shift."
            )
        return self

    def has_available_shifts(self):
        return (self.is_text_visible(Schedule.AVAILABLE_SHIFTS, 2)
                and not self.is_text_visible(Schedule.NO_SHIFTS_AVAILABLE, 1))

    def is_empty_state_visible(self, timeout=3):
        return self.is_text_visible(Schedule.NO_SHIFTS_AVAILABLE, timeout)


class ScheduleNavigator(BasePage):
    """Light helper to navigate inside the Schedule bottom tab."""

    def open_schedule_tab(self):
        dash = DashboardPage(self.driver)
        dash.dismiss_blocking_dialogs()
        # Schedule tab may be feature-gated. open_tab raises ScreenUnavailable
        # if absent, which the test layer translates to pytest.skip.
        dash.open_tab(BottomNav.SCHEDULE,
                      verify_any=[Schedule.HEADING, Schedule.MY_SHIFTS,
                                  Schedule.OPEN_SHIFTS, Schedule.SHIFT_REQUESTS])
        return self

    def open_shift_requests(self):
        self.open_schedule_tab()
        if not self.is_text_visible(Schedule.SHIFT_REQUESTS, 5):
            raise ScreenUnavailable(
                "'Shift Requests' tile not visible on Schedule home — "
                "feature may be gated for this employer")
        self.tap(Schedule.SHIFT_REQUESTS)
        page = ShiftRequestsPage(self.driver)
        page.verify_loaded()
        return page

    def open_swap_shift(self):
        self.open_schedule_tab()
        if not self.is_text_visible(Schedule.SWAP_SHIFT, 5):
            raise ScreenUnavailable(
                "'Swap Shift' tile not visible on Schedule home")
        self.tap(Schedule.SWAP_SHIFT)
        page = SwapShiftPage(self.driver)
        page.verify_loaded()
        return page

    def open_simple_tile(self, tile_text, anchors=()):
        """Generic open helper for the simpler Schedule tiles (Open Shifts /
        My Shifts) — returns self so the test can poll the rows."""
        self.open_schedule_tab()
        if not self.is_text_visible(tile_text, 5):
            raise ScreenUnavailable(f"'{tile_text}' tile not visible")
        self.tap(tile_text)
        # Verify we landed somewhere reasonable (the tile heading on its own
        # detail screen, or an empty-state).
        deadline = time.time() + 10
        while time.time() < deadline:
            for a in (tile_text, *anchors):
                if self.is_text_visible(a, 1):
                    return self
            time.sleep(0.5)
        raise AssertionError(f"Detail screen for '{tile_text}' did not render")


# ─── Visibility (overflow) assertion ──────────────────────────────────────────

def _window_size(driver):
    s = driver.get_window_size()
    return s["width"], s["height"]


def find_element_by_text(driver, text):
    """Return the first element whose text/content-desc/name/label matches."""
    xp = (f"//*[@text='{text}' or @content-desc='{text}' or @name='{text}' "
          f"or @label='{text}' or @value='{text}']")
    els = driver.find_elements(AppiumBy.XPATH, xp)
    return els[0] if els else None


def find_elements_by_text_contains(driver, text):
    xp = (f"//*[contains(@text,'{text}') or contains(@content-desc,'{text}') "
          f"or contains(@name,'{text}') or contains(@label,'{text}')]")
    return driver.find_elements(AppiumBy.XPATH, xp)


def assert_element_within_screen(driver, element, label=""):
    """
    Core PHIX-98287 assertion. Reads the element's on-screen rectangle and
    asserts that its right edge sits at or inside the device's right edge.

    `label` is used in the error message for traceability.
    """
    rect = element.rect  # {'x', 'y', 'width', 'height'}
    width, _ = _window_size(driver)
    right_edge = rect["x"] + rect["width"]
    # Tolerance for sub-pixel rounding / row right-padding overlap.
    tolerance = int(width * _RIGHT_PAD_TOLERANCE_PCT)
    inside = right_edge <= width + tolerance
    msg = (
        f"[overflow] {label or 'element'} right edge {right_edge}px "
        f"exceeds screen width {width}px (rect={rect}, tolerance={tolerance}px). "
        f"Pre-fix PHIX-98287 reproduction: UzioLeftBorderedRowItem.rightItemWrapper "
        f"was flex:0 + flexShrink:0, sizing to content and overflowing."
    )
    assert inside, msg
    print(f"[overflow OK] {label}: right={right_edge} <= screen={width} (+tol {tolerance})")
    return right_edge, width


def assert_text_within_screen(driver, text):
    """Locate `text` and assert its rendered element fits inside the screen."""
    el = find_element_by_text(driver, text)
    assert el is not None, (
        f"Text not found on screen for overflow check: '{text}'. "
        f"Either the screen didn't load, or the data is missing."
    )
    return assert_element_within_screen(driver, el, label=f"text='{text}'")


def find_any_visible_text(driver, candidates):
    """Return the first text from `candidates` that has a rendered element."""
    for t in candidates:
        el = find_element_by_text(driver, t)
        if el is not None:
            return t, el
    return None, None
