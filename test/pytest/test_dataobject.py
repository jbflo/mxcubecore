import os
import sys
import jsonschema

TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
MXCUBE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
HWR = os.path.join(MXCUBE, "HardwareRepository")
sys.path.insert(0, MXCUBE)

from HardwareRepository import HardwareRepository as HWR
from HardwareRepository.utils.dataobject import DataObject


class TestDataObject(DataObject):
    _SCHEMA = {
        "type": "object",
        "properties": {"value": {"type": "number"}, "limit": {"type": "number"}},
    }


def test_object_creation():
    do = TestDataObject({"value": 2, "limit": 4})

    assert do.value == 2 and do.limit == 4


def test_validation_not_valid():
    # Limit should be a number so this should raise a ValidationError
    try:
        do = TestDataObject({"value": 2, "limit": "2"})
    except jsonschema.exceptions.ValidationError:
        assert True
    else:
        assert False


def test_validation_valid():
    try:
        do = TestDataObject({"value": 2, "limit": 2})
    except jsonschema.exceptions.ValidationError:
        assert False
    else:
        assert True


def test_dangerously_set_valid():
    do = TestDataObject({"value": 2, "limit": 2})

    do.dangerously_set("value", 4)

    assert do.value == 4


def test_dangerously_set_not_valid():
    # Limit should be a number so this should raise a ValidationError
    try:
        do = TestDataObject({"value": 2, "limit": 2})
        do.dangerously_set("value", "4")

    except jsonschema.exceptions.ValidationError:
        assert do.value == 2
    else:
        assert False


def test_to_mutable():
    do = TestDataObject({"value": 2, "limit": 2})

    do_mutable = do.to_mutable()

    do_mutable["value"] = 4

    assert do.value != do_mutable["value"]
