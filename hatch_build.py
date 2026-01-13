import sys
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from pydust import buildzig


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        import os

        os.chdir("app/src")
        buildzig.zig_build(["install", f"-Dpython-exe={sys.executable}", "-Doptimize=ReleaseSafe"])
