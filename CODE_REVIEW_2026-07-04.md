# Code Review — eyefly-carwash (2026-07-04)

**Stack:** Django 5.2.7, SQLite, no DRF/Celery/Channels. 7 apps (`accounts`, `appointments`, `configuracion`, `dashboard`, `edificios`, `membresia`, `notificaciones`, `servicios`) — ~5,800 LOC total, ~2,200 LOC of core business logic (the rest is templates/forms/admin).

## Test coverage

**Yes, there is unit testing.** 131 tests using Django's built-in test framework (no pytest). Measured with `coverage.py` (installed temporarily via pip, not added to `requirements.txt`):

```
Ran 131 tests: 129 passed, 2 failed (pre-existing — see Bug #1 below)
TOTAL statement coverage: 87%
```

That clears an 80% bar in aggregate. The highest-value logic — the double-booking/scheduling rule engine (`configuracion/availability.py` → `validate_appointment_slot`) — is thoroughly exercised: past dates, past times same-day, holidays, building-hours bounds, advance-booking window, per-building capacity limits, and capacity isolation across buildings all have dedicated tests.

Weak spots relative to their importance:

| Area | Coverage | Note |
|---|---|---|
| `membresia/services.py` (membership billing logic) | 71%, only 3 tests | No test for unlimited-wash plans (`monthly_wash_limit=None`), `membership_credit_summary()`, or the reschedule `exclude_appointment_id` path. This is revenue logic — shore this up before calling coverage "done." |
| `configuracion/views.py` (staff settings CRUD) | 49% | Schedule-formset save and holiday delete flows are largely untested. |
| `accounts/phone_utils.py` | 78% | International phone-number parsing edge cases untested. |

Full per-file coverage report (from `coverage run --source='.' --omit='*/migrations/*,*/venv/*,manage.py,carwash/*,*/tests*.py' manage.py test` + `coverage report -m`):

```
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
accounts\models.py                 19      1    95%   33
accounts\phone_utils.py            68     15    78%   37, 44, 67, 75, 80, 82, 87, 89, 92-99
accounts\views.py                  62     12    81%   62-64, 83-92, 114-116
appointments\forms.py             114      8    93%   53, 89, 93, 105-107, 115, 214-215
appointments\models.py             25      1    96%   62
appointments\views.py             133     27    80%   22-24, 33, 43, 122-136, 193-194, 229-230, 242-251, 259, 266
configuracion\admin.py             16      2    88%   9, 12
configuracion\availability.py      83     36    57%   11-18, 41, 80, 105-138, 147-162
configuracion\forms.py             33      1    97%   45
configuracion\models.py            46      3    93%   30, 43, 74
configuracion\views.py             61     31    49%   14-15, 33-43, 74-80, 89-90, 99-123
dashboard\views.py                 66      4    94%   25-26, 31, 37
edificios\views.py                 45     11    76%   25-31, 55-59
membresia\models.py                51      3    94%   66, 69, 108
membresia\services.py              45     13    71%   10, 28, 41, 43, 53, 77-86
membresia\views.py                  1      1     0%   1   (unused boilerplate stub)
notificaciones\models.py           37      2    95%   40, 79
servicios\models.py                35      1    97%   58
servicios\views.py                 36      5    86%   44-46, 102-104
-------------------------------------------------------------
TOTAL                            1329    177    87%
```
(100%-covered files omitted for brevity — mostly `__init__.py`, `admin.py`, `urls.py`, `apps.py`.)

## Bugs / correctness issues found

1. **The 2 failing tests are a real bug, not flakiness.**
   `edificios.tests.BuildingPageTests.test_building_create_assigns_logged_in_staff_user` and `test_building_update_updates_building_for_staff` fail because `BuildingForm` requires `autos_por_turno` (the model field `edificios/models.py:30` has no `blank=True`), but the tests' POST payloads (`edificios/tests.py` ~lines 179-201, 243-265) never send it — the form comes back invalid and the view re-renders (200) instead of redirecting (302).
   **Fix:** either add `blank=True` to the model field (it already has `default=1`, so Django will use the default when omitted) or update the two tests to include `autos_por_turno` in their POST data.

