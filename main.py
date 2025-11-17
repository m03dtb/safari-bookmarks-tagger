import sys

import rapidfuzz

from PySide6.QtCore import QSize, Qt, QAbstractTableModel
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit,
    QTableView, QTableWidget, QListWidget, QTableWidgetItem
)
# from PySide6.QtGui import QFocusEvent

# def get_sorted_dictionary(mylist, compared_string):
#     dict_of_results = {}
#     for element in mylist:
#         ratio_res = rapidfuzz.fuzz.partial_ratio(element, compared_string)
#         dict_of_results[element] = ratio_res
#
#     sorted_dict_of_results = dict(
#         sorted(dict_of_results.items(), key=lambda item: item[1], reverse=True)
#     )
#
#     # for key, value in sorted_dict_of_results.items():
#     #     print(f"K: {key}, V: {value}")
#     return sorted_dict_of_results
#
#
#     mylist= ["num1", "num2", "num3","albert","chrissy", "number", "num2b", "numb2", "num4a", "num4b", "nmb41", "num41"]
#     compared_string ="num41"
#     sorted_dict = get_sorted_dictionary(mylist, compared_string)
#
#     for k,v in sorted_dict.items():
#         print(f"{k} -> {v}")


class Table():
    def __init__(self, mydict) -> None:
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
       return set(self.mydict.values())

class LineEdit(QLineEdit):
    def __init__(self, table_obj, dropdown, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_obj = table_obj
        self.dropdown = dropdown

    def focusInEvent(self, event):
        super().focusInEvent(event)
        all_tags = self.table_obj.get_all_tags()
        self.dropdown.clear()
        for tag in all_tags:
            self.dropdown.addItem(tag)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.mydict = self.return_input_list()
        self.setWindowTitle("MyApp")
        self.table = Table(self.mydict)
        self.button = QPushButton("Pressme")
        self.dropdown = QListWidget()
        self.line = LineEdit(self.table, self.dropdown)

        # self.dropdown.addItem("California")

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

    def on_focus(self):
        print("jelllo")

def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()

if __name__ == "__main__":
    main()




