import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

"""
This is here in order to become a base for trade summary.
"""


def _plot_txt_trade(self, stats, ax=None, **kwargs):
    """
    Outputs the statistics for the trades.
    """
    def format_perc(x, pos):
        return '%.0f%%' % x

    if ax is None:
        ax = plt.gca()

    if 'positions' not in stats:
        num_trades = 0
        win_pct = "N/A"
        win_pct_str = "N/A"
        avg_trd_pct = "N/A"
        avg_win_pct = "N/A"
        avg_loss_pct = "N/A"
        max_win_pct = "N/A"
        max_loss_pct = "N/A"
    else:
        pos = stats['positions']
        num_trades = pos.shape[0]
        win_pct = pos[pos["trade_pct"] > 0].shape[0] / float(num_trades)
        win_pct_str = '{:.0%}'.format(win_pct)
        avg_trd_pct = '{:.2%}'.format(np.mean(pos["trade_pct"]))
        avg_win_pct = '{:.2%}'.format(np.mean(pos[pos["trade_pct"] > 0]["trade_pct"]))
        avg_loss_pct = '{:.2%}'.format(np.mean(pos[pos["trade_pct"] <= 0]["trade_pct"]))
        max_win_pct = '{:.2%}'.format(np.max(pos["trade_pct"]))
        max_loss_pct = '{:.2%}'.format(np.min(pos["trade_pct"]))

    y_axis_formatter = FuncFormatter(format_perc)
    ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

    max_loss_dt = 'TBD'  # pos[pos["trade_pct"] == np.min(pos["trade_pct"])].entry_date.values[0]
    avg_dit = '0.0'  # = '{:.2f}'.format(np.mean(pos.time_in_pos))

    ax.text(0.5, 8.9, 'Trade Winning %', fontsize=8)
    ax.text(9.5, 8.9, win_pct_str, fontsize=8, fontweight='bold', horizontalalignment='right')

    ax.text(0.5, 7.9, 'Average Trade %', fontsize=8)
    ax.text(9.5, 7.9, avg_trd_pct, fontsize=8, fontweight='bold', horizontalalignment='right')

    ax.text(0.5, 6.9, 'Average Win %', fontsize=8)
    ax.text(9.5, 6.9, avg_win_pct, fontsize=8, fontweight='bold', color='green', horizontalalignment='right')

    ax.text(0.5, 5.9, 'Average Loss %', fontsize=8)
    ax.text(9.5, 5.9, avg_loss_pct, fontsize=8, fontweight='bold', color='red', horizontalalignment='right')

    ax.text(0.5, 4.9, 'Best Trade %', fontsize=8)
    ax.text(9.5, 4.9, max_win_pct, fontsize=8, fontweight='bold', color='green', horizontalalignment='right')

    ax.text(0.5, 3.9, 'Worst Trade %', fontsize=8)
    ax.text(9.5, 3.9, max_loss_pct, color='red', fontsize=8, fontweight='bold', horizontalalignment='right')

    ax.text(0.5, 2.9, 'Worst Trade Date', fontsize=8)
    ax.text(9.5, 2.9, max_loss_dt, fontsize=8, fontweight='bold', horizontalalignment='right')

    ax.text(0.5, 1.9, 'Avg Days in Trade', fontsize=8)
    ax.text(9.5, 1.9, avg_dit, fontsize=8, fontweight='bold', horizontalalignment='right')

    ax.text(0.5, 0.9, 'Trades', fontsize=8)
    ax.text(9.5, 0.9, num_trades, fontsize=8, fontweight='bold', horizontalalignment='right')

    ax.set_title('Trade', fontweight='bold')
    ax.grid(False)
    ax.spines['top'].set_linewidth(2.0)
    ax.spines['bottom'].set_linewidth(2.0)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_ylabel('')
    ax.set_xlabel('')

    ax.axis([0, 10, 0, 10])
    return ax