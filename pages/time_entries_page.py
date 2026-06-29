"""
Time Entries day-view + Add Edit Time Entry form page objects.

UzioMobile screens:
    src/screens/timesheetScreens/DayStatisticsV2.tsx
    src/screens/timesheetScreens/TimeEntriesCards.tsx
    src/screens/timesheetScreens/AddEditTimeEntryV2.tsx

This module supports PHIX-98315 — the per-card kebab 'Add Hours' on No Show
shifts must open the AddEditTimeEntryV2 form pre-filled with the shift's
clock-in / clock-out. Pre-fix, the popup silently collapsed for shifts
starting before 10:00 AM and always opened the first No Show on multi-shift
days. Tests verify both regression paths.
"""

import time
from appium.webdriver.common.appiumby import AppiumBy

from core.base_page import BasePage
from core.locators import TimeEntries


class TimeEntriesDayPage(BasePage):
    """The DayStatisticsV2 screen — one calendar day's time-entry cards."""

    def verify_loaded(self, timeout: int = 10) -> None:
        self.wait_for_text(TimeEntries.HEADING, timeout)

    def no_show_card_count(self) -> int:
        """Count of 'No Show' status labels visible on the current day view."""
        xp = (
            f"//*[@text='{TimeEntries.NO_SHOW_STATUS}'"
            f" or @content-desc='{TimeEntries.NO_SHOW_STATUS}'"
            f" or @name='{TimeEntries.NO_SHOW_STATUS}'"
            f" or @label='{TimeEntries.NO_SHOW_STATUS}']"
        )
        return len(self.driver.find_elements(AppiumBy.XPATH, xp))

    def is_no_show_visible(self, timeout: int = 5) -> bool:
        return self.is_text_visible(TimeEntries.NO_SHOW_STATUS, timeout)

    def open_no_show_kebab(self, index: int = 0) -> None:
        """
        Tap the 3-dot kebab on the Nth No Show card (0-based).

        The kebab has no visible text and no testID. Strategy:
        locate the Nth 'No Show' status label, then tap the closest sibling
        whose bounds look like a 3-dot button (ImageView/Button with small
        square bounds to the right of the row). We fall back to a coordinate
        tap at the right edge of the row if no button-ish sibling is found.
        """
        labels = self._no_show_labels()
        if not labels:
            raise AssertionError("No Show card not present on the current day")
        if index >= len(labels):
            raise AssertionError(
                f"Requested No Show index {index} but only {len(labels)} present"
            )
        label = labels[index]
        # Try the nearest right-side touchable in the same row.
        try:
            row = label.find_element(AppiumBy.XPATH, "./ancestor::*[@clickable='true'][1]")
            row.click()
            time.sleep(0.4)
        except Exception:
            pass
        # Then tap the kebab — try common a11y patterns first, fall back to bounds.
        for cand_xp in [
            "(//android.widget.ImageView[@clickable='true'])[last()]",
            "(//*[contains(@content-desc,'more') or contains(@content-desc,'menu')"
            " or contains(@content-desc,'option') or contains(@content-desc,'kebab')])"
            "[last()]",
        ]:
            els = self.driver.find_elements(AppiumBy.XPATH, cand_xp)
            if els:
                els[-1].click()
                time.sleep(0.6)
                if self.is_text_visible(TimeEntries.ADD_HOURS, 4):
                    return
        # Last resort: tap to the right of the No Show label using its bounds.
        rect = label.rect
        x = rect["x"] + rect["width"] + 80
        y = rect["y"] + rect["height"] // 2
        self.tap_at(x, y)
        time.sleep(0.6)
        if not self.is_text_visible(TimeEntries.ADD_HOURS, 4):
            raise AssertionError(
                "Kebab popup with 'Add Hours' did not appear after tap"
            )

    def tap_add_hours(self) -> None:
        """Tap 'Add Hours' in the open kebab popup."""
        self.tap(TimeEntries.ADD_HOURS)

    def tap_add_time_entry_cta(self) -> None:
        """Date-level bottom 'Add Time Entry' CTA (unaffected by this defect)."""
        self.scroll_to_text(TimeEntries.ADD_TIME_ENTRY_CTA)
        self.tap(TimeEntries.ADD_TIME_ENTRY_CTA)

    def popup_is_open(self, timeout: int = 3) -> bool:
        """Heuristic: at least one kebab option visible."""
        return any(
            self.is_text_visible(t, timeout)
            for t in (TimeEntries.ADD_HOURS, TimeEntries.CHECK_PHOTOS,
                      TimeEntries.ATTEST_TIME_ENTRY, TimeEntries.SHOW_HISTORY)
        )

    def restrict_popup_visible(self, timeout: int = 5) -> bool:
        return self.is_text_visible(TimeEntries.RESTRICT_OLDER_FRAGMENT, timeout)

    # ─── internal ─────────────────────────────────────────────────────────────

    def _no_show_labels(self):
        xp = (
            f"//*[@text='{TimeEntries.NO_SHOW_STATUS}'"
            f" or @content-desc='{TimeEntries.NO_SHOW_STATUS}'"
            f" or @name='{TimeEntries.NO_SHOW_STATUS}'"
            f" or @label='{TimeEntries.NO_SHOW_STATUS}']"
        )
        return self.driver.find_elements(AppiumBy.XPATH, xp)


class AddEditTimeEntryFormPage(BasePage):
    """The AddEditTimeEntryV2 screen — opened by 'Add Hours' on a No Show card."""

    def verify_loaded(self, timeout: int = 10) -> None:
        # The Clock In time + Clock Out time labels are the most reliable anchors.
        deadline = time.time() + timeout
        while time.time() < deadline:
            if (self.is_text_visible(TimeEntries.FORM_CLOCK_IN_LABEL, 1)
                    or self.is_text_visible(TimeEntries.FORM_CLOCK_OUT_LABEL, 1)):
                return
            time.sleep(0.4)
        raise AssertionError(
            "AddEditTimeEntryV2 form did not appear (no Clock In/Out labels)"
        )

    def is_pre_filled(self, expected_in: str = "", expected_out: str = "") -> bool:
        """
        Sanity check that the time inputs are NOT empty. If the caller passes an
        expected H:MM string we also assert that substring is shown on screen.
        """
        # Empty form would show only the labels with no times — check that *any*
        # digit shows beside the labels via on-screen text containing ':'.
        digits_xp = "//*[contains(@text,':') or contains(@name,':') or contains(@label,':')]"
        has_any_time = bool(self.driver.find_elements(AppiumBy.XPATH, digits_xp))
        if expected_in and not self.is_text_visible(expected_in, 3):
            return False
        if expected_out and not self.is_text_visible(expected_out, 3):
            return False
        return has_any_time

    def save(self) -> None:
        self.tap(TimeEntries.FORM_SAVE)
