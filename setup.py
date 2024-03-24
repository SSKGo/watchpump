# coding: utf-8
import os
import re
import shutil
import sys

from py2exe import freeze

dir_root = os.path.dirname(__file__)
dir_source = os.path.join(dir_root, "source")
dir_dist = os.path.join(dir_root, "dist")

# Create 3rd-party python library license information
with open(os.path.join(dir_root, "OSS_LICENSES"), "r", encoding="utf-8") as f:
    licenses = f.read()

# Constract python license information
with open(
    os.path.join(sys.base_prefix, "LICENSE_PYTHON.txt"), "r", encoding="utf-8"
) as f:
    python_license = f.read()
python_copyright = re.search(
    r"Copyright\s\(c\)[\s\S]*?All\sRights\sReserved", python_license
).group()
licenses += f"""python
{sys.version.split("|")[0].strip()}
{python_copyright}

{python_license}
"""

# Inject license information into python source code
description = f'oss_license_descriptions = """{licenses}"""'
file_path = os.path.join(dir_source, "oss_license_descriptions.py")
with open(file_path, "w", encoding="utf-8") as f:
    f.write(description)

# Compile with py2exe
# Delete dist before exe creation
shutil.rmtree(dir_dist)

sys.path.append(dir_source)
sys.argv.append("py2exe")

freeze(
    options={"py2exe": {"bundle_files": 1, "compressed": True}},
    windows=[{"script": os.path.join(dir_source, "app.py")}],
    zipfile=None,
)
