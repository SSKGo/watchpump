pip-licenses --with-license-file --no-license-path --format=plain-vertical --output-file OSS_LICENSES
python setup.py py2exe
rm OSS_LICENSES