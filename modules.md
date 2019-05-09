# QF-Lib
-- todo paste short project description (I believe we already have one) --

This file contains an introduction for the QF-Lib project users. You will find here a short description 
of the library components. To get started, the [README.md](README.md) file will guide you through the installation 
process and will help you configure the library for your personal use.

## Project Modules
The main functionalities of the Library are presented below. To find more specific information please check the class
documentations or look at their usage in the `qf-lib/demo_scripts` catalogue.

### analysis
The components included in this catalogue are used to analyze strategy progress and generate files containing 
the analysis results. Examples of some documents created using these components are as follows:
* [TearsheetWithoutBenchmark](readme_example_files/tearsheet_without_benchmark.pdf),
* [LeverageAnalysisSheet](readme_example_files/leverage_analysis_sheet.pdf),
* [TimeseriesAnalysis](readme_example_files/timeseries_analysis.xlsx),
* [TradesAnalysis](readme_example_files/trades_analysis.csv),
* [ModelParamsEvaluator](readme_example_files/model_params_evaluator.pdf).

### backtesting


### common


### containers
Data structures that extend the functionality of `pandas Series`, `pandas DataFrame` and `numpy DataArray` containers 
and facilitate the computations performed on time-indexed structures of prices or price returns. Depending on the stored 
data, the 1D and 2D structures have their sub-types, such as e.g. `PricesSeries` or `SimpleReturnsDataFrame`.
The most generic 1D and 2D types are `QFSeries` and `QFDataFrame`. Any time-indexed `DataFrame` or `Series` 
can be cast to a specific type using the `cast_dataframe` and `cast_series` functions.

### data_providers

### indicators
Market indicators that can be implemented in strategies or used for the analysis.

### interactive_brokers
This catalogue contains an interface which allows to communicate with the Interactive Brokers platform. The `IBBroker` 
class can be used in the live trading of your strategy.

### plotting
To make plotting easier we implemented a lot of chart templates along with some easy-to-use decorators. Examples of their 
use are shown in the `qf-lib/demo_scripts/charts` catalogue.

### portfolio_construction
The components in this catalogue can be helpful in the process of portfolio construction - they allow to calculate
the covariance matrix of assets and take it as input to build the portfolio according to suggested models. 
The construction process involves covariance matrix optimization with one of the implemented optimizers.

### publishers
They allow for publishing the documents (i.a. by email). 

### technical_analysis
This catalogue contains tools which facilitate the usage of TA-Lib functions in the project.

### testing_tools
Basic tools that are used in software testing. They include functions that allow e.g. comparing data structures 
or creating sample column names for the test containers.
