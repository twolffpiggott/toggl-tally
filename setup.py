from setuptools import find_packages, setup

setup(
    name="toggl_tally",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "click==8.1.3",
        "holidays==0.19",
        "pytest==7.2.1",
        "pyyaml==6.0",
        "requests==2.28.2",
        "rich==13.3.2",
    ],
    entry_points="""
            [console_scripts]
            toggl-tally=toggl_tally.cli:toggl_tally
        """,
)
