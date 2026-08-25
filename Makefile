# SplitGrid

.PHONY: test test-all test-slow verify install-test

install-test:
	pip install -e ".[test]"

# Default: skip slow (CrossHair) markers. Pure-Python flatten is enough.
test:
	pytest -m "not slow"

test-all:
	pytest

test-slow:
	pytest -m slow

# deal contracts + hypothesis round-trips (excludes CrossHair subprocess).
verify:
	pytest tests/test_serialization_verification.py tests/test_payload_codec_policy_verification.py -m "not slow" -q
