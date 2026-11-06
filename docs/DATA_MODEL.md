# Data model (M0)

```
Organisation --< User
Organisation --< Case (assigned_station)
Organisation --< UnidentifiedRecord (facility)

Subject --< Case --< CaseUpdate
                 --< Media
                 --< Tip
Case --< UnidentifiedRecord (matched_case, optional)
AuditLog (standalone, append-only)
```

**Subject vs Case.** A Subject is the person or pet. A Case is one report about
them. This lets one person have a missing report, then a found report, without
duplicating their description.

**Names.** First, middle and last names plus an `other_names` field for
aliases and spelling variants. Search (M1) matches across all of them.

**Skin tone.** A 1-10 swatch scale plus free text. The swatch scale removes
the ambiguity of words like "fair" or "dark" between people.

**Hospital records.** Every descriptive field is optional on purpose.

**Stale cases.** `last_police_update_at`, `stale_level` and `stale_flagged_at`
on Case. Thresholds live in `FINDR_STALE_DAYS` (settings): 3/7/14 days for
adults, 1/3/7 for children. Level 1 reminds the officer, level 2 notifies the
station commander, level 3 notifies the supervisor via `Organisation.parent`.
Only a police-authored, non-note update resets the clock.
