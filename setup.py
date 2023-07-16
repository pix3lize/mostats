from setuptools import setup
# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "readme.md").read_text()

setup(
    name='mostats',
    version='1.0.9',
    author="Hendri Tjipto",
    url="https://github.com/pix3lize/mostats",
    description="Get the MongoDB database statistic to a local CSV file",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['mostats'],
        install_requires=['pymongo', 'pandas', 'argparse', 'openpyxl'],
    entry_points={
        'console_scripts': [
            'mostats=mostats.getCluster:main'
        ]
    },
        classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)