"""Small Windows-only primitives for native OAuth marker replacement.

Windows callers use the platform's inherited profile-directory ACLs.  This module
checks reparse points below that base and requests write-through replacement; it
does not attempt to reinterpret enterprise ACL policy.
"""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
CSIDL_LOCAL_APPDATA = 0x001C
SHGFP_TYPE_CURRENT = 0
MOVEFILE_REPLACE_EXISTING = 0x00000001
MOVEFILE_WRITE_THROUGH = 0x00000008
_WINDOWS_DLL_ATTRIBUTE = "WinDLL"
_LAST_ERROR_ATTRIBUTE = "get_last_error"


def canonical_local_app_data() -> Path:
    """Return the OS-selected Local AppData directory without env fallbacks."""
    try:
        windll: Any = getattr(ctypes, _WINDOWS_DLL_ATTRIBUTE)
        get_last_error: Any = getattr(ctypes, _LAST_ERROR_ATTRIBUTE)
        shell32 = windll("shell32", use_last_error=True)
        get_folder_path: Any = shell32.SHGetFolderPathW
        get_folder_path.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_wchar_p,
        ]
        get_folder_path.restype = ctypes.c_long
    except AttributeError as exc:
        raise OSError("SHGetFolderPathW is unavailable") from exc
    buffer = ctypes.create_unicode_buffer(260)
    result = get_folder_path(
        None, CSIDL_LOCAL_APPDATA, None, SHGFP_TYPE_CURRENT, buffer
    )
    if result != 0 or not buffer.value:
        raise OSError(get_last_error(), "SHGetFolderPathW failed")
    return Path(buffer.value)


def is_reparse_point(path: Path) -> bool:
    """Return whether an existing path is a Windows reparse point."""
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def replace_file(temporary: Path, destination: Path) -> None:
    """Replace a marker with MoveFileExW write-through semantics."""
    try:
        windll: Any = getattr(ctypes, _WINDOWS_DLL_ATTRIBUTE)
        get_last_error: Any = getattr(ctypes, _LAST_ERROR_ATTRIBUTE)
        kernel32 = windll("kernel32", use_last_error=True)
        move_file_ex: Any = kernel32.MoveFileExW
        move_file_ex.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        move_file_ex.restype = ctypes.c_int
    except AttributeError as exc:
        raise OSError("MoveFileExW is unavailable") from exc

    if not move_file_ex(
        str(temporary),
        str(destination),
        MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH,
    ):
        raise OSError(get_last_error(), "MoveFileExW failed")
