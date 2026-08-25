from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext
import os
import platform
import sys

# Determine architecture flags (same policy as WriterAgent native/writeragent_vec).
extra_compile_args = []
system = platform.system()
machine = platform.machine().lower()

if system == "Windows":
    extra_compile_args.append("/O2")
else:
    extra_compile_args.append("-O3")

# Only apply SPLITGRID_ARCH / WRITERAGENT_ARCH logic on Linux x86_64.
# Generic x86-64 (not v3): flatten is memory-bound; SIMD floors buy ~1%.
if system == "Linux" and (machine == "x86_64" or machine == "amd64"):
    arch = os.environ.get("SPLITGRID_ARCH") or os.environ.get("WRITERAGENT_ARCH", "x86-64")
    extra_compile_args.append(f"-march={arch}")

extensions = [
    Extension(
        "splitgrid.pack",
        ["src/splitgrid/pack.pyx"],
        extra_compile_args=extra_compile_args,
    )
]


class OptionalBuildExt(_build_ext):
    """Build the Cython flatten accelerator when a compiler is present.

    Missing compiler / Cython must not fail ``pip install``: the codec falls
    back to the proven pure-Python flatten.
    """

    def build_extension(self, ext):
        try:
            super().build_extension(ext)
        except Exception as exc:  # pragma: no cover - environment dependent
            sys.stderr.write(
                f"WARNING: splitgrid Cython accelerator not built ({ext.name}): {exc}\n"
                "         Pure-Python flatten will be used.\n"
            )


def _ext_modules():
    try:
        from Cython.Build import cythonize
    except ImportError:
        sys.stderr.write("WARNING: Cython not installed; skipping splitgrid.pack extension.\n")
        return []
    return cythonize(
        extensions,
        language_level=3,
        compiler_directives={
            "emit_code_comments": False,
        },
    )


setup(
    ext_modules=_ext_modules(),
    cmdclass={"build_ext": OptionalBuildExt},
)
