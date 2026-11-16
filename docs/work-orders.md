# Work orders (technician visits)

## Customers may say
"Send a technician", "when is my technician coming?", "my dish is not aligned", "I want a new remote".

## Types
- no_signal: the TV shows no signal
- stb_upgrade: set-top box upgrade
- dish_alignment: the dish needs to be aligned again
- remote_replacement: the remote needs to be replaced

## Statuses
- unscheduled: the request is created, but no time slot is fixed yet
- scheduled: a technician time slot is fixed
- completed: the visit is done
- cancelled: the visit was cancelled

Unscheduled and scheduled work orders are called open.

## Rules
- A suspended connection cannot get a new work order. Explain the suspension first.
- A customer cannot have two open work orders for the same issue type. Tell them about the existing one.
- A completed or cancelled work order does not block a new one.
- For no signal, try the no-signal steps first (check the cables and refresh the account).

## What to tell the customer
- Unscheduled: the request is created, but a time slot has not been fixed yet.
- Scheduled: give the date and time slot from the work order.