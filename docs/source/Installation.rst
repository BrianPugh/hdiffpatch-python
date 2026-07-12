Installation
============

hdiffpatch requires Python ``>=3.10`` and can be installed from pypi via:

.. code-block:: bash

   python -m pip install hdiffpatch


To install directly from github, you can run:

.. code-block:: bash

   python -m pip install git+https://github.com/BrianPugh/hdiffpatch-python.git

For development, it's recommended to use uv. The vendored C libraries are git submodules, so clone with ``--recursive``:

.. code-block:: bash

   git clone --recursive https://github.com/BrianPugh/hdiffpatch-python.git
   cd hdiffpatch-python
   uv sync

``uv sync`` builds the C extension; ``uv run python rebuild.py`` is only needed to rebuild after modifying the Cython or C sources.
