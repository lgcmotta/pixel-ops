# 0036 - Windows desktop lifecycle is per-user

Status: Accepted

## Context

The Lian Li is a Windows desktop display. Its runtime should stay out of the
taskbar, offer explicit Studio/display controls, and launch at user sign-in.
The owner wants to register scheduled tasks personally using PowerShell Core.

## Decision

Add a Windows-only desktop controller, separate from integrations and game
engines. A pystray host owns the notification-area icon and delegates commands
to the same controller used by `tools/windows/PixelOps.ps1`.

Open Config Studio reuses an existing repo-local server. Otherwise it starts
the registered Studio task, or launches directly if not registered, waits for
the local API, and opens the browser. Stop Config Studio stops that server and
its helpers while protecting the display subtree. Existing browser tabs remain
open. Restart display replaces only the display process. Exit stops Studio,
the display, and the tray host without removing startup registrations.

Background processes use windowless Python and bounded process checks. A
repo-local file lock serializes controls; state records PID and creation time.
Adoption requires the expected command and repository location. Stops never
target all Python or Node processes. The controller stores state in the ignored
cache directory and logs under `pixel_ops/output/`.

Tray launches set `PIXEL_OPS_TRAY=1`. Window output uses WS_EX_TOOLWINDOW and
removes WS_EX_APPWINDOW after each creation, including hot reload. The LCD stays
visible. Ordinary preview windows retain their taskbar entry. The tray host
reopens a pre-existing display once to enable this mode. The shell controls
whether the tray icon is visible beside the clock or in its overflow.

`Register-PixelOpsTasks.ps1` provides a read-only `-WhatIf` preview. Actual
registration is left to the owner. Tasks run with the current user's interactive
token and limited privileges, without saved passwords. Desktop starts at sign-in;
Studio is on demand unless `-StudioAtLogon` is supplied. Both tasks run until their
component exits and ignore duplicate triggers. Uninstall removes registrations
without stopping live components. No Windows service is installed.

## Consequences

The display requires a signed-in desktop session. Studio can be stopped without
stopping telemetry, account queries, PR collection, or JSON hot reload. Its
server must run again to use the browser UI. The current Vite server binds only
to 127.0.0.1:5174. PowerShell Core, Node dependencies and Python requirements
must be installed before enabling tasks. Existing Studio Startup-folder
autostart should be disabled before enabling the new desktop task.
