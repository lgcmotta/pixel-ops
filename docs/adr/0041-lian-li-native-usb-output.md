# 0041 - Lian Li native USB output

Status: Accepted

## Context

The US88v1 can expose a Windows secondary display or a native WinUSB LCD
interface. The secondary display shows the Windows desktop, which Windows
replaces with the lock screen on Win+L. The goal is to keep showing the live
Pixel Ops layout while the signed-in PC is locked and awake.

## Decision

Add `lian_li_usb` as a `DisplayOutput` target. The existing per-user Python
runtime opens the US88v1 LCD interface (`1CBE:A088`) through WinUSB. It prepares
1920x480 landscape frames in the panel's 480x1920 JPEG format, sends the
Lian Li command and image together, and reads the panel's acknowledgement.
The output uses the runtime's existing reconnect loop after an I/O error.
The protocol is described in the [US88v1 LCD reference](https://github.com/immortalbob/lian-li-universal-screen-protocol/blob/b9e4bb8/lianli-universal-screen-lcd.md).

Config Studio selects the target and can scope it to a USB serial number when
more than one US88v1 is attached. The existing display rotation setting handles
panel mounting orientation. The sign-in task and tray controls own process
lifecycle as in ADR 0036. Frame transport sits below the game renderer and event
pump.

An optional `border_color` in the Lian Li output config applies a solid RGB hex
color to the separate `0416:8050` LED controller when the LCD output starts.
Pixel Ops sends one frame to all 60 LEDs and releases the controller. It logs
lighting errors and continues LCD output. Applying a border color requires one
connected US88v1 LCD and LED controller so the selection is unambiguous. See the
[US88v1 LED reference](https://github.com/immortalbob/lian-li-universal-screen-protocol/blob/b9e4bb8/lianli-universal-screen-ledring.md).

## Consequences

Native LCD mode requires **Secondary screen** to be off and the LCD interface
to be available to Pixel Ops. Pixel Ops sends frames while the process and
USB device are active. Windows sleep stops live rendering until resume, when
the runtime can reopen the interface if it disconnected. The secondary monitor
path in ADR 0035 remains available via the `window` target.
