import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QHeaderView
import glob


class Ui_MainWindow(object):

    GREEN = QtGui.QColor(196, 237, 194)
    YELLOW = QtGui.QColor(247, 247, 181)
    RED = QtGui.QColor(237, 194, 194)

    def __init__(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(550, 540)
        MainWindow.setMinimumSize(QtCore.QSize(550, 570))
        MainWindow.setMaximumSize(QtCore.QSize(550, 570))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lblLogo = QtWidgets.QLabel(self.centralwidget)
        self.lblLogo.setGeometry(QtCore.QRect(10, 10, 111, 51))
        self.lblLogo.setText("")
        self.lblLogo.setPixmap(QtGui.QPixmap("data_files/DOH.gif"))
        self.lblLogo.setScaledContents(True)
        self.lblLogo.setObjectName("lblLogo")
        self.lblName = QtWidgets.QLabel(self.centralwidget)
        self.lblName.setGeometry(QtCore.QRect(150, 0, 391, 71))
        self.lblName.setStyleSheet("color: rgb(36, 21, 255)")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(22)
        font.setBold(True)
        font.setWeight(75)
        self.lblName.setFont(font)
        self.lblName.setObjectName("lblName")
        self.hline1 = QtWidgets.QFrame(self.centralwidget)
        self.hline1.setGeometry(QtCore.QRect(0, 60, 551, 16))
        self.hline1.setFrameShape(QtWidgets.QFrame.HLine)
        self.hline1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.hline1.setObjectName("hline1")
        self.lblPath = QtWidgets.QLabel(self.centralwidget)
        self.lblPath.setGeometry(QtCore.QRect(10, 70, 411, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.lblPath.setFont(font)
        self.lblPath.setObjectName("lblPath")
        self.btnSelectFolder = QtWidgets.QPushButton(self.centralwidget)
        self.btnSelectFolder.setGeometry(QtCore.QRect(430, 70, 111, 31))
        self.btnSelectFolder.setObjectName("btnSelectFolder")
        self.btnStart = QtWidgets.QPushButton(self.centralwidget)
        self.btnStart.setGeometry(QtCore.QRect(10, 440, 531, 31))
        self.btnStart.setObjectName("btnStart")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(10, 480, 531, 20))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.lblProgress = QtWidgets.QLabel(self.centralwidget)
        self.lblProgress.setGeometry(QtCore.QRect(180, 510, 101, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.lblProgress.setFont(font)
        self.lblProgress.setText("")
        self.lblProgress.setObjectName("lblProgress")
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(10, 150, 531, 281))
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        self.tableWidget.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Arial")
        item.setFont(font)
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Arial")
        item.setFont(font)
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Arial")
        item.setFont(font)
        item.setTextAlignment(QtCore.Qt.AlignLeft)
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.lblUsername = QtWidgets.QLabel(self.centralwidget)
        self.lblUsername.setGeometry(QtCore.QRect(10, 110, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.lblUsername.setFont(font)
        self.lblUsername.setObjectName("lblUsername")
        self.txtUsername = QtWidgets.QLineEdit(self.centralwidget)
        self.txtUsername.setGeometry(QtCore.QRect(90, 110, 181, 31))
        self.txtUsername.setObjectName("txtUsername")
        self.lblPassword = QtWidgets.QLabel(self.centralwidget)
        self.lblPassword.setGeometry(QtCore.QRect(280, 110, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.lblPassword.setFont(font)
        self.lblPassword.setObjectName("lblPassword")
        self.txtPassword = QtWidgets.QLineEdit(self.centralwidget)
        self.txtPassword.setGeometry(QtCore.QRect(360, 110, 181, 31))
        self.txtPassword.setObjectName("txtPassword")
        self.txtPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 550, 25))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslate_ui(MainWindow)
        self.setup_events()
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def start(self):
        print('omegalul')


    def load_xml_from_folder(self):
        # Create a set of all the files to upload
        file_list = set()
        for filename in glob.iglob(
                self.lblPath.text().replace("/", "\\") + '\\**\\*.xml', recursive=True):
            file_list.add(filename)
        # Set the new file count
        self.file_count = len(file_list)
        # Reset the table widget
        self.tableWidget.clearContents()
        # Add the rows
        self.tableWidget.setRowCount(len(file_list))
        # Populate the rows
        row_index = 0
        for filename in file_list:
            try:
                # Parse the path to get the repository and number
                fnms = filename.split('\\')
                objIDpts = fnms[-1].split("_")
                repository = objIDpts[0]
                number = objIDpts[1].split(".")[0]
                self.tableWidget.setItem(row_index, 0, QtWidgets.QTableWidgetItem(repository))
                self.tableWidget.setItem(row_index, 1, QtWidgets.QTableWidgetItem(number))
                self.tableWidget.setItem(row_index, 2, QtWidgets.QTableWidgetItem(filename))
                self.set_row_color(row_index, Ui_MainWindow.GREEN)
                row_index = row_index + 1
            except Exception as e:
                print(e)

        # No valid DOH files found
        if row_index is 0:
            self.tableWidget.setRowCount(0)

        # Set Path size
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

    def set_folder(self):
        dir_path = str(
            QFileDialog.getExistingDirectory(None,
                                             'Select Folder',
                                             self.lblPath.text(),
                                             QFileDialog.ShowDirsOnly
                                             )
        )
        if dir_path is not None and len(dir_path) > 0:
            self.lblPath.setText(dir_path)
            self.load_xml_from_folder()

    def setup_events(self):
        self.btnSelectFolder.clicked.connect(self.set_folder)
        self.btnStart.clicked.connect(self.start)

    def set_row_color(self, row_index, color):
        # color e.g. QtGui.QColor(QtCore.Qt.green)
        for i in range(self.tableWidget.columnCount()):
            self.tableWidget.item(row_index, i).setBackground(color)

    def retranslate_ui(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "DOH - MODS XML Uploader"))
        self.lblName.setText(_translate("MainWindow", "DOH - MODS XML Uploader"))
        self.lblPath.setText(_translate("MainWindow", os.path.dirname(os.path.realpath(__file__))))
        self.btnSelectFolder.setText(_translate("MainWindow", "Select Folder..."))
        self.btnStart.setText(_translate("MainWindow", "Start Upload"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Repository"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Number"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Path"))
        self.lblUsername.setText(_translate("MainWindow", "Username"))
        self.lblPassword.setText(_translate("MainWindow", "Password"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
