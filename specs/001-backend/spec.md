# Feature Specification: VeritX Vision backend v1

**Feature Branch**: `claude/backend-spec`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "Backend for the VeritX Vision website (issues #2, #3, #8, #10): real email for the contact form and calculator results, real meeting booking against the owner's calendar, invite-only customer accounts with Vision Home, and support tickets with small attachments. Decisions settled in a grill-me interview with the owner."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Contact requests and calculator results actually arrive (Priority: P1)

A visitor sends the contact form (or asks the ROI calculator to "send me these results"). Today
nothing is sent. After this story, VeritX staff receive every request in their inbox, the
request is kept on record, and the visitor receives a confirmation (or their calculator results)
in the language they were using on the site.

**Why this priority**: Every lead is currently lost. It is the smallest story and needs no
accounts, so it delivers value first.

**Independent Test**: Submit the contact form and the calculator "send results" panel on the
deployed site; staff inbox receives the request and the visitor inbox receives the confirmation
or results.

**Acceptance Scenarios**:

1. **Given** a visitor filled the contact form with valid data, **When** they submit, **Then** staff receive an email with every field, the request is stored, and the visitor receives a confirmation email in the site language (es/en/fr).
2. **Given** a visitor on the calculator page entered values and an email, **When** they ask to send the results, **Then** the visitor receives an email with their inputs and each section's savings and the total, in the currency and language they used, and staff receive a copy.
3. **Given** a submission with an invalid email or missing required fields, **When** they submit, **Then** nothing is sent and the form shows which fields to fix.
4. **Given** an automated bot fills the hidden trap field, **When** it submits, **Then** the request is silently discarded (the bot sees a normal success).
5. **Given** the email service is temporarily failing, **When** a visitor submits, **Then** the request is still stored and staff can still see it, and the visitor sees a success message (no lost lead).

---

### User Story 2 - Real meeting booking without double-booking (Priority: P2)

A visitor picks "Schedule a meeting" in the contact form. The existing calendar picker only offers
slots that are actually free in VeritX's calendar. Booking creates the meeting in that calendar
with a video-call link and invites the visitor.

**Why this priority**: Prevents the visible failure of two visitors booking the same slot and
removes manual calendar work. Needs no accounts.

**Independent Test**: Block a time in the VeritX calendar; confirm it disappears from the picker.
Book a free slot; confirm the event with a video link appears in the calendar and the visitor gets
the invitation.

**Acceptance Scenarios**:

1. **Given** the VeritX calendar has an event on Tuesday 10:00–11:00 CDMX, **When** a visitor opens Tuesday in the picker, **Then** 10:00 is not offered and the other slots are.
2. **Given** a free slot, **When** the visitor books it, **Then** a 1-hour event with a video-call link is created in the VeritX calendar, the visitor receives the invitation, and staff receive a booking email.
3. **Given** two visitors select the same free slot, **When** both submit, **Then** exactly one booking succeeds and the other is told the slot is no longer available and shown the remaining free slots.
4. **Given** the calendar cannot be reached, **When** a visitor opens the picker, **Then** the picker says live booking is unavailable and offers to send the request as a normal contact message instead.

---

### User Story 3 - Invite-only customer accounts and Vision Home (Priority: P3)

VeritX staff invite people from customer companies. An invited person sets a password from the
emailed link, signs in with their email, and sees their company's subscriptions and payment
history in Vision Home. Several people from one company each have their own sign-in and see the
same company data.

**Why this priority**: The largest and most security-sensitive story; it replaces the simulated
portal, which today must not be presented as real.

**Independent Test**: Staff invite a test person to a test company with one subscription and one
payment; the person accepts the invite, signs in, sees that data, signs out, and resets their
password.

**Acceptance Scenarios**:

1. **Given** staff invite `ana@example.com` to company "Textiles Ruiz", **When** Ana opens the emailed link within 7 days and sets a valid password, **Then** she is signed in and sees Vision Home for Textiles Ruiz.
2. **Given** an invite link that was already used or is older than 7 days, **When** it is opened, **Then** it is rejected with a message to ask VeritX for a new invite.
3. **Given** two users of the same company, **When** each signs in, **Then** both see the same subscriptions, payments and tickets, and neither sees another company's data.
4. **Given** a wrong password or unknown email, **When** someone signs in, **Then** the same generic error is shown in both cases.
5. **Given** 5 failed sign-ins for one account within 15 minutes, **When** a 6th is attempted, **Then** sign-in for that account is temporarily blocked, even with the right password, and the user is told to wait.
6. **Given** a user requests a password reset, **When** they open the link within 30 minutes and set a new password, **Then** the password changes, the link stops working, and all their other sessions are signed out. The reset request shows the same confirmation whether or not the email has an account.
7. **Given** a signed-in user signs out, **When** they press back or reopen Vision Home, **Then** they are asked to sign in again.
8. **Given** the public site, **When** anyone looks for a way to create an account, **Then** there is none: the register page, the username-recovery page and the demo login are gone, and the sign-in page explains accounts are by invitation.
9. **Given** staff disable a user, **When** that user next does anything signed in, **Then** they are signed out and cannot sign in again.

