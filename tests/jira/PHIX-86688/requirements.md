# PHIX-86688 — Requirements
# Source: Jira (fetched 2026-06-16)
# Type: User Story (parent — mobile UI side)
# Status: Code Review · Priority: Major · Fix Versions: neuron-13.0, neuron-12.4.10
# Mobile screens: Login, Login OTP, Register/Switch Accounts, About Us, Side Drawer (language)

## Summary
NRS Purple is being onboarded as a new white-label flavor of the UZIO mobile app
(alongside CAFEPAY, VANGST, TECHSERVE, TWENTYAI, ROLLOHCM, APPRENTOS, COREPAY).
Until now NRS Purple has been a payroll-only client and the mobile app was not
available to its users. This story stands up the full NRS Purple mobile build:
new app target (Android `nrspurple` flavor + iOS `NrsPurple` scheme), `.env.nrspurple`,
branded launcher icons, splash, header colour, square/short logos, About Us copy,
and a dedicated `en_nrspurple` locale. It also wires NRS Purple into the same
subdomain-aware login flow used by the other white-label apps so that Time Tracking,
Time Off, OTP and password login behave consistently with TechServe 360.

This is the **mobile-app** half of the NRS Purple launch. The backend/email-template
half is tracked in the linked sub-story [PHIX-98187](../PHIX-98187/requirements.md).

## Functional Requirements
- **FR-1** A dedicated NRS Purple build (`APP_NAME=NRSPURPLE`) loads its own assets,
  colours and copy — screens: all branded screens (Login, Loading splash, About Us,
  Side Drawer header, app launcher icon).
- **FR-2** Login screen renders the NRS Purple **square** brand logo (`NrspurpleLogo.svg`,
  60×60 via `BrandLogo`) instead of the UZIO logo — screen: Login.
- **FR-3** Login screen layout — the logo wrapper is left-aligned (`alignItems: 'flex-start'`,
  width `55%`) instead of centred — screen: Login (`LoginContentHelper.tsx`).
- **FR-4** Loading/splash screen shows the square NRS Purple logo — screen: Loading.
- **FR-5** About Us screen displays the **short** NRS Purple logo on the left,
  heading `About NRS Purple`, sub-heading `NRS Purple`, app version, the new
  English info paragraph (about payroll software and the Employee Portal / mobile
  app) and copyright footer `Copyright © 2026 National Retail Solutions, Inc.
  All Rights Reserved.` — screen: About Us (`src/screens/AboutUs.tsx`).
- **FR-6** App theme colour for the safe-area and primary surfaces is `#563d6e`
  (purple) — applied via `COLOR.SAFE_AREA_BACKGROUND_COLOR.NRSPURPLE` and the
  primary colour map. Screens affected: every screen that reads safe-area /
  header colour.
- **FR-7** App name shown in OS launcher / Switch Accounts header / About Us
  sub-heading reads **"NRS Purple"** (from `t('APP_NAME')`). The Switch Accounts
  screen previously used a runtime title-case of `Config.APP_NAME`; that hack is
  now replaced by the i18n key — screen: `LoginResigterAccounts.tsx`.
- **FR-8** A new locale `en_nrspurple` is registered in `i18n.js`. When
  `Config.APP_NAME === 'NRSPURPLE'`, `updateUserLanguage()` activates
  `<lang>_nrspurple`, and the in-app language picker (`getLanguageArray()`)
  returns only `en_nrspurple`. Default locale is set via `.env.nrspurple`.
- **FR-9** Login flow includes NRS Purple in the **subdomain-passing** list:
  - `Login.tsx` direct-login POST adds `subdomain` to the body when
    `APP_NAME ∈ {CAFEPAY, VANGST, TECHSERVE, TWENTYAI, ROLLOHCM, APPRENTOS,
    COREPAY, **NRSPURPLE**}`.
  - `LoginOtp.tsx` adds the same `subdomain` field on both OTP send and OTP
    verify calls for the same list.
- **FR-10** Side drawer menu shows the **About Us** entry for NRS Purple
  (`sliderTabsConfig.tsx` `appNames` list now includes `'NRSPURPLE'`).
