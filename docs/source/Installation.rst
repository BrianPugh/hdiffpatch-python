Installation
============

hdiffpatch requires Python ``>=3.10`` and can be installed from pypi via:

.. code-block:: bash

   python -m pip install hdiffpatch


To install directly from github, you can run:

.. code-block:: bash

   python -m pip install git+https://github.com/BrianPugh/hdiffpatch-python.git

For development, it's recommended to use uv:

.. code-block:: bash

   git clone https://github.com/BrianPugh/hdiffpatch-python.git
   cd hdiffpatch-python
   uv sync
   uv run python rebuild.py
