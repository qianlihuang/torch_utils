import gzip
from collections import defaultdict
from pathlib import Path

import orjson
import typer


def main(
        filename: str,
        dir_data: str = "/Users/tom/temp/temp_sglang_server2local",
):
    dir_data = Path(dir_data)
    path_input = dir_data / filename
    path_output = dir_data / f"perfetto-compatible-{filename}"
    print(f"{path_input=} {path_output=}")

    with (gzip.open(path_input, 'rt', encoding='utf-8') as f):
        trace = orjson.loads(f.read())
        output = {key: value for key, value in trace.items() if key != 'traceEvents'}
        output['traceEvents'] = _process_events(trace.get('traceEvents', []))

    with gzip.open(path_output, 'wb') as f:
        f.write(orjson.dumps(output))


def _process_events(events):
    print(f"process_events start {len(events)=}")

    last_end_time_of_pid_tid = defaultdict(lambda: -1)
    moved_tid_by_slice = {}

    for e in events:
        if e["ph"] == "X" and _is_interest_event(e):
            original_tid = e["tid"]
            while e["ts"] < last_end_time_of_pid_tid[(e["pid"], e["tid"])]:
                e["tid"] = str(e["tid"]) + "_pdl"
            if e["tid"] != original_tid:
                moved_tid_by_slice[(e["pid"], original_tid, e["ts"])] = e["tid"]
            last_end_time_of_pid_tid[(e["pid"], e["tid"])] = e["ts"] + e["dur"]

    # Flow end events identify their target slice by pid, tid, and timestamp.
    # Move them with the slice so Perfetto keeps the CUDA launch arrows intact.
    for e in events:
        if e["ph"] == "f":
            slice_key = (e["pid"], e["tid"], e["ts"])
            if slice_key in moved_tid_by_slice:
                e["tid"] = moved_tid_by_slice[slice_key]

    return events


def _is_interest_event(e):
    return "registers per thread" in e.get("args", {})


if __name__ == "__main__":
    typer.run(main)
