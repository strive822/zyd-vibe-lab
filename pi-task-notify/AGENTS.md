# pi-task-notify

Pi coding-agent extension that sends Windows notifications when a Pi task
finishes, fails, waits for confirmation, or emits a heartbeat.

There is no standalone test suite. Verify through the documented flow in
INSTALL.md (Release ZIP or source checkout, `pi -e` trial or
`pi install <path>`, then `/notify` and `/notify-test`). Never claim
notifications appeared on screen without the user confirming it.

Boundaries: do not modify the user's Pi configuration beyond the documented
install; never include real account data in notifications. Build host-loadable
extension packages outside the checkout using root scripts/package_projects.py;
upload programs and checksums to Release, not delivery archives to Git.
