---
permalink: /docs/about/
title: "About"
multi-tool-gallery:
  - url: /assets/images/about/multi-tool-example-1.png
    image_path: /assets/images/about/multi-tool-example-1.png
    alt: "Multi-tool example picture"
  - url: /assets/images/about/multi-tool-example-2.png
    image_path: /assets/images/about/multi-tool-example-2.png
    alt: "Multi-tool example picture"
  - url: /assets/images/about/multi-tool-example-3.png
    image_path: /assets/images/about/multi-tool-example-3.png
    alt: "Multi-tool example picture"  
backtester-gallery:
  - url: /assets/images/about/backtester-example-1.png
    image_path: /assets/images/about/backtester-example-1.png
    alt: "Backtester example picture"
  - url: /assets/images/about/backtester-example-2.png
    image_path: /assets/images/about/backtester-example-2.png
    alt: "Backtester example picture"
  - url: /assets/images/about/backtester-example-3.png
    image_path: /assets/images/about/backtester-example-3.png
    alt: "Backtester example picture"  
backtest-reports-gallery:
  - url: /assets/images/about/backtest-report-1.png
    image_path: /assets/images/about/backtest-report-1.png
    alt: "Backtest report"
  - url: /assets/images/about/backtest-report-2.png
    image_path: /assets/images/about/backtest-report-2.png
    alt: "Backtest report"
toc: true
toc_sticky: true
toc_label: "On this page"
toc_icon: "cog"       
---

QF-Lib is a Python library that provides high quality tools for quantitative finance. Among the features, there are modules for portfolio construction, time series analysis, risk monitoring and diverse charting package. The library allows analyzing financial data in a convenient way, while providing a wide variety of tools for data processing and presentation of the results.

QF-Lib is a convenient environment for conducting your own analysis. The results will be presented in a practical form and include number of charts and statistical measures.  

An extensive part of the project is dedicated to backtesting investment strategies. The Backtester uses an event-driven architecture and simulates the events such as daily market opening or closing. Thanks to the architecture based on interfaces, it is easy to introduce custom settings. Tested strategies can consist of different alpha models, position-sizing techniques, risk management settings and can specify commission pricing or slippage models. After testing a strategy on historical data, user can put it into trading environment without any modifications.

# Multi-tool for any financial research
QF-Lib is a Python library that provides various tools for portfolio construction, time series analysis, and risk monitoring. It allows analysing financial data in a convenient way and provides a wide variety of tools to process data and to present the results.

## Tech Specs
- Flexible data sourcing (Bloomberg, Quandl, IB, Excel, local DB)
- Adapted data containers (Based on Pandas)
- Rich charting package
- Export to Excel, PDF or Email notifications

## Applications
- Financial analysis
- Building custom market indicators
- Financial products evaluation
- Portfolio construction
- Risk management
- Academic research
- Timeseries analysis

{% include gallery id="multi-tool-gallery" %}

# A powerful, event-driven Backtester
A large part of the project is dedicated to backtesting investment strategies. The Backtester uses an event-driven architecture and simulates events such as daily market opening or closing. It is designed to test and evaluate any custom investment strategy.

## Tech Specs
- Modular design (Alpha Models, Risk Management, Position Sizing)
- Easy to build custom strategies
- Tools to prevent look-ahead bias
- Detailed summary of the backtest
- Deploy strategies on testing or production environment

## Applications
- Financial engineering
- Investment strategy development evaluation and testing
- Risk management
- Financial analysis
- Verification of investment ideas

{% include gallery id="backtester-gallery" %}

# Examples of Backtest Reports

{% include gallery id="backtest-reports-gallery" %}
