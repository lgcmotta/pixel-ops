"""Windows transport for the Lian Li US88v1 LCD and border LEDs."""

from __future__ import annotations

import ctypes as ct
import sys
from ctypes import wintypes as wt
from uuid import UUID


_WINUSB_GUID = UUID("dee824ef-729b-4a0e-9c14-b7117d33a817")
_LCD_INTERFACE_PREFIX = r"\\?\usb#vid_1cbe&pid_a088#"
_LED_INTERFACE_PREFIX = r"\\?\usb#vid_0416&pid_8050#"
_BULK_OUT = 0x01
_BULK_IN = 0x81
_PIPE_TRANSFER_TIMEOUT = 3
_CR_BUFFER_SMALL = 0x1A


def _bind(dll, name, result, *arguments):
    function = getattr(dll, name)
    function.restype = result
    function.argtypes = arguments
    return function


def _device_paths(prefix: str = _LCD_INTERFACE_PREFIX) -> list[str]:
    if sys.platform != "win32":
        return []
    config = ct.WinDLL("cfgmgr32")
    guid = ct.create_string_buffer(_WINUSB_GUID.bytes_le, 16)
    size = _bind(config, "CM_Get_Device_Interface_List_SizeW", wt.ULONG,
                 ct.POINTER(wt.ULONG), ct.c_void_p, wt.LPCWSTR, wt.ULONG)
    list_paths = _bind(config, "CM_Get_Device_Interface_ListW", wt.ULONG,
                       ct.c_void_p, wt.LPCWSTR, wt.LPWSTR, wt.ULONG, wt.ULONG)
    length = wt.ULONG()
    for _ in range(3):
        status = size(ct.byref(length), guid, None, 0)
        if status:
            break
        buffer = ct.create_unicode_buffer(length.value)
        status = list_paths(guid, None, buffer, length.value, 0)
        if status == 0:
            break
        if status != _CR_BUFFER_SMALL:
            break
    if status:
        raise RuntimeError(f"Could not enumerate WinUSB devices (CONFIGRET 0x{status:02x})")

    return [path for path in buffer[:].split("\0") if path.lower().startswith(prefix)]


def scan_lian_li_serials() -> list[str]:
    return sorted(path.split("#")[2] for path in _device_paths())


def _device_path(serial_number: str) -> str:
    matches = _device_paths()
    if serial_number:
        matches = [path for path in matches if path.split("#")[2].casefold() == serial_number.casefold()]
    if not matches:
        raise RuntimeError("Lian Li USB device 1CBE:A088 not found. Turn off Secondary screen in L-Connect 3.")
    if len(matches) > 1:
        raise RuntimeError("Multiple Lian Li US88v1 panels found. Set the output's serial_number.")
    return matches[0]


def _led_ring_path() -> str:
    rings = _device_paths(_LED_INTERFACE_PREFIX)
    if not rings:
        raise RuntimeError("Lian Li border LEDs (0416:8050) not found")
    if len(rings) != 1 or len(_device_paths()) != 1:
        raise RuntimeError("Lian Li border color requires a single US88v1 LCD and LED controller")
    return rings[0]


class LianLiWinUsb:
    def __init__(self, serial_number: str, timeout_ms: int, *, led_ring: bool = False):
        if sys.platform != "win32":
            raise RuntimeError("Lian Li US88v1 USB output requires Windows WinUSB.")
        path = _led_ring_path() if led_ring else _device_path(serial_number)
        device = "border LEDs" if led_ring else "LCD"
        kernel = ct.WinDLL("kernel32", use_last_error=True)
        usb = ct.WinDLL("winusb", use_last_error=True)
        create_file = _bind(kernel, "CreateFileW", wt.HANDLE, wt.LPCWSTR, wt.DWORD, wt.DWORD,
                            ct.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE)
        self._close_file = _bind(kernel, "CloseHandle", wt.BOOL, wt.HANDLE)
        initialize = _bind(usb, "WinUsb_Initialize", wt.BOOL, wt.HANDLE, ct.POINTER(wt.HANDLE))
        self._free = _bind(usb, "WinUsb_Free", wt.BOOL, wt.HANDLE)
        set_policy = _bind(usb, "WinUsb_SetPipePolicy", wt.BOOL,
                           wt.HANDLE, wt.BYTE, wt.ULONG, wt.ULONG, ct.c_void_p)
        pipe_arguments = (wt.HANDLE, wt.BYTE, ct.c_void_p, wt.ULONG, ct.POINTER(wt.ULONG), ct.c_void_p)
        self._read_pipe = _bind(usb, "WinUsb_ReadPipe", wt.BOOL, *pipe_arguments)
        self._write_pipe = _bind(usb, "WinUsb_WritePipe", wt.BOOL, *pipe_arguments)

        access = 0x80000000 | 0x40000000  # GENERIC_READ | GENERIC_WRITE
        self._file = create_file(path, access, 0x03, None, 3, 0x40000000, None)
        self._interface = wt.HANDLE()
        if self._file == ct.c_void_p(-1).value:
            raise _open_error(device)
        try:
            if not initialize(self._file, ct.byref(self._interface)):
                raise _open_error(device)
            timeout = wt.ULONG(timeout_ms)
            for endpoint in (_BULK_OUT, _BULK_IN):
                if not set_policy(self._interface, endpoint, _PIPE_TRANSFER_TIMEOUT,
                                  ct.sizeof(timeout), ct.byref(timeout)):
                    raise RuntimeError(f"Could not set Lian Li USB timeout: {ct.WinError(ct.get_last_error())}")
        except Exception:
            self.close()
            raise

    def write(self, packet: bytes) -> None:
        written = wt.ULONG()
        if not self._write_pipe(self._interface, _BULK_OUT, packet, len(packet), ct.byref(written), None):
            raise RuntimeError(f"Lian Li USB write failed: {ct.WinError(ct.get_last_error())}")
        if written.value != len(packet):
            raise RuntimeError(f"Lian Li USB short write ({written.value}/{len(packet)} bytes)")

    def read(self) -> bytes:
        buffer = ct.create_string_buffer(512)
        received = wt.ULONG()
        if not self._read_pipe(self._interface, _BULK_IN, buffer, len(buffer), ct.byref(received), None):
            raise RuntimeError(f"Lian Li USB read failed: {ct.WinError(ct.get_last_error())}")
        return buffer.raw[:received.value]

    def close(self) -> None:
        if self._interface:
            self._free(self._interface)
            self._interface = wt.HANDLE()
        if self._file is not None:
            self._close_file(self._file)
            self._file = None


def _open_error(device: str) -> RuntimeError:
    error = ct.get_last_error()
    message = f"Could not open the Lian Li US88v1 {device} interface: {ct.WinError(error)}"
    if error in (5, 32):
        message += " Check whether L-Connect 3 or another app owns it."
    return RuntimeError(message)
