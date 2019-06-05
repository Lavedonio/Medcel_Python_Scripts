import os
import win32com.client


def run_macro(excel_file_name, module_name, macro_name):
    ''' https://stackoverflow.com/questions/19616205/running-an-excel-macro-via-python
    '''

    if os.path.exists(excel_file_name):
        xl = win32com.client.Dispatch("Excel.Application")
        xl.Workbooks.Open(os.path.abspath(excel_file_name))
        xl.Application.Run("{}!{}.{}".format(excel_file_name, module_name, macro_name))
        xl.Application.Save()  # if you want to save then uncomment this line and change delete the ", ReadOnly=1" part from the open function.
        xl.Application.Quit()  # Comment this out if your excel script closes
        del xl


def main():
    run_macro("excelsheet.xlsm", "modulename", "macroname")


if __name__ == "__main__":
    main()
