from datetime import datetime


def get_formatted_filename(reports_title, date: datetime, extension: str):
    str_date = date.strftime("%Y_%m_%d-%H%M")
    filename = "{str_date:s} {reports_title:s}.{extension:s}".format(str_date=str_date, reports_title=reports_title,
                                                                     extension=extension)
    # replace spaces with underscore
    filename = filename.replace(" ", "_")

    return filename
