import sys

import rapidfuzz

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QPushButton,
    QHBoxLayout, QVBoxLayout, QLineEdit
)

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

# class Table():
#     def __init__(self) -> None:
#
#         self.table = QTableView()

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("MyApp")
        # self.table = Table()
        button = QPushButton("Pressme")
        line = QLineEdit()

        upper_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        main_layout = QVBoxLayout()

        upper_layout.addWidget(button)
        bottom_layout.addWidget(line)

        main_layout.addLayout(upper_layout)
        main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)



def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()

if __name__ == "__main__":
    main()




