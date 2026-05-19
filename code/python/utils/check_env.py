"""
T02: Python 环境验证脚本
验证所有关键包可正常导入并报告版本号
"""

import importlib
import sys

def check_version(pkg_name, import_name=None):
    if import_name is None:
        import_name = pkg_name
    mod = importlib.import_module(import_name)
    version = getattr(mod, '__version__', 'unknown')
    return version

# 1. 验证 econml 核心导入
from econml.grf import CausalForest
from econml.dml import LinearDML
from econml.policy import PolicyTree

# 2. 验证其他依赖包
import pyreadstat
import matplotlib
import scipy
import pandas
import numpy
import sklearn

# 3. 报告版本
import econml
print(f'econml:     {econml.__version__}')
print(f'pyreadstat: {pyreadstat.__version__}')
print(f'matplotlib: {matplotlib.__version__}')
print(f'scipy:      {scipy.__version__}')
print(f'pandas:     {pandas.__version__}')
print(f'numpy:      {numpy.__version__}')
print(f'sklearn:    {sklearn.__version__}')
print(f'python:     {sys.version}')

# 4. econml 版本检查（须 >= 0.13.0）
from packaging import version as pkg_version
econml_ver = econml.__version__
assert pkg_version.parse(econml_ver) >= pkg_version.parse('0.13.0'), \
    f"econml 版本 {econml_ver} < 0.13.0，需升级"

print('环境检查通过')
