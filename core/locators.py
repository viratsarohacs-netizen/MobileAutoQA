"""
Locator text constants for the UZIO Mobile app.

IMPORTANT: The UzioMobile app has NO testID / accessibilityLabel props.
All elements must be located by their VISIBLE TEXT, which comes from i18n keys
resolved against src/i18n/locales/en.json in the UzioMobile repo.

These constants are the resolved English strings. If a string changes in en.json
(or for a white-label flavor), update it here in one place.

Source files (UzioMobile repo):
    src/screens/Login/Login.tsx
    src/screens/timesheetScreens/timesheetMainScreen.tsx
    src/screens/ScreenHelperComponents/MissedBreakSelectModal.tsx
    routing/ScreenConstants.tsx, routing/BottomTabs.tsx
    src/components/UzioSliderTabs.tsx, UzioMainHeaderBar.tsx
    src/i18n/locales/en.json
"""


class Login:
    HEADING = "Welcome to UZIO"
    USERNAME_PLACEHOLDER = "Username (Email Address)"
    PASSWORD_PLACEHOLDER = "Password"
    LOGIN_BUTTON = "LOGIN"                 # btn.login uppercased in code
    FORGOT_PASSWORD = "Forgot Password?"
    SSO_WORK_EMAIL = "Work Email"
    SSO_CONTINUE = "CONTINUE"
    INVALID_CREDENTIALS = "The username or password is incorrect."


class BottomNav:
    # NOTE: tabs are feature-flag gated; not all appear for every employer.
    # There is NO "Home" or "Profile" tab. Default landing tab = Time Tracking.
    BENEFITS = "Benefits"
    SCHEDULE = "Schedule"
    TIME_TRACKING = "Time Tracking"        # default landing tab
    TIME_OFF = "Time Off"
    INBOX = "Inbox"


class TimeTracking:
    HEADING = "Time Tracking"
    CLOCK_IN = "Clock In"
    CLOCK_OUT = "Clock Out"
    BREAK_TIME = "Break Time"

    # Clocked-state sub-heading labels
    CLOCKED_IN = "Clocked In"
    ON_BREAK = "On Break"
    DATE_LABEL = "Date"                    # shown when clocked out / idle

    # Success confirmation modals (global modal with a Close button)
    MODAL_CLOSE = "Close"
    YOU_ARE_CLOCKED_IN = "You are Clocked In"
    YOU_ARE_CLOCKED_OUT = "You are Clocked Out"
    YOU_ARE_ON_BREAK = "You are on Break"
    BREAK_HAS_ENDED = "Break has Ended"
    SWITCH_SUCCESS = "Time entry switched successfully."

    # Indicators that mean "currently clocked in" — PERSISTENT screen state only.
    # HEALED 2026-05-23: do NOT include the "You are Clocked In" confirmation modal
    # text here. It's transient and must be CLOSED (tap "Close"), not treated as the
    # clocked-in state — otherwise the modal is left open and blocks the next test.
    CLOCKED_IN_INDICATORS = [
        "Clock Out",          # button switches to Clock Out when clocked in
        "Clocked In",         # status sub-heading
    ]
    CLOCKED_OUT_INDICATORS = [
        "Clock In",
    ]


class Attestation:
    """
    The MissedBreakSelectModal — triggers on a Clock Out that returns
    HTTP inner-status 428 (missed breaks / time attestation required).
    """
    TITLE = "Time Attestation"
    TITLE_ALT = "Resolve Missed Breaks & Time Attestation"
    HEADING = "Missed Break Attestation"
    CONFIRM_CHECKBOX = "I have reviewed my time and confirm it is complete and accurate."
    BREAK_QUESTION = "Where you provided the opportunity to take the following break(s)?"
    OPTION_TOOK_BREAK = "Yes,I took this break."
    OPTION_PREVENTED = "No, I was prevented by work from taking this break."
    OPTION_FREELY_CHOSE = "Yes, I had the opportunity, but I freely choose not to take this break."
    SAVE_AND_CLOCK_OUT = "Save and Clock Out"

    # Any of these texts on screen indicates the attestation modal is present
    INDICATORS = [TITLE, TITLE_ALT, HEADING, SAVE_AND_CLOCK_OUT]


