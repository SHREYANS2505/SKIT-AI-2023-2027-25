# Sprint 6 Review Notes

## Review scope
- Main landing page and registration UI asset presence.
- Dashboard and farmer profile UI asset presence.
- Flask route declarations for login, registration, dashboard, weather, mandi prices, and loan tracking.
- Template references to static assets.
- Duplicate routes and selected startup/configuration risks.
- Repeatable unit tests for the audit utility.

## Review procedure
1. Run `python3 -m unittest -v test_sprint6.py`.
2. Run `python3 sprint6_review.py <project-directory>`.
3. Investigate every `FAIL` before marking the relevant check complete.
4. Review every `WARN` manually and record whether it is a genuine issue or an intentional design.
5. Open the application in a local browser and test registration, login/logout, dashboard navigation, profile updates, weather/mandi views, and loan-date update with test data.
6. Do not use real farmer identity or financial details in test accounts.
7. Save the terminal output with the team's sprint review record.

## Important limitation
The utility performs static checks only. It does not submit forms, contact external APIs, mutate the SQLite database, or claim that the application has passed end-to-end testing. Browser testing and integration testing must be performed separately.