---

### User Story 4 - Support tickets with small attachments (Priority: P4)

A signed-in customer opens a support ticket from Vision Home, optionally attaching screenshots or
PDFs. Staff are notified by email and reply from their inbox. The ticket and its status are
visible to everyone in the customer's company.

**Why this priority**: Depends on Story 3 (accounts). Completes the portal.

**Independent Test**: Signed in as a test user, open a ticket with one PNG; staff inbox receives
it with the attachment; staff change its status; the user sees the new status in Vision Home.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they submit a ticket with subject, description, priority and up to 3 PNG/JPEG/PDF files of at most 2 MB each, **Then** the ticket is stored with status "open", staff receive an email with the details and files, and the user's reply-to address is the user's email.
2. **Given** a file over 2 MB, a 4th file, or a file whose content is not really PNG/JPEG/PDF (e.g. a renamed .exe), **When** the user submits, **Then** the ticket is not created and the form says which file is rejected and why.
3. **Given** staff mark a ticket "resolved", **When** any user of that company opens Vision Home, **Then** the ticket shows "resolved".
4. **Given** a user of another company, **When** they try to open the ticket or its attachments, **Then** they are refused as if it did not exist.

---

### Edge Cases

- Visitor's browser is in another time zone: slots are always shown and booked in Mexico City time, as today.
- Slot in the past or less than 24 hours ahead: not offered.
- Visitor prefers Zoom/Teams/WhatsApp (existing form field): the event still gets the default video-call link; the preference is recorded for staff, who may send another link.
- Daily sending limit of the Gmail account is reached: submissions are still stored; staff can list unsent notifications and re-send them; the event is logged.
- The Google authorization expires or is revoked: email and booking fail visibly in staff logs, public forms still store requests, and the picker falls back as in Story 2 scenario 4.
- Invite sent to an email that already has an account: the existing account is not changed; staff are told.
- User belongs to a company that has no subscriptions or payments yet: Vision Home shows an empty state, not an error.
- Many submissions from one network address in a short time: further submissions are refused for a while with a "try again later" message.
- Password manager or user pastes leading/trailing spaces into the email: the email is trimmed and compared case-insensitively.

## Requirements *(mandatory)*

### Functional Requirements

**Public forms (Story 1)**

- **FR-001**: System MUST store every valid contact request and calculator "send results" request with its submission time and site language.
- **FR-002**: System MUST email staff each stored request and email the visitor a confirmation (contact) or their results (calculator), in the visitor's site language (es/en/fr).
- **FR-003**: System MUST validate required fields and email format on the server and return field-level errors.
- **FR-004**: System MUST silently discard submissions that fill the hidden trap field.
- **FR-005**: System MUST limit submissions per network address (default: 5 per 10 minutes) and refuse excess with a "try again later" message.
- **FR-006**: System MUST keep a request stored even if sending its emails fails, record the failure, and let staff re-send pending notifications.

**Booking (Story 2)**

- **FR-007**: System MUST offer only slots that are free in the VeritX calendar, using the existing slot grid (Mon–Fri; 09:00, 10:00, 11:00, 12:00, 13:00, 16:00, 17:00 Mexico City time; 1-hour meetings), at least 24 hours ahead and at most 60 days ahead.
- **FR-008**: System MUST create the calendar event with a video-call link and the visitor as invitee when a booking succeeds, and email staff.
- **FR-009**: System MUST guarantee at most one booking per slot, even under simultaneous requests, and tell the losing visitor the slot is gone.
- **FR-010**: System MUST let the visitor fall back to a normal contact request when the calendar is unavailable.

**Accounts (Story 3)**

