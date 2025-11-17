import sys

import rapidfuzz

from PySide6.QtCore import QSize, Qt, QAbstractTableModel
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit,
    QTableView, QTableWidget, QListWidget, QTableWidgetItem
)
# from PySide6.QtGui import QFocusEvent


# class FuzzySearch():
#     def __init__(self, set_of_tags):
#         super().__init__()
#
#     def get_sorted_dictionary(mylist, compared_string, set_of_tags):
#         dict_of_results = {}
#         for element in mylist:
#             ratio_res = rapidfuzz.fuzz.partial_ratio(element, compared_string)
#             dict_of_results[element] = ratio_res
#
#         sorted_dict_of_results = dict(
#             sorted(dict_of_results.items(), key=lambda item: item[1], reverse=True)
#         )
#         return sorted_dict_of_results

class Table():
    def __init__(self, mydict, line) -> None:
        super().__init__()
        self.table = QTableWidget()
        self.mydict = mydict
        table  = self.table 
        table.setRowCount(len(mydict.keys()))
        header_labels = ["Name", "Tags"]
        table.setColumnCount(len(header_labels))
        table.setHorizontalHeaderLabels(header_labels)

        for row, (key, value) in enumerate(mydict.items()):
            table.setItem(row, 0, QTableWidgetItem(key))
            table.setItem(row, 1, QTableWidgetItem(value))

    def get_all_tags(self):
        set_of_tags = set(self.mydict.values())
        return set_of_tags

    def filter_table(self, line):
        self.line = line 
        self.line.clear()
        self.line.textChanged.connect(self.on_filter_table)

    def on_filter_table(self):
        user_input = self.line.text()
        print("USER INPUT: ", user_input)
        


class LineEdit(QLineEdit):
    def __init__(self, table_obj, dropdown, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_obj = table_obj
        self.dropdown = dropdown

    def focusInEvent(self, event):
        super().focusInEvent(event)
        all_tags = self.table_obj.get_all_tags()
        self.dropdown.clear()
        self.dropdown.show()
        for tag in all_tags:
            self.dropdown.addItem(tag)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.dropdown.hide()

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.line = None 
        self.mydict = self.return_input_list()
        self.setWindowTitle("MyApp")
        self.table = Table(self.mydict, self.line)
        self.button = QPushButton("Pressme")
        self.dropdown = QListWidget()
        self.dropdown.hide()
        self.line = LineEdit(self.table, self.dropdown)

        # self.dropdown.addItem("California")
        self.table.filter_table(self.line)

        # LAYOUT 
        upper_layout = QHBoxLayout()
        middle_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()

        main_layout = QVBoxLayout()

        upper_layout.addWidget(self.button)
        middle_layout.addWidget(self.table.table)
        bottom_layout.addWidget(self.line)
        bottom_layout.addWidget(self.dropdown)

        main_layout.addLayout(upper_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


    def return_input_list(self):
        mylist= ["el_num1", "el_num2", "el_num3","el_albert","el_chrissy",
                "el_number", "el_num2b", "el_numb2", "el_num4a", "el_num4b",
                "el_nmb41", "el_num41"]

        mytags =  ["num1", "num2", "num3","num1","num2",
                   "number", "num2b", "numb2", "anum2", "num4b",
                   "nmb41", "num41"]

        dict_list_tags = {}
        for elem, tag in zip(mylist, mytags) :
            dict_list_tags[elem] = tag

        return dict_list_tags


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()

if __name__ == "__main__":
    main()




