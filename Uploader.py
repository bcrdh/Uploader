"""
Contains the entire program, the other py files
are just old files.
"""
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThreadPool, QRunnable, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import glob
from robobrowser import RoboBrowser

"""
The max number of concurrent threads active
in the thread pool.
10 workers so the website is not overloaded
with excessive uploading / parsing of the XML files
This might be able to go higher, we just have to experiment
"""
max_threads = 10

"""
Program logic
"""
"""
The session that will be used by
all browser instances to access the
collections. Set in sign_in()
"""
global_session = None
# The base URL of the DOH Arca website
base_url = 'https://doh.arcabc.ca'


def sign_in(username, password):
    """
    Signs into the DOH website and sets the global session
    to allow other browser instances to access the cookies
    :param username: the username to login with
    :param password: the password to login with
    """
    # If already logged in, don't log in again
    global global_session
    if global_session is not None:
        return True
    # Create Non-JS browser
    browser = RoboBrowser(parser='html.parser')
    # Open login page
    browser.open('https://doh.arcabc.ca/user/login')
    # Get the login form
    form = browser.get_form(id='user-login')
    # Set the username & password
    form['name'].value = username
    form['pass'].value = password
    # Submit the form
    browser.submit_form(form)
    # If successfully signed in
    h1 = browser.find(class_='page__title')
    if h1.text == username:
        # Set the global session
        global_session = browser.session
        return True
    else:
        return False


def get_lock_link(links):
    """
    Gets the link that allows to lock a
    collection object in order to modify it
    :param links: the list of links on the current page of the browser
    :return: the href of the correct link to acquire the lock
    """
    for link in links:
        if link.text == 'acquire the lock':
            return link['href']


def get_unlock_link(links):
    """
    Gets the link that allows to unlock a
    collection object in order to let others to modify it again
    :param links: the list of links on the current page of the browser
    :return: the href of the correct link to release the lock
    """
    for link in links:
        if link.text == 'release':
            return link['href']


def acquire_lock(browser, manage_url):
    """
    Acquires the lock of a collection object in order to modify it
    :param browser: the browser that is currently browsing the collection object
    :param manage_url: the management url of the object to acquire the lock of
    :return: a boolean indicating if the acquisition was successful
    """
    try:
        browser.open(manage_url)
        lock_link = get_lock_link(browser.get_links())

        if lock_link is not None:
            global base_url
            # Open the link to lock
            browser.open(base_url + lock_link)
            # Find the form by class and submit it
            browser.submit_form(browser.get_form(class_='confirmation'))
            # Success
            return True
        # Failed to acquire lock because someone else
        # has locked this object
        else:
            return False
    # Any error indicates failure
    except Exception as e:
        return False


def release_lock(browser, manage_url):
    """
    Releases the lock of a collection object in order to let others
    modify it.
    :param browser: the browser that is currently browsing the collection object
    :param manage_url: the management url of the object to release the lock of
    """
    try:
        browser.open(manage_url)
        unlock_link = get_unlock_link(browser.get_links())
        # if unlock_link is None, then
        # the object is not locked anyways
        if unlock_link is not None:
            global base_url
            browser.open(base_url + unlock_link)
            browser.submit_form(browser.get_form(class_='confirmation'))
    # No return for this as we don't really care
    # if we released the lock since it automatically
    # releases in 30 minutes.
    except Exception as e:
        pass


def upload_xml(file, repo, num):
    """
    Uploads the MODS XML file to the appropriate object given the
    repository namespace and number of the specific object.
    :param file: the path of the MODS XML file to reingest
    :param repo: the repository namespace derived from the file name
    :param num: the number of the object derived from the file name
    :return: None
    """
    global base_url
    global global_session
    # URL for managing the object
    manage_url = 'https://doh.arcabc.ca/islandora/object/' + repo + '%3A' + num + '/datastream/MODS/replace'
    # Create a new browser instance
    browser = RoboBrowser(session=global_session, parser='html.parser')
    try:
        # Acquire the lock for the object
        if acquire_lock(browser, manage_url):
            # Go to the MODS replace page
            browser.open('https://doh.arcabc.ca/islandora/object/' + repo + '%3A' + num + '/datastream/MODS/replace')
            # Get the upload file form
            form = browser.get_form(id='islandora-datastream-version-replace-form')
            # Set the file to upload
            f = open(file, 'r')
            form['files[file]'].value = f
            # This submit submits the form
            browser.submit_form(form, submit=form['op'])
            # Release the lock
            release_lock(browser, manage_url)
            # Close the file
            f.close()
            # Success
            return True
        else:
            print('Failed to update object: ' + file + ' as the lock could not be acquired.')
    except Exception as e:
        print('Failed to update object: ' + file)
        # Release the lock
        release_lock(browser, manage_url)

    # FAIL
    return False


"""
Main UI stuff
"""


def upload(items, row_index):
    """
    Helper method that initiates the upload process. Called by
    any Worker in the threadpool.
    :param items: the cells of the row being processed, as text.
    :param row_index: the index of the row being processed
    :return: the result of the upload as a tuple with a boolean
    indicating if it was successful and the row index.
    """
    result = (upload_xml(items[2], items[0], items[1]), row_index)
    return result


class WorkerSignals(QObject):
    """
    The possible return types from a Worker object
    """
    result = pyqtSignal(tuple)
    started = pyqtSignal(int)


