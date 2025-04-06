import re

_regexCache = {}

def _get_or_compile(pattern, flags=0):
    key = pattern + '^$^$FLAGS=' + str(flags)
    if key not in _regexCache:
        _regexCache[key] = re.compile(pattern, flags)
    return _regexCache[key]

def search(pattern, subject, flags=0):
    return _get_or_compile(pattern, flags).search(subject)

def match(pattern, subject, flags=0):
    return _get_or_compile(pattern, flags).match(subject)

def fullmatch(pattern, subject, flags=0):
    return _get_or_compile(pattern, flags).fullmatch(subject)

def sub(pattern, repl, subject, count=0, flags=0):
    return _get_or_compile(pattern, flags).sub(repl, subject, count)
