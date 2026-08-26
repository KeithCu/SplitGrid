# SplitGrid

.PHONY: test test-all test-slow verify install-test bench bench-child profile-pack

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

PYTHON := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

# Asymmetric host/child serialization bench (needs numpy).
bench:
	$(PYTHON) scripts/bench_serialization.py --direction both

bench-child:
	$(PYTHON) scripts/bench_serialization.py --child-only

profile-pack:
	$(PYTHON) scripts/profile_pack.py
	$(PYTHON) scripts/profile_nones.py
