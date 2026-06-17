=========
Tutorials
=========

This section is a hands-on guide to QF-Lib. Each tutorial is self-contained and
includes runnable code samples based on the ``demo_scripts`` folder in the repository.

**Suggested order for new users**

1. :doc:`tutorials/first_strategy_backtest` - implement and run your first strategy.
2. :doc:`tutorials/first_alpha_model` - use the Alpha Model abstraction.
3. :doc:`tutorials/customize_your_backtest` - add commissions and slippage.
4. :doc:`tutorials/analysing_backtest_results` - read tearsheets and trade statistics.
5. :doc:`tutorials/working_with_data` - connect data providers and configure settings.
6. :doc:`tutorials/portfolio_construction_tutorial` - optimise portfolio weights.

The remaining tutorials cover specialised topics (fast parameter testing, plotting,
and short how-to recipes).

Backtesting
-----------

.. toctree::
   :maxdepth: 1

   tutorials/first_strategy_backtest
   tutorials/first_alpha_model
   tutorials/customize_your_backtest
   tutorials/analysing_backtest_results
   tutorials/fast_alpha_model_testing
   tutorials/how_to_guides

Data and portfolio
------------------

.. toctree::
   :maxdepth: 1

   tutorials/working_with_data
   tutorials/portfolio_construction_tutorial

Visualisation
-------------

.. toctree::
   :maxdepth: 1

   tutorials/plotting_and_visualization

Architecture reference
----------------------

These pages explain how the backtester is structured. They complement the API reference.

.. toctree::
   :maxdepth: 1

   reference/backtest_flow
   reference/structure
   glossary
