import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jtd",
    version="0.1.1",
    author="JSON Typedef Contributors",
    author_email="friends@jsontypedef.com",
    description="A Python implementation of JSON Type Definition",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jsontypedef/json-typedef-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',

    install_requires=["strict_rfc3339>=0.7"],
)
