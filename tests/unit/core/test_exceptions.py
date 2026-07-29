import pytest

from src.woolf_agents.core.exceptions import (
    BaseFrameworkException,
    IntegrationError,
    ConfigurationError
)

@pytest.mark.parametrize(
    ("exception_class", "expected_code"),
    [
        (IntegrationError, "INTEGRATION_ERROR"),
        (ConfigurationError, "CONFIGURATION_ERROR")
    ]
)
def test_core_exceptions_inherit_from_base_framwork_exception(
    exception_class: type[BaseFrameworkException],
    expected_code: str
    ) -> None:
    error = exception_class("Test failure")
    assert isinstance(error, BaseFrameworkException)
    assert isinstance(error, Exception)
    assert error.code == expected_code

def test_core_exception_bfe_message() ->None:
    error = BaseFrameworkException("Something went wrong")
    assert error.message == "Something went wrong"
    assert str(error) == "Something went wrong"
    
def test_core_exception_bfe_code()->None:
    error = BaseFrameworkException(
        "Something went wrong",
        code = "CUSTOM_CODE"
    )
    assert error.code == "CUSTOM_CODE"