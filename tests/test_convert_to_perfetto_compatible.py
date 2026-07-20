import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "convert_to_perfetto_compatible"
    / "convert_to_perfetto_compatible.py"
)
SPEC = importlib.util.spec_from_file_location("convert_to_perfetto_compatible", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProcessEventsTest(unittest.TestCase):
    def test_moves_overlapping_kernels_and_their_flow_end_events(self):
        events = [
            self._kernel(ts=0, dur=10),
            self._flow_end(ts=5),
            self._kernel(ts=5, dur=10),
            self._flow_end(ts=6),
            self._kernel(ts=6, dur=10),
        ]

        processed = MODULE._process_events(events)

        self.assertEqual(processed[0]["tid"], 7)
        self.assertEqual(processed[1]["tid"], "7_pdl")
        self.assertEqual(processed[2]["tid"], "7_pdl")
        self.assertEqual(processed[3]["tid"], "7_pdl_pdl")
        self.assertEqual(processed[4]["tid"], "7_pdl_pdl")

    def test_leaves_unmatched_flow_end_event_on_its_original_track(self):
        events = [
            self._kernel(ts=0, dur=10),
            self._flow_end(ts=4),
        ]

        processed = MODULE._process_events(events)

        self.assertEqual(processed[1]["tid"], 7)

    @staticmethod
    def _kernel(ts, dur):
        return {
            "ph": "X",
            "pid": 0,
            "tid": 7,
            "ts": ts,
            "dur": dur,
            "args": {"registers per thread": 128},
        }

    @staticmethod
    def _flow_end(ts):
        return {
            "ph": "f",
            "pid": 0,
            "tid": 7,
            "ts": ts,
        }


if __name__ == "__main__":
    unittest.main()
