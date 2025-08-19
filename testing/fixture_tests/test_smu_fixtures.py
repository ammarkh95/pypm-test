from pypm_test import KeysightU2723Wrapper


def test_smu_fixture(
    smu_handle: KeysightU2723Wrapper,
) -> None:
    assert isinstance(smu_handle, KeysightU2723Wrapper)
    # TODO COMPLETE THIS TEST
