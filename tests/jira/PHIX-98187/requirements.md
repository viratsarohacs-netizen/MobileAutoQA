# PHIX-98187 — Requirements
# Source: Jira (fetched 2026-06-16)
# Type: User Story (sub-story — backend half of NRS Purple mobile launch)
# Status: Code Review · Priority: Major · Fix Versions: neuron-13.0, neuron-12.4.10
# Mobile screens (indirectly): Login, Time Tracking invitation, Time Off request/approval,
#                              email-link deep-links into the app

## Summary
This sub-story is the **server-side / configuration** half of the NRS Purple
white-label mobile launch. The mobile-app UI changes (logos, colours, About Us,
locale, login flavor wiring) are tracked in the parent story
[PHIX-86688](../PHIX-86688/requirements.md). Here the team:

1. Commits the Auth0 PEM file used by the NRS Purple mobile app (Phix SVN).
2. Updates platform email templates and the **Mobile URL** configuration in
   NeuronDB so Time Tracking invitations, Time Off request/approval emails,
   and other transactional emails deep-link into the NRS Purple mobile app
   (matching the standard white-label flow, e.g. TechServe 360).
3. Renames the NRS Purple QA SAML key file in Phix trunk to remove a trailing
   space that prevented sync on Windows / QA pickup.
4. Brings in any related Phix property / config changes through `int_branch`
   and `trunk` SVN revisions.

NRS Purple was previously a payroll-only client; the Time Tracking invitation
workflow, email notifications, and Time Off request/approval processes were
customized on the assumption employees would not use the UZIO mobile app.
Now that the mobile app is shipping for NRS Purple, those flows need to be
aligned with the standard white-label experience.

## Functional Requirements (server-side)
- **FR-1** Auth0 PEM file for the NRS Purple mobile app exists in the Phix
  SVN tree at the expected `*.pem` location and is picked up by the deployed
  Phix container (committed at SVN revision **329896** / completed at
  **329898** on `int_branch`).
- **FR-2** NeuronDB email templates referencing app deep-links / web fallbacks
  are updated for NRS Purple so the URLs point to the NRS Purple white-label
  domain (commits `88ecab27`, `6b60c3e4`, `084be646`, `3c09e86a`, `8f833ae4`,
  `449a9dd1`, `d8826048`, `42f9a2b4` across `neurondb/dev` and
  `neurondb/int_branch`).
- **FR-3** Mobile URL configuration (the deep-link / smart-banner URL the
  emails embed) is updated in NeuronDB so emails opened on a device with the
  NRS Purple app installed open the app, not the generic UZIO portal.
- **FR-4** NRS Purple QA SAML key file in Phix trunk is renamed to drop the
  trailing space in its filename. The trailing space was blocking sync on
  Windows machines and preventing the QA server from picking up the key
  (committed at trunk revision **329920**). After deploy, NRS Purple SAML
  login on QA must succeed.
- **FR-5** Phix property / config changes on `int_branch` and `trunk`
  (revisions **329922**, **329923**, **329924**) are deployed so the back-end
  recognises the NRS Purple mobile app context (e.g., subdomain → exchange
  mapping, mobile-supported flag).
- **FR-6** Time Tracking **invitation** workflow for NRS Purple matches the
  standard white-label experience (TechServe 360 reference): invitation
  emails include the mobile-app deep-link and the same body content other
  white-label clients receive.
- **FR-7** Time Off **request/approval** email notifications for NRS Purple
  match the standard white-label experience (same template, NRS Purple
  branding, mobile deep-link).

