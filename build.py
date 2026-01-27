#!/usr/bin/env python3
"""Build script for ziggy-pydust modules."""

import os
import subprocess
import sys


def build():
    """Build the Zig modules using ziggy-pydust."""
    os.chdir("app/src")

    # Run zig build with ziggy-pydust
    try:
        result = subprocess.run(
            ["zig", "build", "install", f"-Dpython-exe={sys.executable}", "-Doptimize=ReleaseSafe"],
            check=True,
            capture_output=True,
            text=True,
        )

        print("Zig build completed successfully")
        print(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    build()
