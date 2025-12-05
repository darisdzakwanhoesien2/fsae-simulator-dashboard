# utils/json_writer.py
import json
import os
import time


def _ensure_dir(path: str):
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)


def atomic_write(path: str, data: dict, attempts=3):
    """
    Safely write JSON to a file using tmp write + replace.
    Retries automatically on APFS/macOS race conditions.
    """
    _ensure_dir(path)
    tmp = path + ".tmp"

    for attempt in range(attempts):
        try:
            # 1. Write temp file
            with open(tmp, "w") as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())

            # Ensure temp file is visible
            if not os.path.exists(tmp):
                raise RuntimeError("Temporary file not created after write")

            # 2. Atomic replace
            os.replace(tmp, path)
            return

        except Exception as e:
            print(f"[atomic_write] Attempt {attempt+1} failed: {e}")
            time.sleep(0.05)

    # ---- FINAL FALLBACK (non-atomic write) ----
    print("[atomic_write] ⚠ Falling back to non-atomic write.")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def write_realtime_json(path, data):
    """Write realtime.json safely."""
    atomic_write(path, data)


def write_session_log(path, session_list):
    """Write session log safely."""
    atomic_write(path, session_list)


# # utils/json_writer.py
# import json
# import os


# def _ensure_dir(path: str):
#     folder = os.path.dirname(path)
#     if folder:
#         os.makedirs(folder, exist_ok=True)


# def write_realtime_json(path, data):
#     """
#     Atomically write 'realtime.json' (or any JSON) with a temp file dance.
#     Ensures folder exists and avoids partial writes.
#     """
#     _ensure_dir(path)
#     tmp = path + ".tmp"

#     with open(tmp, "w") as f:
#         json.dump(data, f, indent=2)

#     # Safety check – tmp must exist
#     if not os.path.exists(tmp):
#         raise RuntimeError(f"Temp file was not created: {tmp}")

#     os.replace(tmp, path)


# def write_session_log(path, session_list):
#     """
#     Overwrite full session log JSON.
#     """
#     _ensure_dir(path)
#     tmp = path + ".tmp"

#     with open(tmp, "w") as f:
#         json.dump(session_list, f, indent=2)

#     if not os.path.exists(tmp):
#         raise RuntimeError(f"Temp file was not created: {tmp}")

#     os.replace(tmp, path)


# # utils/json_writer.py
# import json
# import os

# # def write_realtime_json(path, data):
# #     tmp = path + ".tmp"
# #     with open(tmp, "w") as f:
# #         json.dump(data, f)
# #     os.replace(tmp, path)
# # utils/json_writer.py
# import json, os, tempfile

# def write_realtime_json(path, data):
#     # Ensure directory exists
#     folder = os.path.dirname(path)
#     os.makedirs(folder, exist_ok=True)

#     # Write via atomic temp file
#     tmp = path + ".tmp"
#     with open(tmp, "w") as f:
#         json.dump(data, f)

#     os.replace(tmp, path)


# def write_session_log(path, data_list):
#     with open(path, "w") as f:
#         json.dump(data_list, f, indent=2)
