.. image:: https://img.shields.io/github/workflow/status/saltstack/pytest-system-statistics/CI?style=plastic
   :target: https://github.com/saltstack/pytest-system-statistics/actions/workflows/testing.yml
   :alt: CI


.. image:: https://readthedocs.org/projects/pytest-system-statistics/badge/?style=plastic
   :target: https://pytest-system-statistics.readthedocs.io
   :alt: Docs


.. image:: https://img.shields.io/codecov/c/github/saltstack/pytest-system-statistics?style=plastic&token=CqV7t0yKTb
   :target: https://codecov.io/gh/saltstack/pytest-system-statistics
   :alt: Codecov


.. image:: https://img.shields.io/pypi/pyversions/pytest-system-statistics?style=plastic
   :target: https://pypi.org/project/pytest-system-statistics
   :alt: Python Versions


.. image:: https://img.shields.io/pypi/wheel/pytest-system-statistics?style=plastic
   :target: https://pypi.org/project/pytest-system-statistics
   :alt: Python Wheel


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=plastic
   :target: https://github.com/psf/black
   :alt: Code Style: black


.. image:: https://img.shields.io/pypi/l/pytest-system-statistics?style=plastic
   :alt: PyPI - License


..
   include-starts-here

================================
What is Pytest System Statistics
================================

It's a `pytest`_ plugin, extracted from `pytest-salt-factories`_,  which tracks the test
suite CPU and memory usage and, optionally, includes a report section including that data,
for example:

.. code-block:: text

   test_proc_sys_stats.py::test_one PASSED                                                [100%]
   ----------------------------------- Processes Statistics ------------------------------------
     .......... System - CPU: 17.80 %  MEM: 29.70 % (Virtual Memory)  SWAP:  12.80 %
     .. Test Suite Run - CPU:  0.00 %  MEM:  0.05 % (RSS)  MEM SUM: 0.09 % (RSS)  CHILD PROCS: 2
     ...... FooProcess - CPU:  0.00 %  MEM:  0.02 % (RSS)  MEM SUM: 0.03 % (RSS)  CHILD PROCS: 1

   ==================================== 1 passed in 0.34s ======================================


Install
=======

Installing Pytest System Statistics is as simple as:

.. code-block:: bash

   python -m pip install pytest-system-statistics


Usage
=====

Controlling the behaviour of the plugin is made through flags which are passed to `pytest`_.

.. code-block:: console

   --sys-stats             Print System CPU and MEM statistics after each test execution.
   --no-sys-stats          Do not print System CPU and MEM statistics after each test execution.
   --sys-stats-no-children Don't include child processes memory statistics.
   --sys-stats-uss-mem     Use the USS("Unique Set Size", memory unique to a process which
                           would be freed if the process was terminated) memory instead which
                           is more expensive to calculate.


Tracking Additional Processes
=============================

To include additional processes to track and report statistics against, simply add it to the
session scoped ``stats_processes`` fixture, for example:

.. code-block:: python

   @pytest.fixture
   def my_server_process(stats_processes):
       proc = subprocess.Popen(...)
       stats_processes.add("MyServerProcess", proc.pid)
       try:
           yield proc
       finally:
           stats_processes.remove("MyServerProcess")


Contributing
============

The pytest-system-statistics project team welcomes contributions from the community.
For more detailed information, refer to `CONTRIBUTING`_.

.. _pytest: https://pytest.org
.. _CONTRIBUTING: https://github.com/saltstack/pytest-system-statistics/blob/main/CONTRIBUTING.md
.. _pytest-salt-factories: https://github.com/saltstack/pytest-salt-factories

..
   include-ends-here

Documentation
=============

The full documentation can be seen `here <https://pytest-system-statistics.readthedocs.io>`_.
