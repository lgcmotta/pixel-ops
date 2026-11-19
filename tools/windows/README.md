# Windows tray and scheduled tasks

Run these commands in **PowerShell Core 7**, from the repository root. Install
`requirements.txt` in `.venv` and run `npm ci` in `config-studio` first.
These scripts do not install a Windows service or store a Windows password.

Preview the two task definitions without registering anything:

```powershell
pwsh -NoProfile -File ./tools/windows/Register-PixelOpsTasks.ps1 -WhatIf
```

Register them yourself:

```powershell
pwsh -NoProfile -File ./tools/windows/Register-PixelOpsTasks.ps1
```

This creates `Pixel OPs - Desktop` at **your sign-in**, and
`Pixel OPs - Config Studio` as an on-demand task. Add `-StudioAtLogon` to the
registration command if you also want Studio's server at sign-in. The browser
opens only when you choose Open Config Studio. Tasks use your interactive session,
limited privileges, no execution time limit, and ignore duplicate starts.
If task registration is denied, rerun the registration in an elevated PowerShell
under the same Windows account. Do not choose a different service account.

Disable any previous Pixel OPs Startup-folder entry through Studio's old
autostart control before registering these tasks. Use `-TaskPrefix 'My Pixel OPs'`
if the default names belong to a different checkout. Controls remember that prefix.

Start now without waiting for the next sign-in:

```powershell
pwsh -NoProfile -File ./tools/windows/PixelOps.ps1 -Action Start
```

The same command works before registration, launching the tray directly.
Background Python uses `pythonw.exe`; the LCD stays visible without a taskbar
button. Preview windows retain their normal taskbar behavior. Windows decides
whether the tray icon appears beside the clock or under the overflow arrow.

| Tray action | Behavior |
| --- | --- |
| Open Config Studio | Reuses its server or triggers its task, waits for readiness, opens the local UI. |
| Stop Config Studio | Stops only the server and its helpers; display continues. Browser tabs remain open. |
| Restart display | Replaces only the display process; keeps Studio and the tray. |
| Exit | Stops Studio, display and tray. Startup registration remains for the next sign-in. |

All actions are available from PowerShell:

```powershell
pwsh -NoProfile -File ./tools/windows/PixelOps.ps1 -Action Status
pwsh -NoProfile -File ./tools/windows/PixelOps.ps1 -Action OpenStudio
pwsh -NoProfile -File ./tools/windows/PixelOps.ps1 -Action StopStudio
pwsh -NoProfile -File ./tools/windows/PixelOps.ps1 -Action RestartDisplay
pwsh -NoProfile -File ./tools/windows/PixelOps.ps1 -Action Exit
```

`StartStudio`, `StartDisplay`, and `StopDisplay` are also available for diagnostics.
Prefer StopStudio/Exit to forcibly ending scheduled tasks: these commands explicitly
stop the owned subprocesses as well. Repeated starts reuse existing processes.
Only processes belonging to this checkout are adopted/stopped, and stored PIDs
are validated against process creation time. A busy port 5174 owned by another
application causes an error instead of starting a second Studio.

Logs are in `pixel_ops/output/desktop.log`, `studio.log`, and `display.log`.
Studio-launched display restarts use its existing `runtime.log`.
Closing Studio does not stop runtime JSON watching. Most JSON edits reload;
source/dependency changes and startup options require a controlled restart.

Remove registrations later (does not stop currently running components):

```powershell
pwsh -NoProfile -File ./tools/windows/Register-PixelOpsTasks.ps1 -Uninstall -WhatIf
pwsh -NoProfile -File ./tools/windows/Register-PixelOpsTasks.ps1 -Uninstall
```
