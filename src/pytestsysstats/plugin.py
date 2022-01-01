# Copyright 2021-2022 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Process statistics PyTest plugin interface.
"""
import os
from collections import OrderedDict
from typing import Dict
from typing import ItemsView
from typing import Iterator
from typing import Optional
from typing import Union

import attr
import psutil
import pytest
from pytestskipmarkers.utils import platform

if False:  # TYPE_CHECKING  # pylint: disable=using-constant-test
    # pylint: disable=import-error,unused-import,no-name-in-module
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import SubRequest
    from _pytest.main import Session
    from _pytest.reporter import TerminalReporter
    from _pytest.reports import TestReport

    # pylint: enable=import-error,unused-import,no-name-in-module


@attr.s(kw_only=True, slots=True, hash=True)
class StatsProcesses:
    """
    Class which holds the processes being tracked.
    """

    processes = attr.ib(
        init=False, default=attr.Factory(OrderedDict), hash=False
    )  # type: Dict[str, psutil.Process]

    def add(self, display_name: str, process: Union[int, psutil.Process]) -> None:
        """
        Add a process to track.
        """
        if isinstance(process, int):
            # This is a process pid
            process = psutil.Process(process)
        self.processes[display_name] = process

    def remove(self, display_name: str) -> None:
        """
        Remove tracked process.
        """
        self.processes.pop(display_name, None)

    def items(self) -> ItemsView[str, psutil.Process]:
        """
        Return the tracked items.
        """
        return self.processes.items()

    def __iter__(self) -> Iterator[str]:
        """
        Iterate over tracked processes.
        """
        return iter(self.processes)


@attr.s(kw_only=True, slots=True, hash=True)
class SystemStatsReporter:
    """
    Tracked processes pytest reporter.
    """

    config = attr.ib(repr=False, hash=False)  # type: "Config"
    stats_processes = attr.ib(repr=False, hash=False)  # type: Optional[StatsProcesses]
    terminalreporter = attr.ib(repr=False, hash=False)  # type: "TerminalReporter"
    show_sys_stats = attr.ib(init=False)  # type: bool
    sys_stats_no_children = attr.ib(init=False)  # type: bool
    sys_stats_mem_type = attr.ib(init=False)  # type: str

    def __attrs_post_init__(self) -> None:
        """
        Initialization routines, port attrs initialization.
        """
        self.show_sys_stats = (
            self.config.getoption("--sys-stats") is True
            and self.config.getoption("--no-sys-stats") is False
        )
        self.sys_stats_no_children = self.config.getoption("--sys-stats-no-children") is True
        if self.config.getoption("--sys-stats-uss-mem") is True:
            self.sys_stats_mem_type = "uss"
            if platform.is_freebsd():
                # FreeBSD doesn't apparently support uss
                self.sys_stats_mem_type = "rss"
        else:
            self.sys_stats_mem_type = "rss"

    @pytest.hookimpl(trylast=True)  # type: ignore[misc]
    def pytest_runtest_logreport(self, report: "TestReport") -> None:
        """
        Pytest logreport hook.
        """
        if self.terminalreporter.verbosity <= 0:
            return

        if report.when != "call":
            return

        if self.show_sys_stats is False:
            return

        if self.terminalreporter.verbosity > 1:
            assert self.stats_processes  # Make mypy happy
            remove_from_stats = set()
            self.terminalreporter.ensure_newline()
            self.terminalreporter.section("Processes Statistics", sep="-", bold=True)
            left_padding = len(max(["System"] + list(self.stats_processes), key=len))
            template = (
                "  ...{dots}  {name}  -  CPU: {cpu:6.2f} %   MEM: {mem:6.2f} % (Virtual Memory)"
            )

            stats = {
                "name": "System",
                "dots": "." * (left_padding - len("System")),
                "cpu": psutil.cpu_percent(),
                "mem": psutil.virtual_memory().percent,
            }

            swap = psutil.swap_memory().percent
            if swap > 0:
                template += "  SWAP: {swap:6.2f} %"
                stats["swap"] = swap

            template += "\n"
            self.terminalreporter.write(template.format(**stats))

            template = "  ...{dots}  {name}  -  CPU: {cpu:6.2f} %   MEM: {mem:6.2f} % ({m_type})"
            children_template = (
                template + "   MEM SUM: {c_mem} % ({m_type})   CHILD PROCS: {c_count}\n"
            )
            no_children_template = template + "\n"
            for name, psproc in self.stats_processes.items():
                template = no_children_template
                dots = "." * (left_padding - len(name))
                pids = []
                try:
                    with psproc.oneshot():
                        stats = {
                            "name": name,
                            "dots": dots,
                            "cpu": psproc.cpu_percent(),
                            "mem": psproc.memory_percent(self.sys_stats_mem_type),
                            "m_type": self.sys_stats_mem_type.upper(),
                        }
                        if self.sys_stats_no_children is False:
                            pids.append(psproc.pid)
                            children = psproc.children(recursive=True)
                            if children:
                                template = children_template
                                stats["c_count"] = 0
                                c_mem = stats["mem"]
                                for child in children:
                                    if child.pid in pids:  # pragma: no cover
                                        continue
                                    pids.append(child.pid)
                                    if not psutil.pid_exists(child.pid):  # pragma: no cover
                                        remove_from_stats.add(name)
                                        continue
                                    try:
                                        c_mem += child.memory_percent(self.sys_stats_mem_type)
                                        stats["c_count"] += 1
                                    except (
                                        psutil.AccessDenied,
                                        psutil.NoSuchProcess,
                                    ):  # pragma: no cover
                                        continue
                                if stats["c_count"]:
                                    stats["c_mem"] = "{:6.2f}".format(c_mem)
                                else:  # pragma: no cover
                                    template = no_children_template
                        self.terminalreporter.write(template.format(**stats))
                except psutil.NoSuchProcess:  # pragma: no cover
                    remove_from_stats.add(name)
                    continue
            if remove_from_stats:  # pragma: no cover
                for name in remove_from_stats:
                    self.stats_processes.remove(name)


def pytest_addoption(parser: "Parser") -> None:
    """
    Register argparse-style options and ini-style config values.
    """
    output_options_group = parser.getgroup("Output Options")
    output_options_group.addoption(
        "--sys-stats",
        default=False,
        action="store_true",
        help="Print System CPU and MEM statistics after each test execution.",
    )
    output_options_group.addoption(
        "--no-sys-stats",
        default=False,
        action="store_true",
        help="Do not print System CPU and MEM statistics after each test execution.",
    )
    output_options_group.addoption(
        "--sys-stats-no-children",
        default=False,
        action="store_true",
        help="Don't include child processes memory statistics.",
    )
    output_options_group.addoption(
        "--sys-stats-uss-mem",
        default=False,
        action="store_true",
        help='Use the USS("Unique Set Size", memory unique to a process which would be freed if the process was '
        "terminated) memory instead which is more expensive to calculate.",
    )


@pytest.hookimpl(trylast=True)  # type: ignore[misc]
def pytest_sessionstart(session: "Session") -> None:
    """
    Pytest session start routines.
    """
    if (
        session.config.getoption("--sys-stats") is True
        and session.config.getoption("--no-sys-stats") is False
    ):
        stats_processes_instance = StatsProcesses()
        stats_processes_instance.add("Test Suite Run", os.getpid())
    else:
        stats_processes_instance = None

    session.config.pluginmanager.register(stats_processes_instance, "sysstats-processes")

    terminalreporter = session.config.pluginmanager.getplugin(
        "terminalreporter"
    )  # type: "TerminalReporter"
    sys_stats_reporter = SystemStatsReporter(
        config=session.config,
        stats_processes=stats_processes_instance,
        terminalreporter=terminalreporter,
    )
    session.config.pluginmanager.register(sys_stats_reporter, "sysstats-reporter")


@pytest.fixture(scope="session")  # type: ignore[misc]
def stats_processes(request: "SubRequest") -> StatsProcesses:
    """
    Session scoped process statistics tracker.
    """
    plugin = request.config.pluginmanager.get_plugin("sysstats-processes")  # type: StatsProcesses
    return plugin
