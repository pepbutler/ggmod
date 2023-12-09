import sys
import setuptools

LONG_DESC = open('README.md').read()

setuptools.setup(
    name="ggmod",
    # version=VERSION,
    author="joe",
    author_email="joe@momma.com",
    description="Download and install guilty gear mods",
    long_description_content_type="text/markdown",
    long_description=LONG_DESC,
    license="MIT",
    packages=["ggmod"],
    entry_points={"console_scripts": ["ggmod=ggmod.main:main"]},
    python_requires=">=3.5",
    install_requires=[
        "PyPAKParser==1.2.0",
        "requests>=2.31.0",
    ],
    #test_suite="tests",
    #include_package_data=True,
    zip_safe=False)