class Drawer:
    """
    Side drawer (slider menu) — opened via the hamburger icon (Ionicon 'menu-sharp')
    in the top-left of the header bar. Logout is at the very bottom (scroll to reach).
    Section headers are uppercased in the UI.
    """
    LOGOUT = "Logout"
    SWITCH_COMPANY = "Switch Company"
    # Section headers
    SEC_MANAGE_TEAM = "MANAGE TEAM"
    SEC_TIME_AND_ATTENDANCE = "TIME AND ATTENDANCE"
    SEC_PAY = "PAY"
    SEC_PERSONAL = "PERSONAL"
    SEC_SETTINGS = "SETTINGS"
    SEC_HELP_SUPPORT = "HELP AND SUPPORT"
    # Manage Team
    TEAM_TIMESHEET = "Team Timesheet"
    TEAM_TIME_OFF = "Team Time Off"
    # Time & Attendance
    MY_TIMESHEET = "My Timesheet"
    TIME_OFF_HISTORY = "Time Off History"
    HOLIDAY_CALENDAR = "Holiday Calendar"
    # Pay
    PAY_STUBS = "Pay Stubs"
    PAYMENT_METHOD = "Payment Method"
    W2_FORMS = "W-2 Forms"
    FEDERAL_TAX = "Federal Tax Withholding"
    # Personal
    MY_INFO = "My Info"
    DOCUMENTS = "Documents"
    TASKS = "Tasks"
    RESOURCES = "Resources"
    # Settings / Account
    APP_LOCK = "App Lock"
    KIOSK_LOGIN = "Kiosk Login"
    ACCOUNT_INFORMATION = "Account Information"
    LOGIN_ACCOUNTS = "Login Accounts"
    TWO_STEP_VERIFICATION = "2-Step Verification"
    LANGUAGE = "Language"
    # Help & Support
    CONTACT_SUPPORT = "Contact Support"
    HELP_CENTER = "Help Center"
    ABOUT_UZIO = "About UZIO"


class Welcome:
    """First-launch onboarding carousel (3 slides) — src/screens/welcomeScreen/Swiper.tsx."""
    SLIDE1_BENEFITS = "Benefits"
    SLIDE2_PAYROLL = "Payroll"
    SLIDE3_TIME_TRACKING = "Time Tracking"
    SKIP = "Skip"
    LETS_BEGIN = "Let's Begin"


class AppLock:
    """Post-login 'Enable App Lock' biometric prompt — src/screens/AppLock.tsx."""
    HEADING = "App Lock"
    ENABLE_HEADING = "Enable App Lock"
    ENABLE = "Enable"
    LATER = "I'll do it later"          # match via contains("do it later") — apostrophe breaks xpath
    LATER_FRAGMENT = "do it later"


class Schedule:
    HEADING = "Schedule"
    MY_UPCOMING_SCHEDULE = "My Upcoming Schedule"
    VIEW_FULL_SCHEDULE = "View Full Schedule"
    NO_SHIFT = "No Shift"
    SWAP_SHIFT = "Swap Shift"
    OFFER_SHIFT = "Offer Shift"
    OPEN_SHIFTS = "Open Shifts"
    MY_SHIFTS = "My Shifts"

    # PHIX-98287 — Shift Requests + Swap Shift screens that consume
    # UzioLeftBorderedRowItem. The fix re-flowed the right-side card so it
    # stops overflowing past the screen edge. These constants drive the
    # automated regression tests; they are i18n-resolved English strings.
    SHIFT_REQUESTS = "Shift Requests"            # i18n: shift.shiftRequests
    OFFER_TAB = "Offer"                          # i18n: shift.offer
    SWAP_TAB = "Swap"                            # i18n: shift.swap
    INCOMING_REQUESTS = "Incoming Requests"      # i18n: shift.incomingRequest
    YOUR_REQUESTS = "Your Requests"              # i18n: shift.yourRequest
    AVAILABLE_SHIFTS = "Available Shifts"        # i18n: shift.availableShifts
    NO_SHIFTS_AVAILABLE = "No Shifts Available." # i18n: shift.noShiftsAvailable
    # Card action buttons live on the Offer Incoming row only
    ACCEPT = "Accept"
    REJECT = "Reject"


