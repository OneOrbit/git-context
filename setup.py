from setuptools import setup, find_packages

setup(
    name="git-context",
    version="0.1.0",
    description="Autonomous Living Memory & Rule Compiler for AI Coding Assistants (Cursor, Copilot, Claude Code)",
    author="GitContext Team",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "git-context=git_context.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
