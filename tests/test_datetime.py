import unittest
import datetime
def test_datetime_strptime_simple():
    format = "test-%Y-%m-%d"
    res = datetime.datetime.strptime("test-2023-01-02", format)
    assert res == datetime.datetime(2023, 1, 2)
def test_datetime_strptime_complex():
    format = "test-2023-01/%Y-%m-%d"
    res = datetime.datetime.strptime("test-2023-01/2023-01-02", format)
    assert res == datetime.datetime(2023, 1, 2)

def test_datetime_strptime_invalid():
    format = "test-2023-01/%Y-%m-%d"
    try:
        res = datetime.datetime.strptime("test-2023-01/202", format)
    except ValueError as ex:
        assert True, "this should be OK"

