"""UI Window Generator."""

# Form implementation generated from reading ui file 'ui_raw.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class UiMainWindow:
    """UI Main Window."""

    def setup_ui(self, main_window: QtWidgets.QMainWindow) -> None:
        """Set up the UI."""
        main_window.setObjectName("MainWindow")
        main_window.resize(1333, 793)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap("images/gui_icon.ico"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off
        )
        main_window.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(parent=main_window)
        self.centralwidget.setObjectName("centralwidget")
        self.vertical_layout_3 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.vertical_layout_3.setObjectName("verticalLayout_3")
        self.table_title_label = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(17)
        font.setBold(True)
        self.table_title_label.setFont(font)
        self.table_title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.table_title_label.setObjectName("table_title_label")
        self.vertical_layout_3.addWidget(self.table_title_label)
        self.horizontal_layout = QtWidgets.QHBoxLayout()
        self.horizontal_layout.setObjectName("horizontalLayout")
        self.vertical_layout = QtWidgets.QVBoxLayout()
        self.vertical_layout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.vertical_layout.addWidget(self.label_2)
        self.stage_pos_line_edit = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.stage_pos_line_edit.setReadOnly(True)
        self.stage_pos_line_edit.setObjectName("stage_pos_line_edit")
        self.vertical_layout.addWidget(self.stage_pos_line_edit)
        self.stage_pos_slider = QtWidgets.QSlider(parent=self.centralwidget)
        self.stage_pos_slider.setMaximum(1000)
        self.stage_pos_slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.stage_pos_slider.setObjectName("stage_pos_slider")
        self.vertical_layout.addWidget(self.stage_pos_slider)
        self.message_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.message_label.setObjectName("message_label")
        self.vertical_layout.addWidget(self.message_label)
        spacer_item = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred
        )
        self.vertical_layout.addItem(spacer_item)
        self.home_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.home_btn.setObjectName("home_btn")
        self.vertical_layout.addWidget(self.home_btn)
        spacer_item_1 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.vertical_layout.addItem(spacer_item_1)
        self.horizontal_layout.addLayout(self.vertical_layout)
        self.vertical_layout_3.addLayout(self.horizontal_layout)
        main_window.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=main_window)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1333, 22))
        self.menubar.setObjectName("menubar")
        main_window.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=main_window)
        self.statusbar.setObjectName("statusbar")
        main_window.setStatusBar(self.statusbar)

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window: QtWidgets.QMainWindow) -> None:
        """Set text and titles."""
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("MainWindow", "My Stage GUI"))
        self.table_title_label.setText(_translate("MainWindow", "Starter Stage GUI"))
        self.label_2.setText(_translate("MainWindow", "Stage Position:"))
        self.message_label.setText(_translate("MainWindow", "message_label"))
        self.home_btn.setText(_translate("MainWindow", "Home Stage"))