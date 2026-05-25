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
