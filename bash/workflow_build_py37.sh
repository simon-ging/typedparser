# Generated given ../public/typedparser/.github/workflows/build_py37.yml workflow 'build for python 3.7'

# Exit on error
set -e

# Display commands as they are executed
set -x

# Enable conda access for bash
source ${CONDA_PATH}/etc/profile.d/conda.sh

# Conda setup
conda deactivate
conda update conda -n base -y
conda env remove -n env-py37 -y
conda create -n env-py37 -y
conda activate env-py37

# Conda install packages
conda env update -q -f etc/environment-py37.yml

# Pip install packages
python -m pip install --progress-bar off -U pip
pip install --progress-bar off -U -r requirements.txt
pip install --progress-bar off -U pytest pytest-cov pylint pytest-lazy-fixture

# Conda list
conda list

# Pip list
pip list

# Install code
python -m pip install -U -e .

# Run pytest
python -m pytest --cov

# Run pylint
pylint typedattr
pylint tests
