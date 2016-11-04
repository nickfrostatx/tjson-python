import base64
import binascii
from datetime import datetime, timedelta, tzinfo
import json
import re


__all__ = ['EncodeError', 'ParseError', 'loads', 'dumps']


INT_MAX = 2 ** 63 - 1
INT_MIN = -(2 ** 63)
UINT_MAX = 2 ** 64 - 1

text_type = type(u'')


class EncodeError(ValueError):
    """Exception class when trying to encode bad data."""


class ParseError(ValueError):
    """Exception class for tjson-specific parse errors."""


def raise_on_duplicate_keys(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ParseError("Duplicate key: '%s'" % k)
        d[k] = v
    return d


def loads(s, **kwargs):
    kwargs['object_pairs_hook'] = raise_on_duplicate_keys
    obj = json.loads(s, **kwargs)
    if not isinstance(obj, (list, dict)):
        raise ParseError('Toplevel elements other than object or array are '
                         'disallowed')
    return unpack(obj)


def dumps(obj):
    if not isinstance(obj, (list, dict)):
        raise EncodeError('Toplevel elements other than object or array are '
                          'disallowed')
    return json.dumps(pack(obj))


def pack(obj):
    if isinstance(obj, list):
        return [pack(e) for e in obj]
    elif isinstance(obj, dict):
        rv = {}
        for k in obj:
            if not isinstance(k, (text_type, bytes)):
                raise EncodeError('Object member names must be text or binary')
            rv[pack(k)] = pack(obj[k])
        return rv
    elif isinstance(obj, text_type):
        return u's:' + obj
    elif isinstance(obj, bytes):
        return u'b64:' + (base64.urlsafe_b64encode(obj).rstrip(b'=')
                          .decode('ascii'))
    elif isinstance(obj, float):
        return obj
    elif isinstance(obj, int):
        if obj < 0:
            return u'i:%d' % obj
        else:
            return u'u:%d' % obj


def unpack(obj):
    """Deep copy of obj, parse any string values."""
    if isinstance(obj, list):
        return [unpack(e) for e in obj]
    elif isinstance(obj, dict):
        rv = {}
        for k in obj:
            parsed_key = parse_str(k)
            if not isinstance(parsed_key, (text_type, bytes)):
                raise ParseError('Object member names must be text or binary')
            elif parsed_key in rv:
                raise ParseError('Duplicate key: %r' % parsed_key)
            rv[parsed_key] = unpack(obj[k])
        return rv
    elif isinstance(obj, text_type):
        return parse_str(obj)
    elif isinstance(obj, float):
        return obj
    elif isinstance(obj, int):
        return float(obj)

    raise TypeError('Unrecognized TJSON object type')


def parse_str(s):
    try:
        ndx = s.index(':', 0, 4)
    except ValueError:
        raise ParseError("Invalid tag (missing ':' delimeter)")
    tag, body = s[:ndx + 1], s[ndx + 1:]

    if tag == 's:':
        return body
    elif tag == 'b16:':
        return _parse_b16(body)
    elif tag == 'b32:':
        return _parse_b32(body)
    elif tag == 'b64:':
        return _parse_b64(body)
    elif tag == 'i:':
        return _parse_int(body)
    elif tag == 'u:':
        return _parse_uint(body)
    elif tag == 't:':
        return _parse_date(body)

    raise ParseError('Invalid tag %r on string %r' % (tag, s))


def _parse_b16(s):
    if re.search(r'[A-F]', s):
        raise ParseError('Base16 data must be lowercase')

    try:
        return binascii.unhexlify(s)
    except (TypeError, ValueError):
        raise ParseError('Invalid hexadecimal data')


def _parse_b32(s):
    if re.search(r'[A-Z]', s):
        raise ParseError('Base32 data must be lowercase')
    elif s.endswith('='):
        raise ParseError('Base32 data must not include padding')

    padding = '=' * (-len(s) % 8)
    try:
        return base64.b32decode(s.upper() + padding)
    except (TypeError, ValueError):
        raise ParseError('Invalid base32-encoded data')


def _parse_b64(s):
    if re.search(r'\+|\/', s):
        raise ParseError("Base64 data must not contain '+' or '/'")
    elif s.endswith('='):
        raise ParseError('Base64 data must not include padding')

    padding = '=' * (-len(s) % 4)
    try:
        encoded = (s + padding).encode('ascii')
        return base64.urlsafe_b64decode(encoded)
    except (TypeError, ValueError):
        raise ParseError('Invalid base64-encoded data')


def _parse_int(s):
    val = int(s)
    if val > INT_MAX:
        raise ParseError('oversized integer: %d' % val)
    elif val < INT_MIN:
        raise ParseError('undersized integer: %d' % val)
    return val


def _parse_uint(s):
    val = int(s)
    if val < 0:
        raise ParseError('negative value for unsigned integer: %d' % val)
    elif val > UINT_MAX:
        raise ParseError('oversized integer: %d' % val)
    return val


def _parse_date(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
