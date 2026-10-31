# Data model: VeritX Vision backend v1

Postgres. All tables have `id` (bigint identity) and `created_at` (timestamptz, default now()).
Emails are stored trimmed and lower-cased.

## companies
| Field | Type | Rules |
|---|---|---|
| name | text | required, unique |

## users
| Field | Type | Rules |
|---|---|---|
| company_id | → companies | required |
| email | text | required, unique, lower-case |
| name | text | required |
| password_hash | text | null until invite accepted |
| status | enum `invited` \| `active` \| `disabled` | default `invited` |
| lang | enum `es` \| `en` \| `fr` | default `es`; language of emails |

State: `invited` → (accept invite) → `active` → (staff disable) → `disabled` → (staff enable) → `active`.
Disabling deletes the user's sessions.

## tokens
Invite and reset links.
| Field | Type | Rules |
|---|---|---|
| user_id | → users | required |
| kind | enum `invite` \| `reset` | |
| token_hash | text | SHA-256 of the link secret, unique |
| expires_at | timestamptz | invite +7 d, reset +30 min |
| used_at | timestamptz | null until used; a used or expired token is rejected |

Creating a new token of a kind invalidates (marks used) earlier unused ones for that user.

## sessions
| Field | Type | Rules |
|---|---|---|
| user_id | → users | required |
| token_hash | text | SHA-256 of cookie value, unique |
| expires_at | timestamptz | created +7 d |
| last_seen_at | timestamptz | session invalid if older than 24 h |

Deleted on logout, password reset (all of the user's), and disable.

## subscriptions
| Field | Type | Rules |
|---|---|---|
| company_id | → companies | required |
| name | text | required |
| status | enum `active` \| `paused` \| `cancelled` | |

## payments
| Field | Type | Rules |
|---|---|---|
| company_id | → companies | required |
| paid_on | date | required |
| amount | numeric(12,2) | > 0 |
| currency | char(3) | ISO 4217, e.g. MXN, USD |

## tickets
| Field | Type | Rules |
|---|---|---|
| company_id | → companies | required (copied from user) |
| user_id | → users | author |
| subject | text | 1–200 chars |
| description | text | 1–5000 chars |
| priority | enum `low` \| `medium` \| `high` | |
| status | enum `open` \| `in_progress` \| `resolved` \| `closed` | default `open`; staff change it |
| notification_status | enum `pending` \| `sent` \| `failed` | |
| updated_at | timestamptz | |

## attachments
| Field | Type | Rules |
|---|---|---|
| user_id | → users | uploader |
| ticket_id | → tickets | null until linked; max 3 per ticket |
| filename | text | sanitized, ≤255 chars |
| content_type | enum `image/png` \| `image/jpeg` \| `application/pdf` | from magic bytes |
| size | int | 1 – 2 097 152 |
| content | bytea | |

## contact_requests
| Field | Type | Rules |
|---|---|---|
| kind | enum `message` \| `meeting` \| `calculator` | |
| lang | enum `es` \| `en` \| `fr` | |
| email | text | required, valid |
| payload | jsonb | form fields (validated per kind, see contracts/api.md) |
| ip | inet | for rate limiting |
| notification_status | enum `pending` \| `sent` \| `failed` | |

## bookings
| Field | Type | Rules |
|---|---|---|
| contact_request_id | → contact_requests | the meeting request |
| slot_start | timestamptz | **unique**; on the slot grid |
| calendar_event_id | text | Google event id |

## audit_log
| Field | Type | Rules |
|---|---|---|
| kind | enum `login_ok` \| `login_failed` \| `logout` \| `invite_sent` \| `invite_accepted` \| `reset_requested` \| `reset_done` \| `user_disabled` \| `user_enabled` | |
| user_id | → users | nullable (unknown email) |
| email | text | as entered |
| ip | inet | |

Indexes: `audit_log (email, kind, created_at)`, `audit_log (ip, kind, created_at)`,
`contact_requests (ip, created_at)` — used for the rate limits (research R6).

## Tenant isolation rule
Every portal query filters by the signed-in user's `company_id`; a record of another company is
answered as 404, never 403 (FR-022, scenario 4.4).
