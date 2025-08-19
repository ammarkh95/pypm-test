from pypm_test import KeysightU3606Wrapper


def test_psu_fixture(psu_handle: KeysightU3606Wrapper) -> None:
    assert isinstance(psu_handle, KeysightU3606Wrapper)
    # TODO COMPLETE THIS TEST
