from datetime import datetime
import functools
import tjson
import pytest


def parse_error(expected_msg, exc_cls=tjson.ParseError):
    def wrapper(fn):
        @functools.wraps(fn)
        def inner(*a, **kw):
            with pytest.raises(exc_cls) as exc_info:
                fn(*a, **kw)
            assert str(exc_info.value) == expected_msg
        return inner
    return wrapper


def test_empty_array():
    assert tjson.loads('[]') == []


def test_empty_object():
    assert tjson.loads('{}') == {}


def test_object_with_utf8_string_key():
    assert tjson.loads('{"s:foo":"s:bar"}') == {u'foo': u'bar'}


def test_object_with_binary_data_key():
    assert tjson.loads('{"b16:48656c6c6f2c20776f726c6421":"s:foobar"}') == {
        b'Hello, world!': u'foobar',
    }


@parse_error("Invalid tag (missing ':' delimeter)")
def test_invalid_object_with_bare_string_key():
    tjson.loads('{"foo":"s:bar"}')


@parse_error('Object member names must be text or binary')
def test_invalid_object_with_integer_key():
    tjson.loads('{"i:42":"s:foobar"}')


@parse_error("Duplicate key: b'foo'")
def test_invalid_object_with_repeated_decoded_keys():
    tjson.loads('{"b64:Zm9v":1,"b32:mzxw6":2}')


@parse_error("Duplicate key: 's:foo'")
def test_invalid_object_with_repeated_keys():
    tjson.loads('{"s:foo":1,"s:foo":2}')


def test_utf8_and_binary_keys():
    tjson.loads('{"s:foo":1,"b64:Zm9v":2}') == {u'foo': 1, b'foo': 2}


@parse_error('Toplevel elements other than object or array are disallowed')
def test_bare_string():
    tjson.loads('"s:hello, world!"')


def test_empty_utf8_string():
    assert tjson.loads('["s:"]') == [u'']


def test_utf8_string():
    assert tjson.loads('["s:hello, world!"]') == [u'hello, world!']


@parse_error("Invalid tag (missing ':' delimeter)")
def test_invalid_empty_string():
    tjson.loads('[""]')


@parse_error("Invalid tag (missing ':' delimeter)")
def test_invalid_untagged_string():
    tjson.loads('["hello, world!"]')


def test_empty_base16_binary_data():
    assert tjson.loads('["b16:"]') == [b'']


def test_base16_binary_data():
    expected = b'Hello, world!'
    assert tjson.loads('["b16:48656c6c6f2c20776f726c6421"]') == [expected]


@parse_error('Base16 data must be lowercase')
def test_invalid_base16_binary_data_with_bad_case():
    tjson.loads('["b16:48656C6C6F2C20776F726C6421"]')


@parse_error('Invalid hexadecimal data')
def test_invalid_base16_binary_data():
    tjson.loads('["b16:This is not a valid hexadecimal string"]')


def test_empty_base32_binary_data():
    assert tjson.loads('["b32:"]') == [b'']


def test_base32_binary_data():
    assert tjson.loads('["b32:jbswy3dpfqqho33snrscc"]') == [b'Hello, world!']


@parse_error('Base32 data must be lowercase')
def test_invalid_base32_binary_data_with_bad_case():
    tjson.loads('["b32:JBSWY3DPFQQHO33SNRSCC"]')


@parse_error('Base32 data must not include padding')
def test_invalid_base32_binary_data_with_padding():
    tjson.loads('["b32:jbswy3dpfqqho33snrscc==="]')


@parse_error('Base32 data must be lowercase')
def test_invalid_base32_uppercase_binary_data():
    tjson.loads('["b32:This is not a valid base32 string"]')


@parse_error('Invalid base32-encoded data')
def test_invalid_base32_binary_data():
    tjson.loads('["b32:this is not a valid base32 string"]')


def test_empty_base64url_binary_data():
    assert tjson.loads('["b64:"]') == [b'']


def test_base64url_binary_data():
    assert tjson.loads('["b64:SGVsbG8sIHdvcmxkIQ"]') == [b'Hello, world!']


@parse_error('Base64 data must not include padding')
def test_invalid_base64url_binary_data_with_padding():
    tjson.loads('["b64:SGVsbG8sIHdvcmxkIQ=="]')


@parse_error("Base64 data must not contain '+' or '/'")
def test_invalid_base64url_binary_data_with_non_url_safe_characters():
    tjson.loads('["b64:+/+/"]')


@parse_error('Invalid base64-encoded data')
def test_invalid_base64url_binary_data():
    tjson.loads('["b64:This is not a valid base64url string"]')


def test_int_as_float():
    value = tjson.loads('[42]')
    assert value == [42.0]
    assert type(value[0]) == float


def test_float():
    assert tjson.loads('[42.5]') == [42.5]


def test_signed_integer():
    assert tjson.loads('["i:42"]') == [42]


def test_signed_integer_range_test():
    data = '["i:-9223372036854775808", "i:9223372036854775807"]'
    assert tjson.loads(data) == [-9223372036854775808, 9223372036854775807]


@parse_error('oversized integer: 9223372036854775808')
def test_oversized_signed_integer_test():
    tjson.loads('["i:9223372036854775808"]')


@parse_error('undersized integer: -9223372036854775809')
def test_undersized_signed_integer_test():
    tjson.loads('["i:-9223372036854775809"]')


@parse_error("invalid literal for int() with base 10: 'This is not a valid "
             "integer'", ValueError)
def test_invalid_signed_integer():
    tjson.loads('["i:This is not a valid integer"]')


def test_unsigned_integer():
    assert tjson.loads('["u:42"]') == [42]


def test_unsigned_integer_range_test():
    assert tjson.loads('["u:18446744073709551615"]') == [18446744073709551615]


@parse_error('oversized integer: 18446744073709551616')
def test_oversized_unsigned_integer_test():
    tjson.loads('["u:18446744073709551616"]')


@parse_error('negative value for unsigned integer: -1')
def test_negative_unsigned_integer_test():
    tjson.loads('["u:-1"]')


@parse_error("invalid literal for int() with base 10: 'This is not a valid "
             "integer'", ValueError)
def test_invalid_unsigned_integer():
    tjson.loads('["u:This is not a valid integer"]')


def test_timestamp():
    expected = datetime(2016, 10, 2, 7, 31, 51)
    assert tjson.loads('["t:2016-10-02T07:31:51Z"]') == [expected]


@parse_error("time data '2016-10-02T07:31:51-08:00' does not match format "
             "'%Y-%m-%dT%H:%M:%SZ'", ValueError)
def test_timestamp_with_invalid_time_zone():
    tjson.loads('["t:2016-10-02T07:31:51-08:00"]')


@parse_error("time data 'This is not a valid timestamp' does not match format "
             "'%Y-%m-%dT%H:%M:%SZ'", ValueError)
def test_invalid_timestamp():
    tjson.loads('["t:This is not a valid timestamp"]')
