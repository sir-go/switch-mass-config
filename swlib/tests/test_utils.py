import pytest
from swlib.class_switch import c_join, list_pack
from swlib.snmp_term import mac_dec_to_hex


@pytest.mark.parametrize('mac_dec,result', [
    ((10, 12, 43, 55, 67, 43), '0a0c2b37432b'),
    ((0, 0, 0, 0, 0, 0), '000000000000'),
    ([1], '01'),
])
def test_mac_dec_to_hex(mac_dec, result):
    assert mac_dec_to_hex(mac_dec) == result


@pytest.mark.parametrize('joined_list,result', [
    (['1', '0', '3'], '1, 0, 3'),
    (['1'], '1'),
    ([], ''),
])
def test_c_join(joined_list, result):
    assert c_join(joined_list) == result


@pytest.mark.parametrize('packed_list,result', [
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], '1-12'),
    ([1, 2, 3, 6, 7, 8, 9, 10, 11], '1-3,6-11'),
    ([1, 4, 5, 6, 7], '1,4-7'),
    ([1, 2, 3, 5, 6, 7], '1-3,5-7'),
    ([1, 2, 3, 6, 7, 10, 11, 12], '1-3,6-7,10-12'),
])
def test_list_pack(packed_list, result):
    assert list_pack(packed_list) == result
