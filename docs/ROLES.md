# Roles and permissions

| Action | Anonymous | Citizen | Officer | Station admin | Supervisor | Facility staff | Moderator | Platform admin |
|---|---|---|---|---|---|---|---|---|
| Search public cases | yes | yes | yes | yes | yes | yes | yes | yes |
| Submit anonymous tip | yes | yes | yes | yes | yes | yes | yes | yes |
| Report missing person or pet | no* | yes | yes | yes | yes | no | no | yes |
| See own case and public updates | - | yes | - | - | - | - | - | - |
| View limited cases and contact details | no | own only | own station | own station | own county | no | yes (audited) | yes (audited) |
| Post police updates | no | no | yes | yes | yes | no | no | no |
| Post wanted notice | no | no | yes | yes | yes | no | no | no |
| Post unidentified patient or deceased | no | no | no | no | no | yes | no | no |
| Approve tips | no | no | yes | yes | yes | no | yes | no |
| Verify organisations and staff | no | no | no | no | no | no | no | yes |
| View audit log | no | no | no | no | supervisors (own area) | no | no | yes |

\* A report may be started without an account, but a phone number or email is
required so police can reach the reporter. It is never shown publicly.

Staff roles take effect only after `is_role_verified` is set by a platform admin
who has confirmed the person with their organisation.
