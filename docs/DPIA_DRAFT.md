# Data Protection Impact Assessment - DRAFT (M0)

*Starting point only. A DPIA must be completed before processing begins and
reviewed by qualified counsel. See Section 31 of the Data Protection Act, 2019,
and the ODPC's guidance notes on biometric data.*

## 1. Description of processing
| Item | Entry |
|---|---|
| Purpose | Help families, hospitals and police find missing or unidentified people and pets |
| Data subjects | Missing persons (including children), reporters, tippers, patients, deceased persons, wanted persons named by police |
| Data categories | Names, age, physical description, photos, location, contact details, health-related details; face templates from M5 |
| Sensitive data | Photos used for biometric matching, health data, data about children |
| Recipients | Public (limited fields), police, verified hospitals/mortuaries |
| Retention | [To be set per category] |
| Lawful basis | Consent (reporter); vital interests; public task for police-originated data [confirm] |

## 2. Necessity and proportionality
- **Waiting periods:** none; this reduces harm.
- **Minimisation:** public listings omit contact details, exact home address and
  medical details.
- **Biometrics:** off by default; only on images with consent_for_matching
  (M5). Camera-based matching (M7) requires a formal police or Interior Ministry
  agreement, a separate DPIA and ODPC registration.

## 3. Risk register
| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| Malicious report to locate or harass a person (for example an abuser looking for a victim who fled) | Medium | High | Police review before publication; option to limit visibility; flag reports where the "missing" person is an adult who may have left voluntarily; adults can be asked to confirm they wish to be found |
| False or hostile anonymous tips | High | Medium | Moderation queue; rate limits; tips go to police, not the public |
| Defamation via wanted notices | Medium | High | Wanted notices police-only, OB number required, takedown path |
| Face-match false positive harms an innocent person | Medium | High | Matches are leads for human review, shown with confidence, never auto-actioned; bias testing across skin tones before any deployment |
| Data breach of children's or deceased persons' data | Low-Med | High | Encryption at rest and in transit, role-based access, audit logging, minimal retention |
| Misuse by staff | Medium | High | Verified roles, audit log, periodic access review |
| Function creep (mass surveillance) | Medium | High | Watchlists limited to approved cases; documented purpose; independent review |
| Deceased person's photo shown to public | Medium | Medium | Photos not public by default; released to verified police or family |

## 4. Open items
- [ ] Appoint a data protection officer
- [ ] Register with ODPC
- [ ] Set retention periods
- [ ] Confirm lawful basis for each category
- [ ] Written agreement with police before any official use
- [ ] Legal review of this document and the privacy notice