- **FR-011**: System MUST model companies and users; each user belongs to exactly one company; a company can have many users.
- **FR-012**: Staff MUST be able to, from a command-line tool: create companies, invite users, disable users, and add/edit a company's subscriptions and payments.
- **FR-013**: System MUST send invite links valid for 7 days and usable once; accepting one sets the user's password and signs them in.
- **FR-014**: Users MUST sign in with email + password; email is the only identifier (no usernames).
- **FR-015**: System MUST enforce passwords of at least 12 characters that are not on a common-password list.
- **FR-016**: System MUST store passwords only as slow, salted hashes designed for passwords.
- **FR-017**: System MUST keep sign-in sessions on the server and identify them with a cookie the page's scripts cannot read, sent only over HTTPS; sessions expire after 7 days or 24 hours of inactivity, whichever is first.
- **FR-018**: System MUST show the same error for unknown email and wrong password, and the same confirmation for password-reset requests whether or not the email exists.
- **FR-019**: System MUST block sign-in for an account after 5 failures in 15 minutes for 15 minutes, and limit reset requests per email and per network address.
- **FR-020**: System MUST send password-reset links valid for 30 minutes and usable once; a successful reset ends all the user's other sessions.
- **FR-021**: Vision Home MUST show the signed-in user's company subscriptions (name, status) and payments (date, amount, currency) as entered by staff, with an empty state when there are none.
- **FR-022**: System MUST never return one company's data to a user of another company.
- **FR-023**: System MUST record an audit entry for sign-in success/failure, sign-out, invite sent/accepted, reset requested/completed, and user disabled, with time, user/email and network address.
- **FR-024**: The site MUST remove the self-registration page, the username-recovery page and the development demo login, and explain on the sign-in page that accounts are by invitation.

**Tickets (Story 4)**

- **FR-025**: Signed-in users MUST be able to create tickets with subject, description, priority (low/medium/high) and up to 3 attachments.
- **FR-026**: System MUST accept only PNG, JPEG and PDF attachments of at most 2 MB each, judged by file content, not just name.
- **FR-027**: System MUST email staff each new ticket with its attachments, with the user's email as reply-to.
- **FR-028**: Staff MUST be able to change a ticket's status (open, in progress, resolved, closed) from the command-line tool.
- **FR-029**: Vision Home MUST list the company's tickets with subject, date, priority and status, and let company users download their attachments.

**Cross-cutting**

- **FR-030**: All credentials and keys MUST come from the hosting environment's configuration, never from the repository.
- **FR-031**: The site MUST keep working as a marketing site (all pages render) if the backend is down; forms show a clear "could not send, please try again or use WhatsApp" message.

### Key Entities

- **Company**: A customer organization. Name; has users, subscriptions, payments, tickets.
- **User**: A person at a company. Email (unique, the sign-in identifier), name, password hash, status (invited, active, disabled), preferred language.
- **Invite / Reset link**: Single-use, expiring link tied to a user; only a non-reversible form of the link secret is stored.
- **Session**: A signed-in browser for a user; created at sign-in, ended by sign-out, expiry, reset or disable.
- **Subscription**: A product line a company pays for (e.g. "Vision A — Final Inspection Line"), with status.
- **Payment**: A recorded payment for a company: date, amount, currency. Entered by staff; display only.
- **Ticket**: A support request from a user on behalf of their company: subject, description, priority, status, timestamps.
- **Attachment**: A file on a ticket: name, type, size, content.
- **Contact request**: A public form submission (contact message, meeting request, or calculator results) with language, payload, and notification status.
- **Booking**: A reserved slot: start time, visitor contact, link to its calendar event; at most one per slot.
- **Audit entry**: A security-relevant event: time, kind, user/email, network address.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid contact, calculator and booking submissions are stored, and at least 99% reach the staff inbox within 2 minutes.
- **SC-002**: Zero double-booked slots over the first 3 months.
- **SC-003**: A visitor can book a meeting in under 2 minutes from opening the form.
- **SC-004**: An invited user can go from opening the invite email to seeing Vision Home in under 3 minutes.
- **SC-005**: No user can see another company's data, verified by automated checks on every change.
- **SC-006**: Every sign-in, invite and reset event in a test run appears in the audit record.
- **SC-007**: The marketing pages stay available when the backend is down.
- **SC-008**: Staff can perform every admin task in FR-012 and FR-028 without editing data by hand.

## Assumptions

- Low volume: tens of submissions per day and fewer than 100 portal users; the personal Gmail account's limit (~500 emails/day) is enough for v1.
- VeritX has no domain yet; the site stays on its current hosting address and the API is reached through the same address, so sign-in cookies are first-party.
- One personal Google account owns the meeting calendar and sends all emails; staff read and reply from that inbox.
- Meetings are 1 hour, in the existing slot grid; the slot grid and booking window (24 h–60 days) can be changed later by configuration.
- Staff replies to tickets happen by email; the portal shows ticket status, not the conversation.
- Existing data in visitors' browsers from the simulated portal is discarded; no migration.
- Payments are recorded after offline invoicing; no online payment, tax documents or billing in v1.
- The portal pages keep the current design and three languages; new copy is added in es/en/fr.
- Non-goals: admin web interface, self-registration, online payments, attachments over 2 MB or video, staff replies inside the portal, own domain and branded email.