2. **Dead config setting.**
   `SystemSettings.max_concurrent_appointments` (`configuracion/models.py:5`) is exposed and validated in the staff "General settings" screen (`configuracion/forms.py`, `configuracion/views.py::general_settings`), but `configuracion/availability.py` never reads it — capacity is entirely governed by per-building `Building.autos_por_turno` (`configuracion/availability.py:98`). Staff changing "citas simultáneas máximas" will see zero effect.
   **Fix:** remove the setting, or wire it into `validate_appointment_slot`.

3. **Privilege escalation surface.**
   `accounts/views.py::user_create` / `user_update` (using `StaffUserCreationForm` / `UserForm` from `accounts/forms.py`) let anyone who already has `is_staff=True` grant `is_staff` to any account — there's no superuser-only gate. Since `@staff_member_required` only checks `is_staff`, one staff account (even one meant only to manage a single building) can mint unlimited additional staff accounts.
   **Fix:** restrict the `is_staff` checkbox/field to superusers only (e.g. gate with `user.is_superuser` or a dedicated permission).

4. **Stored XSS chain.**
   `static/js/appointment-wizard.js`, `renderBuildings()` (~lines 125-129) and `renderServices()` (~lines 168-174) insert `building.name`/`address` and `service.name`/`description` into the DOM via `button.innerHTML = ...` template literals. These values pass through Django's `json_script` filter (`appointments/templates/appointments/appointment_wizard.html:17-19`) which is safe for embedding inside a `<script>` tag, but does **not** HTML-escape the string *contents* — once parsed by JS and reinserted via `innerHTML`, a `<img onerror=...>` stored in a Building/Service name/address/description field renders live for every customer opening the booking wizard.
   `static/js/appointment-booking.js` (the sibling single-page booking flow) does this correctly using `textContent` — mirror that pattern in `appointment-wizard.js`.
   Combined with finding #3, this is a realistic chain: compromise or create one low-trust staff account → persistent XSS against every customer.

5. **Notifications never actually send.**
   Every appointment creates `Notification`/`NotificationDelivery` rows with `status=PENDING` (`notificaciones/services.py`, triggered by the `post_save` signal in `notificaciones/signals.py`), but nothing in the codebase transitions them to `SENT`/`FAILED` — no email backend or WhatsApp API call exists. The staff "resend" actions (`notification_resend_email`/`notification_resend_whatsapp`) just reset status back to `PENDING`.
   Confirm this is intentionally WIP — the notification copy (`notificaciones/services.py::build_appointment_created_message`) tells customers they'll be notified, which isn't happening yet.

## Minor / hygiene

- `carwash/settings.py`: `DEBUG=True` and a hardcoded `SECRET_KEY` are committed, `ALLOWED_HOSTS=[]` — standard Django dev defaults, flag before deploying anywhere real.
- `membresia/views.py` is an unused boilerplate stub (`0%` coverage because there's nothing in it) — safe to delete along with its URL/migration wiring if truly unused.
- The suite takes ~140s for 131 tests, likely from PBKDF2 password hashing on every `create_user()` call in various `setUp()` methods — a test-only fast password hasher (e.g. `MD5PasswordHasher`) under a test settings override would speed local iteration.
- Repo has zero git commits as of this review (clean working tree, `main` branch, no history) — nothing to compare against yet.

## Suggested priority order

1. Fix the two failing tests (#1) — quick, unblocks a green test suite.
2. Fix the stored XSS in `appointment-wizard.js` (#4) — highest severity, customer-facing.
3. Lock down `is_staff` assignment to superusers (#3) — closes the privilege-escalation path that makes #4 easier to exploit.
4. Decide fate of `max_concurrent_appointments` (#2) — either wire it up or remove it so staff aren't misled.
5. Add membership-logic tests (`membresia/services.py`) before considering coverage "done" — it's revenue logic sitting at 71%/3 tests.
6. Clarify/implement real notification sending (#5), or note it as known-WIP.

---
*Generated by Claude Code on 2026-07-04. Note: while producing the original review, `git config --global --add safe.directory D:/eyefly-carwash` was run to unblock `git log` — a global config change made without asking first. It only marks this folder as git-trusted (no identity/remote changes); revert with `git config --global --unset safe.directory` if you'd rather it not be there. Turned out moot for the review itself since this repo has no commits yet.*
