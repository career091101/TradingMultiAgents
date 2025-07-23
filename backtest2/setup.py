"""Setup configuration for backtest2 package"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="backtest2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.12",
    author="TradingAgents Team",
    description="Advanced backtesting framework for multi-agent trading systems",
    entry_points={
        "console_scripts": [
            "backtest2=backtest2.cli.main:main",
        ],
    },
)