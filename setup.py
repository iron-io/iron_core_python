from setuptools import setup

setup(
        name = "iron-core",
        py_modules = ["iron_core"],
        install_requires=["iso8601"],
        version = "0.1.0",
        description = "Universal classes and methods for Iron.io API wrappers to build on.",
        author = "Iron.io",
        author_email = "thirdparty@iron.io",
        url = "https://www.github.com/iron-io/iron_core_python",
        keywords = ["Iron.io"],
        classifiers = [
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
                "Intended Audience :: Developers",
                "Operating System :: OS Independent",
                "Development Status :: 2 - Pre-Alpha",
                "License :: OSI Approved :: BSD License",
                "Natural Language :: English",
                "Topic :: Internet",
                "Topic :: Internet :: WWW/HTTP",
                "Topic :: Software Development :: Libraries :: Python Modules",

        ],
        long_description = """\
Iron.io common library
----------------------

This package offers common functions for Iron.io APIs and services. It does not wrap 
any APIs or contain API-specific features, but serves as a common base that wrappers
may be built on. Users looking for API wrappers should instead look at 
iron_worker_python and iron_worker_mq."""
)