class Benefits:
    HEADING = "Benefits"
    CURRENT = "Current"
    PENDING = "Pending"
    UPCOMING = "Upcoming"
    INSURANCE_CARDS = "Insurance Cards"
    PLAN_DOCUMENTS = "Plan Documents"
    SUMMARY_BENEFITS_COVERAGE = "Summary of Benefits and Coverage"


class Pay:
    PAY_STUBS = "Pay Stubs"
    PAY_PERIOD = "Pay Period"
    NET_PAY = "Net Pay"
    PAYMENT_METHOD = "Payment Method"
    DIRECT_DEPOSIT = "Direct Deposit"
    W2_FORMS = "W-2 Forms"
    NO_W2 = "No W-2 Forms are Available"
    FEDERAL_TAX = "Federal Tax Withholding"
    FILING_STATUS = "Filing Status"
    # SECURITY: sanity verifies screen loads only — NEVER enter account/routing numbers.


class Personal:
    MY_INFO = "My Info"
    PERSONAL_DETAILS = "Personal Details"
    HOME_ADDRESS = "Home Address"
    DOCUMENTS = "Documents"
    TASKS = "Tasks"
    TASKS_PENDING = "Pending"
    TASKS_COMPLETED = "Completed"
    RESOURCES = "Resources"


class Inbox:
    HEADING = "Inbox"
    ACTION_NEEDED = "Your Action Needed"
    NOTIFICATIONS = "Notifications"
    NO_NOTIFICATIONS = "No Notifications Available"
    CLEAR_ALL = "Clear All"


class ManageTeam:
    TEAM_TIMESHEET = "Team Timesheet"
    TEAM_TIME_OFF = "Team Time Off"
    WHOS_OUT = "Who's out during this period"


class TimeOff:
    HEADING = "Time Off"
    AVAILABLE = "Available"
    UPCOMING = "Upcoming"
    PENDING = "Pending"
    COMPLETED = "Completed"
    REQUEST_TIME_OFF = "Request Time Off"
    SELECT_TYPE = "Select Time Off Type"
    START_DATE = "Start Date"
    END_DATE = "End Date"
    SUBMIT_FOR_APPROVAL = "Submit for Approval"
    REQUEST_SUBMITTED = "Request Submitted Successfully"
    HOLIDAY_CALENDAR = "Holiday Calendar"
    TEAM_TIME_OFF = "Team Time Off"
    TIME_OFF_HISTORY = "Time Off History"
    NO_POLICY = "No Policy Assigned"


