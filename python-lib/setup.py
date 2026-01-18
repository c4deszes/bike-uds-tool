from setuptools import setup, find_packages
import os

with open(os.path.join(os.path.dirname(__file__), "..", "library.properties"), "r") as f:
    version_str = "0.0.0"  # Default version in case of failure to read
    for line in f:
        if line.startswith("version="):
            version_str = line.strip().split("=", 1)[1]
            break

with open("README.md", "r") as fh:
    long_description = fh.read()
setup(
    name='line-uds',
    version=version_str,
    author="Balazs Eszes",
    author_email="c4deszes@gmail.com",
    description="Diagnostic extension for LINE devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/c4deszes/bike-uds-tool",
    packages=find_packages(),
    package_data={'': ['*.jinja2']},
    include_package_data=True,
    license='MIT',
    keywords=['LINE', 'UDS', 'Diagnostics'],
    install_requires=[
        'line-protocol'
    ],
    extras_require={
        'dev': [
            # Packaging
            "setuptools",
            "wheel",
            "twine",
            # Testing
            "pytest",
            "pytest-cov",
            # Linting
            "pylint",
            "flake8"
        ]
    },
    python_requires='!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4',
    entry_points={
        'console_scripts': [
            'line-uds-gencode=line_uds.codegen.generator:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Documentation": "https://c4deszes.github.io/bike-flash-tool/",
        "Source Code": "https://github.com/c4deszes/bike-flash-tool",
    }
)
