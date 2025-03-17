Contributing
============

We love your input! We want to make contributing to TorrentDirectories as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

Development Process
-------------------

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

Code Style
----------

We use several tools to maintain code quality:

- `black` for code formatting
- `isort` for import sorting
- `mypy` for type checking
- `ruff` for linting

Before submitting a pull request, ensure your code passes all checks:

.. code-block:: bash

    # Format code
    black .
    isort .

    # Run type checker
    mypy src tests

    # Run linter
    ruff check .

    # Run tests
    pytest

Pull Request Process
--------------------

1. Update the README.md with details of changes to the interface, if applicable.
2. Update the docs with any new features or changes in behavior.
3. The PR may be merged once you have the sign-off of at least one other developer.

Testing
-------

We use pytest for testing. To run the tests:

.. code-block:: bash

    # Run all tests
    pytest

    # Run with coverage report
    pytest --cov=src tests/

    # Run only integration tests
    pytest tests/torrent/cli/test_commands_integration.py

Documentation
-------------

We use Sphinx for documentation. To build the docs:

.. code-block:: bash

    cd docs
    make html

The documentation will be built in `docs/_build/html`. 