class MyTimesheet:
    HEADING = "My Timesheet"
    PAY_PERIOD = "Pay Period"
    SELECT_PAY_PERIOD = "Select Pay Period"
    TOTAL_PAID_HOURS = "Total Paid Hours"
    NO_TIME_ENTRIES_TO_DISPLAY = "No time entries to display"
    CONFIRM = "Confirm"
    CLOSE = "Close"

    # Proposed / change-request entry card (ER and EE views)
    MANUAL_ENTRY_PENDING_APPROVAL = "Manual Entry Pending for Approval"

    # Action buttons — ER view
    ACCEPT = "Accept"
    REJECT = "Reject"
    NO = "No"

    # Accept Time Entry modal (opens when ER taps Accept on card)
    # i18n: timeEntries.acceptEmployeeTimeEntryHeading
    ACCEPT_MODAL_HEADING = "Accept employee time entry changes"

    # Reject Time Entry modal
    REJECT_MODAL_TITLE = "Reject Time Entry"
    REJECT_REASON_PLACEHOLDER = "Enter reason for rejection (optional)"
    SEND_EMAIL_NOTIFICATION = "Send email notification to employee"
    # Warning inside reject modal — depends on CR type (isProposedEntry flag)
    REJECT_WARNING_NEW_ENTRY = "Rejecting this entry will permanently delete this time entry."
    REJECT_WARNING_MODIFICATION = "If rejected, the modifications will be discarded and the time entry will be reverted to its previous state."

    # EE-side text for NEW manual entry awaiting manager review
    # Rendered by: TimeEntriesCards — isManuallyAdded && !isManagerApprovalPage branch
    # i18n: timeEntries.manualEntryPendingNotice
    MANUAL_ENTRY_PENDING_NOTICE = "This time entry is currently pending manager approval"

    # EE-side cancel for MODIFICATION CRs
    # Rendered inside the employee-modifications accordion (hasPendingEmployeeModification)
    # i18n: timeEntries.cancelModifications
    CANCEL_MODIFICATIONS = "Cancel Modifications"
    # i18n: timeEntries.cancelModificationsTooltip
    CANCEL_MODIFICATIONS_TOOLTIP = "Cancelling will discard the pending modifications"

    # Cancel-modification confirmation dialog (EE flow)
    CANCEL_CONFIRM_MESSAGE = "Your pending changes will be discarded, and the time entry will revert to its previous state. Do you want to continue?"
    CANCEL_CONFIRM_YES = "Yes"

    # Clock-out blocked modal — when EE tries to clock out with a pending modification CR
    # i18n: timeEntries.cancelModificationsAndClockOut
    CANCEL_MODIFICATIONS_AND_CLOCK_OUT = "Cancel Modifications & Clock Out"
    DISMISS = "Dismiss"

    # Block messages (partial — app text is longer; use contains-match)
    CLOCK_OUT_BLOCKED_PARTIAL = "You have pending modifications on this time entry that are awaiting manager approval."
    ADD_TIME_BLOCKED_PARTIAL = "Time cannot be added while modifications are pending manager approval"

    # Edit-disabled messages — ER view
    # i18n: timeEntries.editDisabledManualEntryER
    EDIT_DISABLED_NEW_ENTRY_ER = (
        "This time entry is currently pending your approval and cannot be edited at this time. "
        "To make changes, you must first accept or reject the time entry."
    )
    # i18n: timeEntries.editDisabledPendingModifER
    EDIT_DISABLED_MODIFICATION_ER = (
        "This time entry modification is currently pending your approval and cannot be edited further at this time. "
        "To make changes, you must first accept or reject the pending modifications."
    )

    # Edit-disabled messages — EE view
    # i18n: timeEntries.editDisabledManualEntryEE
    EDIT_DISABLED_NEW_ENTRY_EE = "This time entry is currently pending manager approval and cannot be edited at this time."
    # i18n: timeEntries.editDisabledPendingModifEE
    EDIT_DISABLED_MODIFICATION_EE = "This time entry modification is currently pending manager approval and cannot be edited further at this time."

    # Add/Edit time entry buttons
    ADD_TIME_ENTRY = "Add Time Entry"
    EDIT_TIME_ENTRY = "Edit Time Entry"


