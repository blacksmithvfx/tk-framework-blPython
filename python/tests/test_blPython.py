import pytest
from pytest import raises, fixture

import sys, os

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

import blPython

def test_blPython():
    blp = blPython.custom_entities
    assert blp is not None