- **FR-11** New error string `login.socialLoginFailed = "Social login failed.
  Please try again"` is added to base `en.json`. Login.tsx now selects between
  `login.ssoLoginFailed` (SSO path) and `login.socialLoginFailed`
  (non-SSO/social path) when authentication fails — screen: Login.
- **FR-12** Unauthorized-access guard message for NRS Purple reads:
  `"You are not authorized to access NRS Purple mobile application."` (locale
  key `error.unauthorized`).
- **FR-13** Kiosk facial-recognition consent message references **NRS Purple**
  (replacing UZIO) in both occurrences:
  `"By clicking below, I voluntarily consent ... by NRS Purple and its service
  providers ..."` and `"... my employer has enabled NRS Purple Kiosk facial
  recognition feature ..."` — locale key `kioskLogin.registrationConsentMessageDesc`.

## UI Elements Affected
- **Login screen** — square NRS Purple logo, left-aligned, on the purple
  safe-area background. Heading from `t('login.heading')` resolves to
  `"Welcome to NRS Purple"`.
- **About Us screen** — short NRS Purple logo (left), `About NRS Purple`,
  `NRS Purple` sub-heading (now coloured `COLOR.BLACK`, top-aligned with logo),
  `App v<APP_VERSION>` (version `6.4.9` per `.env.nrspurple`), the new info
  paragraph, copyright footer.
- **Loading splash** — square NRS Purple logo on purple background.
- **Side drawer** — "About Us" menu entry visible for NRS Purple users.
- **Switch / Register Accounts screen** — app-name label resolved from
  `t('APP_NAME')` → `"NRS Purple"` (no more title-cased `NRSPURPLE`).
- **OS launcher** — Android `ic_launcher.png` (mipmap-*dpi*) and iOS
  `AppIcon-NrsPurple.appiconset` show the new padded logo on a dark base.
  Android `strings.xml` provides `app_name = NRS Purple` for the launcher label.

## Acceptance Criteria (mobile-app side)
- **AC-1** When the NRS Purple build is installed, the OS launcher shows the
  new icon and label "NRS Purple".
- **AC-2** Splash/loading screen shows the **square** NRS Purple logo.
- **AC-3** Login screen header colour is the NRS Purple purple `#563d6e`,
  matching the XD design.
- **AC-4** Login screen shows the **square** NRS Purple logo at the left edge
  of the form.
- **AC-5** A valid NRS Purple employee user can log in via email + password
  on the NRS Purple build; the login POST carries the correct `subdomain`.
- **AC-6** OTP login flow (send + verify) works on the NRS Purple build and
  carries the correct `subdomain`.
- **AC-7** Side drawer → About Us opens and shows: short logo, heading
  `About NRS Purple`, sub-heading `NRS Purple`, `App v<APP_VERSION>`, the
  new info paragraph, copyright footer text.
- **AC-8** A user with no access to NRS Purple sees the message
  `"You are not authorized to access NRS Purple mobile application."`
- **AC-9** When the kiosk consent screen is opened (manager kiosk flow), the
  consent body text references "NRS Purple" (not "UZIO") in both paragraphs.
- **AC-10** A non-SSO login failure shows `"Social login failed. Please try
  again"`; an SSO login failure shows `"SSO login failed. Please try again"`
  (already existed).
- **AC-11** Language picker in the side-drawer / profile shows exactly one
  option mapped to `en_nrspurple`.
- **AC-12** Switch Accounts header reads "NRS Purple" exactly (case-correct).

## Edge Cases & Conditional Behavior
- **EC-1** App must read `APP_NAME=NRSPURPLE` from `.env.nrspurple` — building
  any other flavor must NOT pick up NRS Purple branding (build-flavor regression).
- **EC-2** Default locale on first launch is `en_nrspurple` (via env), even
  before the user logs in.
- **EC-3** If `Config.APP_NAME` is NRSPURPLE but the locale file fails to load,
  the language picker should still return the `en_nrspurple` option (it is
  hard-coded in `getLanguageArray()` — but the strings will fall back).
- **EC-4** Subdomain passthrough on login: if NRS Purple build is pointed at
  a non-`internal.uzio.org` server (e.g., misconfigured `.env`), login must
  still send the `subdomain` field — server determines correctness, app must
  not silently skip it.