class TimeEntries:
    """
    Time Entries day-view labels (DayStatisticsV2.tsx + TimeEntriesCards.tsx).

    Reached by selecting a date inside the My Timesheet pay period. Each date
    renders a list of "cards" — regular time entries, Time Off, Holiday, and
    No Show (source='MISSED_SHIFT') cards for scheduled shifts the EE never
    clocked into.

    Defect PHIX-98315 lives here: the per-card 3-dot kebab → 'Add Hours' on a
    No Show card must navigate to AddEditTimeEntryV2 pre-filled with the
    shift's clock-in / clock-out. Pre-fix it silently collapsed for shifts
    starting before 10:00 AM (H:MM time string length 4 vs the >=5 check) and
    always opened the FIRST No Show card on days with multiple No Show shifts.
    """
    HEADING = "Time Entries"                          # i18n: timeEnteries (sic)
    NO_TIME_ENTRIES_AVAILABLE = "No Time Entries Available"
    SELECT_TIME_ENTRIES_DAY = "Select Time Entries Day"

    # No Show card (source='MISSED_SHIFT')
    NO_SHOW_STATUS = "No Show"                        # i18n: timeEntries.noShow

    # Kebab popup options (DayStatisticsV2 — items shown depend on card type)
    ADD_HOURS = "Add Hours"                           # i18n: dayStatistics.addHours
    CHECK_PHOTOS = "Check Photos"                     # i18n: dayStatistics.checkPhotos
    ATTEST_TIME_ENTRY = "Attest Time Entry"           # i18n: dayStatistics.attestTimeEntry
    ADD_NOTES = "Add Notes"                           # i18n: dayStatistics.addNotes
    SHOW_HISTORY = "Show History"                     # i18n: dayStatistics.history

    # Date-level bottom CTA (unaffected by this defect; non-regression check)
    ADD_TIME_ENTRY_CTA = "Add Time Entry"             # i18n: dayStatistics.addTimeEntry

    # Add/Edit Time Entry form — reached by Add Hours
    # Route name: AddEditTimeEntryV2 (no testID; identify by visible labels)
    FORM_CLOCK_IN_LABEL = "Clock In time"             # i18n: addEditTimeEntry.clockInTime
    FORM_CLOCK_OUT_LABEL = "Clock Out time"           # i18n: addEditTimeEntry.clockOutTime
    FORM_SAVE = "Save"

    # Retro-action restriction (EC-4) — substring match; days is interpolated
    RESTRICT_OLDER_FRAGMENT = "time entry is older than"
    # Full template: "This action cannot be performed because the time entry
    #                 is older than {{days}} days."


class TimesheetHistory:
    """Labels that appear in Time Entry History for CR-related events."""
    TIME_ENTRY_ACCEPTED = "Time Entry Accepted"
    MODIFICATIONS_ACCEPTED = "Modifications Accepted"
    TIME_ENTRY_REJECTED = "Time Entry Rejected"
    MODIFICATIONS_REJECTED = "Modifications Rejected"
    TIME_ENTRY_CANCELLED = "Time Entry Cancelled"
    MODIFICATIONS_CANCELLED = "Modifications Cancelled"


class TeamTimesheet:
    HEADING = "Team Timesheet"


# Generic popup dismiss-button texts (used by dismiss_popup_if_present)
COMMON_DISMISS_BUTTONS = [
    "Close", "OK", "Okay", "Got it", "Continue", "Confirm",
    "Yes", "Allow", "Accept", "Done",
]

# No-internet / resilience messages
NO_INTERNET_MESSAGES = [
    "No Internet. Please try again later.",
    "No Internet Connection",
]


# ────────────────────────────────────────────────────────────────────────────
# White-label flavor — NRS Purple (PHIX-86688)
#
# Strings resolved from UzioMobile src/i18n/locales/en_nrspurple.json + en.json.
# Used by tests/jira/PHIX-86688/ when running against APP_NAME=NRSPURPLE.
# ────────────────────────────────────────────────────────────────────────────

class NrsPurple:
    APP_NAME = "NRS Purple"                       # t('APP_NAME')

    # Theme colour (header / safe-area)
    THEME_COLOR_HEX = "#563d6e"

    # Login
    LOGIN_HEADING = "Welcome to NRS Purple"       # login.heading

    # Error / auth
    UNAUTHORIZED = "You are not authorized to access NRS Purple mobile application."

    # New shared key added to base en.json by this ticket (used by every flavor)
    SOCIAL_LOGIN_FAILED = "Social login failed. Please try again"

    # About Us
    ABOUT_HEADING = "About NRS Purple"
    ABOUT_SUBHEADING = "NRS Purple"
    ABOUT_FOOTER = "Copyright © 2026 National Retail Solutions, Inc. All Rights Reserved."
    ABOUT_INFO_FRAGMENT = "NRS Purple provides payroll software"
    ABOUT_INFO_FRAGMENT_2 = "The NRS Purple Employee Portal and mobile app"

    # Drawer item label (replaces Drawer.ABOUT_UZIO on this flavor)
    DRAWER_ABOUT_ITEM = "About NRS Purple"

    # Kiosk consent (partial — substring match)
    KIOSK_CONSENT_FRAGMENT_1 = "by NRS Purple and its service providers"
    KIOSK_CONSENT_FRAGMENT_2 = "NRS Purple Kiosk facial recognition feature"
