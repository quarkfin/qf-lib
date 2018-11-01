import os

import numpy as np
from pandas import DataFrame

from qf_common.config.ioc import container
from qf_lib.analysis.trade_analysis.trade_analysis_sheet import TradeAnalysisSheet
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.miscellaneous.get_cached_value import cached_value
from qf_lib.settings import Settings


def get_data():
    start_date = str_to_date('2017-01-01')
    end_date = str_to_date('2017-12-31')

    trades_df = DataFrame(np.random.normal(0.01, 0.2, 200), columns=[TradeField.Return])
    trades_df.loc[0, TradeField.StartDate] = start_date
    trades_df.loc[199, TradeField.EndDate] = end_date
    return trades_df, 1


this_dir_path = os.path.dirname(os.path.abspath(__file__))
trades_df, nr_of_assets_traded = cached_value(get_data, os.path.join(this_dir_path, 'trade_analysis.cache'))


settings = container.resolve(Settings)  # type: Settings
pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter

trade_analysis_sheet = TradeAnalysisSheet(settings, pdf_exporter, trades_df,
                                          nr_of_assets_traded=nr_of_assets_traded,
                                          title="Sample trade analysis")
trade_analysis_sheet.build_document()
trade_analysis_sheet.save()

print("Finished")
