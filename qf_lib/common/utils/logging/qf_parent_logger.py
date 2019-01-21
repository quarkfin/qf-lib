import logging

qf_logger = logging.getLogger("qf")

ib_logger = logging.getLogger("ib")

"""
This is the preferred way of using logger in the project. All loggers are the children of QF and therefore 
can be filtered in the logging settings. 

Usage: 

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

Now in the class you can call 
    self.logger = qf_logger.getChild(self.__class__.__name__)
which will create an instance of a logger. 

"""