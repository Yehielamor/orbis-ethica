from setuptools import setup, find_packages

setup(
    name="orbis-sdk",
    version="0.1.0",
    description="The Safety Layer for AI Agents",
    author="Orbis Ethica",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
