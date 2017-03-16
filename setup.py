from setuptools import setup

setup(name='ninfo-client',
    version='0.3.0',
    zip_safe=True,
    include_package_data=True,
    py_modules = ["ninfo_client"],
    install_requires=[
        "requests",
    ],
    entry_points = {
        'console_scripts': [
            'ninfo-client = ninfo_client:main',
        ]
    }
)
