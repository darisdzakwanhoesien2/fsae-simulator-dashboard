# utils/json_writer.py
import json
import os

def write_realtime_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)

def write_session_log(path, data_list):
    with open(path, "w") as f:
        json.dump(data_list, f, indent=2)
