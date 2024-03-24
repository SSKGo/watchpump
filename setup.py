# coding: utf-8
import os
import re
import sys

from py2exe import freeze

# Create license information
dir_file = os.path.dirname(__file__)

with open(os.path.join(dir_file, "OSS_LICENSES"), "r", encoding="utf-8") as f:
    licenses = f.read()

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


description = f'oss_license_descriptions = """{licenses}"""'

with open(
    os.path.join(dir_file, "source", "oss_license_descriptions.py"),
    "w",
    encoding="utf-8",
) as f:
    f.write(description)

# Compile with py2exe
dir_main = os.path.join(os.path.dirname(__file__), "source")

sys.path.append(dir_main)
sys.argv.append("py2exe")

freeze(
    options={"py2exe": {"bundle_files": 1, "compressed": True}},
    windows=[{"script": os.path.join(dir_main, "watchdog_s3_uploader.py")}],
    zipfile=None,
)
