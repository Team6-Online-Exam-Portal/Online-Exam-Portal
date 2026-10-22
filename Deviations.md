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