class Worker(QRunnable):
    """
    Worker class that processes a single table widget row
    i.e. a single collection object
    https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        items, row_index = self.args
        self.signals.started.emit(row_index)
        result = self.fn(items, row_index)
        self.signals.result.emit(result)


"""
All UI setup is down here
"""


class Ui_MainWindow(object):
    """
    Some static colors that will be used often in the UI
    """
    GREEN = QtGui.QColor(196, 237, 194)
    YELLOW = QtGui.QColor(247, 247, 181)
    RED = QtGui.QColor(237, 194, 194)

    def __init__(self, MainWindow):
        """
        UI Setup (Nasty, auto-generated code with some modifications)
        :param MainWindow: the main PyQt window
        """
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
        self.lblProgress.setGeometry(QtCore.QRect(138, 510, 320, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
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

        """
        Set custom names and events for UI
        """
        self.retranslate_ui(MainWindow)
        self.setup_events()
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        """
        Thread pool for processing
        """
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(max_threads)

        """
        Variables for tracking progress
        """
        # The number of successful uploads done
        self.successful_uploads = 0
        self.successful_uploads_lock = QtCore.QMutex()
        # The total number of upload attempts, successful or not
        self.completed_tasks = 0
        self.completed_tasks_lock = QtCore.QMutex()

    @staticmethod
    def show_error_message(msg):
        """
        Helper method to display a messagebox with an error
        :param msg: the error message
        :return: None
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(msg)
        msg_box.setWindowTitle("There's a problem...")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def start(self):
        """
        Called when the user clicks the Begin Upload button.
        This function checks if there are valid MODS XML files loaded,
        whether there is a username and password and if there is, whether
        the username and password are valid. Then creates a threadpool and
        submits all the files to be processed
        :return: None
        """
        # Make sure table has files, username and password are entered
        if self.tableWidget.rowCount() is 0:
            self.show_error_message("No files have been loaded! Select" +
                                    " a folder with valid MODS XML files.")
        elif len(self.txtUsername.text().strip()) is 0:
            self.show_error_message("You must enter a username!")
        elif len(self.txtPassword.text().strip()) is 0:
            self.show_error_message("You must enter a password!")
        elif not sign_in(self.txtUsername.text(), self.txtPassword.text()):
            self.show_error_message("Ensure your username and password are correct!")
        else:
            for i in range(self.tableWidget.rowCount()):
                items = []
                for j in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(i, j)
                    items.append(str(item.text()))

                worker = Worker(upload, items, i)
                worker.signals.started.connect(self.started)
                worker.signals.result.connect(self.worker_response_handler)

                self.threadpool.start(worker)

    def started(self, row_index):
        """
        The function that handles a started emit from a Worker.
        When a upload task starts, it calls this method to update the UI
        and set the row to yellow to inform the user the row is being
        processed (i.e. the uploading process)
        :param row_index: the index of the row being processed
        :return: None
        """
        self.set_row_color(row_index, Ui_MainWindow.YELLOW)

    def worker_response_handler(self, completed):
        """
        The handler to handle a response from a Worker when
        an upload task is completed (not necessarily successful)
        :param completed: the tuple holding the result from the Worker
        :return: None
        """
        # Pattern match the tuple
        success, row_index = completed
        if success:
            self.set_row_color(row_index, Ui_MainWindow.GREEN)
            # Safely increment successful upload
            # And update progress label
            self.successful_uploads_lock.lock()
            self.successful_uploads = self.successful_uploads + 1
            self.lblProgress.setText \
                ("Successfully uploaded: " + str(self.successful_uploads) + "/" + str(self.tableWidget.rowCount()))
            self.successful_uploads_lock.unlock()
        else:
            self.set_row_color(row_index, Ui_MainWindow.RED)

        # Safely increment completed tasks
        # and set progress bar value
        self.completed_tasks_lock.lock()
        self.completed_tasks = self.completed_tasks + 1
        self.progressBar.setValue((self.completed_tasks / self.tableWidget.rowCount()) * 100)
        self.completed_tasks_lock.unlock()

    def load_xml_from_folder(self):
        """
        Loads all XML files from a folder recursively using globe.
        :return: None
        """
        # Reset the UI and its variables
        self.reset()
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
                row_index = row_index + 1
            except Exception as e:
                print(e)

        # No valid DOH files found
        if row_index is 0:
            self.tableWidget.setRowCount(0)

        # Set Path column size
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

    def set_folder(self):
        """
        Sets the folder selected by the user in the label and
        calls the function to load XML files from it
        :return: None
        """
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

    def reset(self):
        """
        Resets the UI variables and elements
        for another upload session
        :return: None
        """
        self.completed_tasks = 0
        self.successful_uploads = 0
        self.progressBar.setValue(0)
        self.lblProgress.setText("")

    def setup_events(self):
        """
        Connects the UI buttons to relevant functions,
        called only once at the start of the program
        :return: None
        """
        self.btnSelectFolder.clicked.connect(self.set_folder)
        self.btnStart.clicked.connect(self.start)

    def set_row_color(self, row_index, color):
        """
        Sets the color of a row given the index of it
        :param row_index: the index of the row to color
        :param color: the color as a QtGui.QColor e.g. QtGui.QColor(QtCore.Qt.green)
        Can also use the static color variables set in the UI for yellow, red & green
        :return: None
        """
        for i in range(self.tableWidget.columnCount()):
            self.tableWidget.item(row_index, i).setBackground(color)

    def retranslate_ui(self, MainWindow):
        """
        Renames all the elements that need custom text from
        their default text
        :param MainWindow: the ui window
        :return: None
        """
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