- **EC-5** About Us logo alignment changed from `center` to `flex-start` (top-
  aligned with the text block) — regression check on the other flavors that
  share this screen.
- **EC-6** Login screen logo width changed from `hp('8%')` to `wp('55%')` —
  regression check on UZIO/CAFEPAY/TECHSERVE/TWENTYAI/ROLLOHCM/APPRENTOS/COREPAY
  Login screens (same `LoginContentHelper` is used everywhere).
- **EC-7** Login error message routing: non-SSO failures previously displayed
  `ssoLoginFailed` text by mistake; they now display `socialLoginFailed`. Verify
  on UZIO + every white-label that text routing is correct for both paths.

## Platform Notes
- **Android**
  - New flavor folder `android/app/src/nrspurple/` with `res/` (mipmaps,
    `strings.xml`, drawables) and a `nrspurple_app.keystore`.
  - `build.gradle` adds the NRSPURPLE product flavor, signing config, etc.
  - `gradle.properties` updated.
  - `google-services.json` added at the app level (push-notif / Firebase).
- **iOS**
  - New `ios/NrsPurple-Info.plist` with bundle id / display name "NRS Purple",
    URL schemes, Auth0 callback.
  - New shared xcscheme `NrsPurple.xcscheme`, new app-icon set
    `AppIcon-NrsPurple.appiconset` (sizes 16…1024).
  - New `nrspurple.entitlements`.
  - `Podfile` / `Podfile.lock` and `project.pbxproj` updated to wire the
    target.

## Out of Scope (covered elsewhere)
- Backend email-template HTML + Mobile URL config in NeuronDB → **PHIX-98187**.
- Auth0 PEM file for the mobile app in Phix SVN → **PHIX-98187**.
- NRS Purple QA SAML key file (rename / sync) → **PHIX-98187**.
- Jenkins mobile-build pipeline changes → **INFRA-127464**.
- Subdomain config + supporting-email HTML on `teamadmin` / prod →
  **INFRA-127465 / INFRA-127471**.
- Tenant public-key pre-deploy config on prod → **INFRA-127463**.
- Time Tracking invitation flow + Time Off request/approval workflow alignment
  with the standard white-label experience: the ticket description calls this
  out as a goal, but it is **server-side process alignment**. On the mobile
  app side it surfaces only as the standard Time Tracking + Time Off screens
  working end-to-end for NRS Purple users (covered by the existing sanity /
  regression suites once an NRS Purple test user exists).

## New locators needed (for `core/locators.py`)
NRS Purple flavor-specific strings the mobile-automation framework will need
when running against an NRS Purple build:

- `Login.HEADING_NRSPURPLE = "Welcome to NRS Purple"` (overrides
  `Login.HEADING = "Welcome to UZIO"`).
- `AboutUs.HEADING_NRSPURPLE = "About NRS Purple"`.
- `AboutUs.SUBHEADING_NRSPURPLE = "NRS Purple"`.
- `AboutUs.FOOTER_NRSPURPLE = "Copyright © 2026 National Retail Solutions, Inc. All Rights Reserved."`
- `Errors.UNAUTHORIZED_NRSPURPLE = "You are not authorized to access NRS Purple mobile application."`
- `Login.SOCIAL_LOGIN_FAILED = "Social login failed. Please try again"`
  (applies to every flavor — new shared string).
- Recommendation: introduce a flavor-aware helper (e.g.
  `flavor_strings.get(APP_NAME, 'login.heading')`) instead of hard-coding
  per-flavor constants, so future white-label launches don't require code
  changes in MobileAutoQA.

## Source commits (UzioMobile, master)
- `b2b4e07b` — primary NRS Purple flavor (assets, env, screens, locale)
- `422fc952` — strings.xml, app icon 100.png, pbxproj target wiring, Podfile.lock
- `f89705bd` — review fixes (NrsPurple-Info.plist tweaks)
- `3f75d05d` — `.env.nrspurple` / `.env.nrspurple.prod` adjustments
- Merged to release branch `PHIX_12.4.4.3` at
  `7790863a / 97ab6dd5 / 12a3368a / 37c90b22`.
