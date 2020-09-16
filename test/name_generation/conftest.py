import pytest

from aclimatise.converter import WrapperGenerator


@pytest.fixture()
def snake_gen():
    return WrapperGenerator(case="snake", generate_names=True)


@pytest.fixture()
def camel_gen():
    return WrapperGenerator(case="camel", generate_names=True)


@pytest.fixture()
def gen():
    return WrapperGenerator()
