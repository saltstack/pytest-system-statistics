# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Tests related to processes system statistics enabled by the `--sys-stats` flag.
"""
import sys
import textwrap

import pytest


def test_sys_stats_not_verbose(pytester):
    pytester.makepyfile(
        """
        def test_one():
            assert True
        """
    )
    res = pytester.runpytest("--sys-stats")
    res.assert_outcomes(passed=1)
    no_match_lines = [
        "* Processes Statistics *",
        "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
        "* Test Suite Run  -  CPU: * %   MEM: * % (RSS)*",
    ]
    for line in no_match_lines:
        res.stdout.no_fnmatch_line(line)


def test_sys_stats_not_verbose_enough(pytester):
    pytester.makepyfile(
        """
        def test_one():
            assert True
        """
    )
    res = pytester.runpytest("-v", "--sys-stats")
    res.assert_outcomes(passed=1)
    res.stdout.fnmatch_lines(
        [
            "* PASSED*",
            "* 1 passed in *",
        ]
    )
    no_match_lines = [
        "* Processes Statistics *",
        "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
        "* Test Suite Run  -  CPU: * %   MEM: * % (RSS)*",
    ]
    for line in no_match_lines:
        res.stdout.no_fnmatch_line(line)


def test_sys_stats_disabled(pytester):
    pytester.makepyfile(
        """
        def test_one():
            assert True
        """
    )
    res = pytester.runpytest("-vv", "--sys-stats", "--no-sys-stats")
    res.assert_outcomes(passed=1)
    res.stdout.fnmatch_lines(
        [
            "* PASSED*",
            "* 1 passed in *",
        ]
    )
    no_match_lines = [
        "* Processes Statistics *",
        "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
        "* Test Suite Run  -  CPU: * %   MEM: * % (RSS)*",
    ]
    for line in no_match_lines:
        res.stdout.no_fnmatch_line(line)


def test_basic_sys_stats(pytester):
    pytester.makepyfile(
        """
        def test_one():
            assert True
        """
    )
    res = pytester.runpytest("-vv", "--sys-stats")
    res.assert_outcomes(passed=1)
    res.stdout.fnmatch_lines(
        [
            "* PASSED*",
            "* Processes Statistics *",
            "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
            "* Test Suite Run  -  CPU: * %   MEM: * % (RSS)*",
            "* 1 passed in *",
        ]
    )


@pytest.mark.skip_on_freebsd
def test_basic_sys_stats_uss(pytester):
    pytester.makepyfile(
        """
        def test_one():
            assert True
        """
    )
    res = pytester.runpytest("-vv", "--sys-stats", "--sys-stats-uss-mem")
    res.assert_outcomes(passed=1)
    res.stdout.fnmatch_lines(
        [
            "* PASSED*",
            "* Processes Statistics *",
            "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
            "* Test Suite Run  -  CPU: * %   MEM: * % (USS)*",
            "* 1 passed in *",
        ]
    )


def test_proc_sys_stats(pytester, tmp_path):
    executable = sys.executable
    script1 = tmp_path / "script1.py"
    script1.write_text(
        textwrap.dedent(
            """\
        import time
        import multiprocessing

        if __name__ == '__main__':
            multiprocessing.freeze_support()
            try:
                while True:
                    time.sleep(0.25)
            except Exception:
                pass
        """
        )
    )
    script2 = tmp_path / "script2.py"
    script2.write_text(
        textwrap.dedent(
            """\
        import sys
        import subprocess
        import multiprocessing

        if __name__ == '__main__':
            multiprocessing.freeze_support()
            proc = subprocess.run([r"{}", r"{}"])
        """.format(
                executable, script1
            )
        )
    )
    pytester.makepyfile(
        """
        import sys
        import pytest
        import subprocess
        import psutil
        import time

        @pytest.fixture
        def foo_process(stats_processes):
            proc = subprocess.Popen([r"{}", r"{}"])
            try:
                time.sleep(0.25)
                assert psutil.Process(proc.pid).children()
                stats_processes.add("FooProcess", proc.pid)
                yield proc
            finally:
                stats_processes.remove("FooProcess")
                proc.terminate()

        def test_one(foo_process):
            assert True
        """.format(
            executable, script2
        )
    )
    res = pytester.runpytest("-vv", "--sys-stats")
    res.assert_outcomes(passed=1)
    res.stdout.fnmatch_lines(
        [
            "* PASSED*",
            "* Processes Statistics *",
            "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
            "* Test Suite Run  -  CPU: * %   MEM: * % (RSS) * CHILD PROCS: *",
            "* FooProcess  -  CPU: * %   MEM: * % (RSS) * CHILD PROCS: *",
            "* 1 passed in *",
        ]
    )


def test_proc_sys_stats_no_children(pytester, tmp_path):
    executable = sys.executable
    script1 = tmp_path / "script1.py"
    script1.write_text(
        textwrap.dedent(
            """\
        import time
        import multiprocessing

        if __name__ == '__main__':
            multiprocessing.freeze_support()
            try:
                while True:
                    time.sleep(0.25)
            except Exception:
                pass
        """
        )
    )
    script2 = tmp_path / "script2.py"
    script2.write_text(
        textwrap.dedent(
            """\
        import sys
        import subprocess
        import multiprocessing

        if __name__ == '__main__':
            multiprocessing.freeze_support()
            proc = subprocess.run([r"{}", r"{}"])
        """.format(
                executable, script1
            )
        )
    )
    pytester.makepyfile(
        """
        import sys
        import pytest
        import subprocess
        import psutil
        import time

        @pytest.fixture
        def foo_process(stats_processes):
            proc = subprocess.Popen([r"{}", r"{}"])
            try:
                time.sleep(0.25)
                assert psutil.Process(proc.pid).children()
                stats_processes.add("FooProcess", proc.pid)
                yield proc
            finally:
                stats_processes.remove("FooProcess")
                proc.terminate()

        def test_one(foo_process):
            assert True
        """.format(
            executable, script2
        )
    )
    res = pytester.runpytest("-vv", "--sys-stats", "--sys-stats-no-children")
    res.assert_outcomes(passed=1)
    res.stdout.fnmatch_lines(
        [
            "* PASSED*",
            "* Processes Statistics *",
            "* System  -  CPU: * %   MEM: * % (Virtual Memory)*",
            "* Test Suite Run  -  CPU: * %   MEM: * % (RSS)*",
            "* FooProcess  -  CPU: * %   MEM: * % (RSS)*",
            "* 1 passed in *",
        ]
    )
    no_match_lines = [
        "* Test Suite Run  -  CPU: * %   MEM: * % (RSS) * CHILD PROCS: *",
        "* FooProcess  -  CPU: * %   MEM: * % (RSS) * CHILD PROCS: *",
    ]
    for line in no_match_lines:
        res.stdout.no_fnmatch_line(line)
