from enum import Enum


class WriteMode(Enum):
    """
    Class defining the access modes for writing to the file.
    """

    OPEN_EXISTING = 0           # open the file if it exists; if it doesn't, raise an error
    CREATE = 1                  # create a new file; if it does exist, raise an error
    CREATE_IF_DOESNT_EXIST = 2  # create a new file, if it doesn't exist; open an existing one if it does
