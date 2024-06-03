import datetime

import pytest
from airflow_monitoring.saver import iso_to_dt


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            "2022-05-30T12:35:00+00:00",
            datetime.datetime(2022, 5, 30, 12, 35, tzinfo=datetime.timezone.utc),
        ),
        ("", None),
    ],
)
def test_iso_to_dt(test_input, expected):
    assert iso_to_dt(test_input) == expected
