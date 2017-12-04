from datetime import datetime

import pytest

from heliosSDK.utilities import parsingTools

# Python 2 to 3 fix.
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


@pytest.fixture()
def url():
    return 'https://helios-exelis.s3.amazonaws.com/1a67-CODOT-11150-13689_20171128153407000.jpg'


@pytest.fixture()
def name():
    return '1a67-CODOT-11150-13689_20171128153407000.jpg'


def test_parseTime_from_url(url):
    result = parsingTools.parseTime(url)
    assert (result == datetime(2017, 11, 28, 15, 34, 7))


def test_parseTime_from_name(name):
    result = parsingTools.parseTime(name)
    assert (result == datetime(2017, 11, 28, 15, 34, 7))


def test_parseCamera_from_url(url):
    result = parsingTools.parseCamera(url)
    assert (result == 'CODOT-11150-13689')


def test_parseCamera_from_name(name):
    result = parsingTools.parseCamera(name)
    assert (result == 'CODOT-11150-13689')


def test_parseImageName(url, name):
    result = parsingTools.parseImageName(url)
    assert (result == name)


def test_parseUrl(url):
    result = parsingTools.parseUrl(url)
    assert (result == urlparse(url))


if __name__ == '__main__':
    pytest.main([__file__])