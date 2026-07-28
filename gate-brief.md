You are the GATE. Adversarially review this DESIGN: /home/svarkor/svarkor-builds/bibliotek/DESIGN.md

Check specifically:
1. Is every module one concern? Is anything here already implemented on the fleet we should extend?
2. Are the acceptance criteria actually checkable by a tool?
3. What is MISSING that this build will discover too late?
4. Is the SQLite choice appropriate for this use case?
5. Is the JWT auth pattern correct (cookie vs bearer)?
6. Are the API routes complete and non-overlapping?
7. Is the HCF classification heuristic sound, or will it fail?
8. Is the Libris API integration correct (is the endpoint actually real)?

Try to REFUTE the design. Report SHIP / FIX / RECONSIDER with concrete evidence.
If you find issues, list them as actionable items.

--- RESULT ---
STATUS: | BLOCKED
FILES: paths created/modified, one per line
DID: what you did, <=4 lines
VERIFY: the check you ran + its outcome
BLOCKERS: concrete blocker, or "none"
--- END ---
