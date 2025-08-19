import pytest
import pathlib
import logging


@pytest.fixture
def read_pytest_ini(request):
    return pathlib.Path(request.config.rootdir, "pytest.ini").read_text()


@pytest.mark.pytester_example_path("fixture_tests")
def test_psu_fixtures(testdir, read_pytest_ini) -> None:
    testdir.makeini(read_pytest_ini)
    testdir.copy_example()
    logging.info("Running PSU Fixtures Tests")
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(["*passed*"])
    result.assert_outcomes(passed=3)


def test_psu_context_manager() -> None:
    logging.info("::::::Running PSU Context Manager::::::")

    raise NotImplementedError("Test Not Yet Implemented")


@pytest.mark.pytester_example_path("fixture_tests")
def test_smu_fixtures(testdir, read_pytest_ini) -> None:
    testdir.makeini(read_pytest_ini)
    testdir.copy_example()
    logging.info("Running SMU Fixtures Tests")
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(["*passed*"])
    result.assert_outcomes(passed=3)


def test_smu_context_manager() -> None:
    logging.info("::::::Running SMU Context Manager::::::")

    raise NotImplementedError("Test Not Yet Implemented")
