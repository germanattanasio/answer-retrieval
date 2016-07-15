#!/bin/bash

# Runs pylint only for Python 2.7.X
PYTHON_VERSION=$(python -c 'import sys; print (".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"
if [ $PYTHON_VERSION = '2.7' ]; then
  pylint server.py custom-scorer/retrieve_and_rank_scorer bin/python
fi