## UI Elements Affected (downstream of the backend changes)
- **Email body** (rendered in the user's mail client — not in the mobile app):
  NRS Purple branded header, mobile-app deep-link / "Open in app" CTA, web
  fallback URL pointing at the NRS Purple white-label domain.
- **Mobile Login** — succeeds against Auth0 + SAML with the corrected PEM
  and re-named QA SAML key.
- **Time Tracking invitation acceptance** — when a user taps the invitation
  link from email on a device with NRS Purple installed, they land on the
  correct Time Tracking onboarding screen in-app.
- **Time Off request submit / manager approval** — emails received contain
  the mobile-app deep-link to open the request inside NRS Purple.

## Acceptance Criteria
- **AC-1** A NRS Purple employee can log in to the NRS Purple mobile app on
  QA (post-deploy of trunk r329920) using SAML / SSO.
- **AC-2** On Time Tracking invitation for an NRS Purple employee, the
  invitation email body uses the standard white-label template and contains
  the NRS Purple mobile-app deep-link.
- **AC-3** When the employee taps the invitation link on a device with the
  NRS Purple app installed, the NRS Purple app opens to the Time Tracking
  onboarding flow (not the browser, not the UZIO app).
- **AC-4** A Time Off request submitted by an NRS Purple employee triggers
  the standard request-confirmation email; the manager receives the standard
  approval-required email. Both carry the NRS Purple mobile deep-link.
- **AC-5** When the manager taps the approval link, the NRS Purple mobile
  app opens to the pending Time Off request approval screen.
- **AC-6** No NeuronDB checksum errors after applying the migrations
  referenced in the comments (run `bash deploy_db.sh`).
- **AC-7** Auth0-based login (the Login.tsx path that POSTs to
  `Api.LOGIN` with the `subdomain` field) succeeds end-to-end on the
  NRS Purple flavor; the back-end accepts the PEM committed at SVN r329896.

## Edge Cases & Conditional Behavior
- **EC-1** SAML key file rename — if SVN clients on Windows had pulled the
  pre-rename file (with the trailing space), the file may persist locally
  after sync; deployers must verify the old filename is removed before
  restarting the container.
- **EC-2** Email deep-links — opening a NRS Purple email on a device without
  the NRS Purple app installed must fall back to the NRS Purple web portal
  URL (not the UZIO portal, not an empty page).
- **EC-3** Existing NRS Purple users invited under the **old** custom Time
  Tracking flow (pre-alignment) should not be re-invited; only **new**
  invitations should use the standard template. Confirm during regression
  that old data is unaffected.
- **EC-4** Time Off requests created before the template change must not
  be re-emailed.
- **EC-5** Mobile URL — if a user is opted out of the white-label mobile app
  (e.g., legacy NRS Purple user), the email should still render and the web
  link should still work, even if the deep-link is unusable.

## Platform Notes
- **Backend / NeuronDB** — migrations land on `dev` first, then
  `int_branch`. Liquibase/Flyway expect migrations applied in order; run
  `deploy_db.sh` (and `repair_db.sh` on checksum errors).
- **Phix (SVN)** — PEM file, SAML key file rename, and config changes are
  committed to `int_branch` and `trunk`. Deploy of `trunk` is the
  prerequisite for QA login validation.
- **Mobile app** — no Android or iOS code changes in this sub-story; the
  mobile work is in [PHIX-86688](../PHIX-86688/requirements.md).

## Out of Scope (covered elsewhere)
- All mobile-app branding, colour, login-flow, About Us, locale changes →
  **PHIX-86688**.
- Jenkins mobile-build pipeline changes for NRS Purple →
  **INFRA-127464**.
- Subdomain config + supporting-email HTML on `teamadmin` →
  **INFRA-127465**.
- Production subdomain config + supporting-email HTML →
  **INFRA-127471**.
- Production pre-deploy tenant public-key configuration → **INFRA-127463**.
- Original white-label exchange setup for NRS Purple → **PHIX-86686**.
- The link/redirect work for platform emails (Time Off, Time Tracking) shared
  with PHIX-98187 → **PHIX-86946**.

## New locators needed (for `core/locators.py`)
**None directly** — this sub-story is server-side. The mobile app's user-visible
strings are added by PHIX-86688 (see that requirements doc for the list of new
constants).

The MobileAutoQA suite **will** need an NRS Purple-aware Login flow once a
QA test user exists, but those locators are the same as PHIX-86688's. The
only artifact this sub-story produces on the QA side is **a working NRS
Purple test environment** (QA exchange + Auth0 tenant + SAML key + email
templates) — without it, no NRS Purple-flavor mobile test can run.

## Source commits (server-side)
- **Phix (SVN)** — Auth0 PEM file: revision **329896** (completed at
  **329898**, `int_branch`).
- **Phix (SVN)** — NRS Purple QA SAML key file rename: trunk revision
  **329920**.
- **Phix (SVN)** — `int_branch` revision **329922**; trunk **329923**;
  `int_branch` **329924** (related config).
- **NeuronDB (Git)** — email templates + Mobile URL:
  `88ecab27`, `6b60c3e4`, `084be646`, `3c09e86a` (dev / int_branch);
  `8f833ae4`, `449a9dd1`, `d8826048`, `42f9a2b4` (additional rounds).
- **NeuronDB (Git)** — earlier setup commits:
  `39d7461f` (master), `f3eeb369` (dev).

## QA hand-off checklist (for the rest of the pipeline)
1. After Phix `trunk` deploy on QA, re-check NRS Purple SAML login (per the
   comment by Birajpal — QA was previously blocked by the trailing-space
   filename).
2. Confirm `deploy_db.sh` ran cleanly against QA NeuronDB (no checksum
   errors).
3. Provision (or confirm) an NRS Purple QA employee and manager so the
   PHIX-86688 mobile-flavor tests can run end-to-end.
4. With those prerequisites in place, the existing **Sanity** and **Time
   Off** / **Time Tracking** suites in MobileAutoQA can be re-run against
   an NRS Purple build to satisfy AC-1 through AC-7 above.
