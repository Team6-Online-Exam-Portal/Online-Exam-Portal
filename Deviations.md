# Deviations from the submitted documents

Every difference between what we built and what the SRS, SAD or Test Plan says goes here, with the reason.
Add a row the moment a deviation happens. These are explained at the final demo.

| # | Date | Document and section | What the document says | What we built | Reason | Owner |
|---|---|---|---|---|---|---|
| 1 | 2026-10-22 | SRS 4.2 and Appendix B (Attempt) | Attempt stores score only; FR-6 says score and percentage are stored | Added a `percentage` field to Attempt | Needed to store percentage once at submission, as FR-6 requires | Arati |
| 2 | 2026-10-22 | SAD 4.2 (sequence diagram 2) | Answers are sent only at final submit | Each answer is saved to the server when selected | Makes late-answer rejection testable and avoids losing answers if the tab closes | Prakash |
| 3 | 2026-10-22 | SRS / SAD (not described) | Nothing on abandoned attempts | Server finalizes and scores an expired In Progress attempt the next time it is accessed | Timer in the browser cannot fire if the tab is closed | Prakash |
| 4 | 2026-10-22 | SAD 4.3 vs Test Plan test data | Different URL styles | One unified URL map (see the sprint plan, section 8) | Keep code, SAD and Test Plan consistent | Darshana |
| 5 | 2026-10-22 | Folder structure plan | Separate Source-Code/Backend and Source-Code/Frontend | Single Django project in Source-Code/ with templates inside | Django serves the HTML, so there is no separate frontend app | Arati |
| 6 | 2026-10-23 | SRS Appendix B (Attempt) | Attempt has a stored `status` field | `status` is a computed property (In Progress until `submitted_at` is set) | One source of truth; a stored status could disagree with `submitted_at` | Prakash |
| 7 | 2026-10-23 | SRS 5.3 FR-5 (one attempt per exam) | A second start attempt is refused with a message | Refused once the attempt is submitted or its time is over. Starting again while the attempt is still running reopens that same attempt | Needed so a reload or closed tab does not lock the student out of their own running attempt. Still only one Attempt row (database unique constraint) | Prakash |
| 8 | 2026-10-23 | SAD 4.3 (API design) | Only start, submit and results endpoints listed | Added `POST /attempt/{id}/answer/` and `GET /exam/{id}/instructions/` | Supports deviation 2 (save on select) and the SRS instructions page | Prakash |
| 9 | 2026-10-23 | Scaffold (templates) | `templates/` folder at project level | Added it to `TEMPLATES['DIRS']`; Logout in `base.html` is now a POST form | The folder was not registered, so `base.html` and the custom 403 page were not found; logout view only accepts POST | Prakash |
