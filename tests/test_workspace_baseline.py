"""Streamlit regression coverage for all three independently uploaded workspaces."""

import base64
import json
import unittest
from datetime import date

import numpy as np
from streamlit.testing.v1 import AppTest

from config.constants import (
    WORKSPACE_FULL_ANALYSIS,
    WORKSPACE_PLOT_GRAPH,
    WORKSPACE_PLOT_TRACES,
)
from tests.sample_data import (
    BASELINE_SUMMARY,
    instron_csv_bytes,
    multimeter_csv_bytes,
)


class WorkspaceBaselineTests(unittest.TestCase):
    def _axis_length(self, axis):
        if isinstance(axis, dict) and "bdata" in axis:
            values = base64.b64decode(axis["bdata"])
            return np.frombuffer(values, dtype=np.dtype(axis["dtype"])).size
        return len(axis)

    def _new_app(self):
        app = AppTest.from_file("app.py").run()
        self.assertEqual(app.exception, [])
        uploaders = app.get("file_uploader")
        if uploaders and type(uploaders[0]).__name__ == "UnknownElement":
            self.skipTest(
                "This Streamlit AppTest version does not expose file uploader widgets."
            )
        return app

    def _upload(self, app, key, filename, data):
        for uploader in app.get("file_uploader"):
            if uploader.key == key:
                uploader.set_value((filename, data, "text/csv"))
                return
        self.fail(f"Upload widget {key!r} was not rendered.")

    def test_three_workspaces_keep_independent_uploads(self):
        app = self._new_app()
        self._upload(
            app, "analysis_instron_uploads", "analysis_instron.csv", instron_csv_bytes()
        )
        self._upload(
            app, "analysis_dmm_uploads", "analysis_dmm.csv", multimeter_csv_bytes()
        )
        self._upload(
            app, "plot_instron_uploads", "trace_instron.csv", instron_csv_bytes()
        )
        self._upload(
            app, "plot_dmm_uploads", "trace_dmm.csv", multimeter_csv_bytes()
        )
        self._upload(
            app,
            "plot_csv_uploads",
            "generic.csv",
            b"time,signal\n0,1\n1,2\n2,3\n",
        )
        app.run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.radio[0].value, WORKSPACE_FULL_ANALYSIS)
        self.assertEqual(
            app.dataframe[0].value.to_dict(orient="records")[0], BASELINE_SUMMARY
        )

        app.radio[0].set_value(WORKSPACE_PLOT_TRACES).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.selectbox[0].options[0], "Resistance (DMM)")
        self.assertEqual(len(app.get("plotly_chart")), 2)
        full_trace = json.loads(app.get("plotly_chart")[0].proto.spec)
        self.assertEqual(self._axis_length(full_trace["data"][0]["x"]), 11)

        app.radio[1].set_value("Cut to time range").run()
        app.number_input[0].set_value(2.0).run()
        app.number_input[1].set_value(4.0).run()
        self.assertEqual(app.exception, [])
        cropped_trace = json.loads(app.get("plotly_chart")[0].proto.spec)
        axis = cropped_trace["data"][0]["x"]
        if isinstance(axis, dict):
            axis = np.frombuffer(
                base64.b64decode(axis["bdata"]),
                dtype=np.dtype(axis["dtype"]),
            ).tolist()
        self.assertEqual(list(axis), [2.0, 3.0, 4.0])

        app.radio[0].set_value(WORKSPACE_PLOT_GRAPH).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(app.selectbox[0].value, "time")
        self.assertEqual(app.selectbox[1].value, "signal")
        self.assertEqual(len(app.get("plotly_chart")), 1)

        self.assertEqual(
            {uploader.key for uploader in app.get("file_uploader")},
            {
                "analysis_instron_uploads",
                "analysis_dmm_uploads",
                "plot_instron_uploads",
                "plot_dmm_uploads",
                "plot_csv_uploads",
            },
        )

    def test_two_specimens_and_csv_download_render(self):
        app = self._new_app()
        self._upload(
            app,
            "analysis_instron_uploads",
            "specimen.csv",
            instron_csv_bytes(),
        )
        self._upload(
            app,
            "analysis_dmm_uploads",
            "meter.csv",
            multimeter_csv_bytes(),
        )
        app.run()
        app.number_input[0].set_value(2).run()
        self.assertEqual(app.exception, [])
        self.assertEqual(len(app.selectbox[0].options), 1)
        self.assertEqual(len(app.selectbox[1].options), 1)
        self.assertEqual(len(app.dataframe[0].value), 2)
        self.assertEqual(
            [button.label for button in app.get("download_button")],
            ["Download Complete Summary Metrics CSV"],
        )
        self.assertEqual(len(app.get("plotly_chart")), 5)

    def test_generic_date_axis_filters_without_losing_full_data_default(self):
        app = self._new_app()
        app.radio[0].set_value(WORKSPACE_PLOT_GRAPH).run()
        self._upload(
            app,
            "plot_csv_uploads",
            "dated.csv",
            b"Date,Signal\n2026-01-01,2\n2026-01-02,4\n2026-01-03,8\n",
        )
        app.run()
        self.assertEqual(app.exception, [])
        self.assertEqual(len(app.get("plotly_chart")), 1)
        full_figure = json.loads(app.get("plotly_chart")[0].proto.spec)
        self.assertEqual(len(full_figure["data"][0]["x"]), 3)

        app.get("radio")[1].set_value("Choose range").run()
        app.get("date_input")[0].set_value(
            (date(2026, 1, 2), date(2026, 1, 3))
        ).run()
        self.assertEqual(app.exception, [])
        cropped_figure = json.loads(app.get("plotly_chart")[0].proto.spec)
        self.assertEqual(len(cropped_figure["data"][0]["x"]), 2)


if __name__ == "__main__":
    unittest.main()
