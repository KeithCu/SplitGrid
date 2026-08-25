# SplitGrid

.PHONY: test test-all test-slow verify install-test

# Prefer a local venv so `make test` / `make verify` work without activating it.
PYTEST := $(if $(wildcard .venv/bin/pytest),.venv/bin/pytest,python3 -m pytest)
PIP := $(if $(wildcard .venv/bin/pip),.venv/bin/pip,pip)

install-test:
	$(PIP) install -e ".[test]"

# Default: skip slow (CrossHair) markers. Pure-Python flatten is enough.
test:
	$(PYTEST) -m "not slow"

test-all:
	$(PYTEST)

test-slow:
	$(PYTEST) -m slow

# deal contracts + hypothesis round-trips (excludes CrossHair subprocess).
verify:
	$(PYTEST) tests/test_serialization_verification.py tests/test_payload_codec_policy_verification.py -m "not slow" -q
