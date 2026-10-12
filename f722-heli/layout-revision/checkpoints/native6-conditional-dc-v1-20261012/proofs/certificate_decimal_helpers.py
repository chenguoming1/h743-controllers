# These helpers are embedded in the isolated native_edge_noding.py successor.
# F and Refused are its existing Fraction alias and refusal exception.
CERTIFICATE_DECIMAL_MAX_DIGITS = 32768
CERTIFICATE_DECIMAL_CHUNK_DIGITS = 600
_CERTIFICATE_DECIMAL_BASE = 10 ** CERTIFICATE_DECIMAL_CHUNK_DIGITS
_CERTIFICATE_DECIMAL_LIMIT = 10 ** CERTIFICATE_DECIMAL_MAX_DIGITS


def _certificate_integer_decimal(value):
    """Lossless canonical decimal text, bounded without changing Python guards."""
    if type(value) is not int:
        raise Refused('Certificate decimal integer has the wrong type')
    negative = value < 0
    value = -value if negative else value
    if value >= _CERTIFICATE_DECIMAL_LIMIT:
        raise Refused('Certificate decimal integer exceeds the 32768-digit representation cap')
    chunks = []
    while value >= _CERTIFICATE_DECIMAL_BASE:
        value, remainder = divmod(value, _CERTIFICATE_DECIMAL_BASE)
        chunks.append(str(remainder).zfill(CERTIFICATE_DECIMAL_CHUNK_DIGITS))
    text = str(value) + ''.join(reversed(chunks))
    return '-' + text if negative else text


def exact_fraction_decimal(value):
    """Keep legacy str(int/Fraction) spelling; change only bounded serialization."""
    if type(value) is int:
        return _certificate_integer_decimal(value)
    if not isinstance(value, F):
        raise Refused('Exact certificate scalar is not an integer or Fraction')
    numerator = _certificate_integer_decimal(value.numerator)
    if value.denominator == 1:
        return numerator
    return numerator + '/' + _certificate_integer_decimal(value.denominator)


def _certificate_integer_from_decimal(text):
    """Bounded reader for audit tools; never parses an oversized decimal chunk."""
    if not isinstance(text, str) or not text:
        raise Refused('Certificate decimal integer text is absent')
    negative = text.startswith('-')
    digits = text[1:] if negative else text
    if not digits or len(digits) > CERTIFICATE_DECIMAL_MAX_DIGITS:
        raise Refused('Certificate decimal integer text exceeds its representation cap')
    if any(c < '0' or c > '9' for c in digits):
        raise Refused('Certificate decimal integer text is not ASCII decimal')
    if (len(digits) > 1 and digits[0] == '0') or (negative and digits == '0'):
        raise Refused('Certificate decimal integer text is not canonical')
    value = 0
    for start in range(0, len(digits), CERTIFICATE_DECIMAL_CHUNK_DIGITS):
        chunk = digits[start:start + CERTIFICATE_DECIMAL_CHUNK_DIGITS]
        value = value * (10 ** len(chunk)) + int(chunk)
    return -value if negative else value


def exact_fraction_from_decimal(text):
    """Read the unchanged canonical decimal certificate field losslessly."""
    if not isinstance(text, str) or len(text) > 2 * CERTIFICATE_DECIMAL_MAX_DIGITS + 2:
        raise Refused('Exact certificate text has wrong type or exceeds its cap')
    components = text.split('/')
    if len(components) not in (1, 2):
        raise Refused('Exact certificate text has an invalid fraction separator')
    numerator = _certificate_integer_from_decimal(components[0])
    denominator = _certificate_integer_from_decimal(components[1]) if len(components) == 2 else 1
    if denominator <= 0:
        raise Refused('Exact certificate denominator must be positive')
    value = F(numerator, denominator)
    if exact_fraction_decimal(value) != text:
        raise Refused('Exact certificate fraction text is not canonical and reduced')
    return value
