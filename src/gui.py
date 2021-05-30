import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow,
    QAction,
    qApp,
    QApplication,
    QFileDialog,
    QMessageBox,
    QMdiArea,
    QMdiSubWindow,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QTableView,
)
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from database import Database


class GUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timeline_paths = []
        self.case_name = ''
        self.case_directory = ''
        self.db = None
        self.mdi = None
        self.model = None

    def init_ui(self):
        self.statusBar()

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(self.newcase_action())
        file_menu.addAction(self.import_action())
        file_menu.addAction(self.exit_action())

        self.setGeometry(50, 50, 800, 600)
        self.setWindowTitle('DroneTimeline: Forensic Timeline Analysis for Drones')
        self.show()

    def newcase_action(self):
        newcase_act = QAction('&Select Case Directory', self)
        newcase_act.setShortcut('Ctrl+N')
        newcase_act.setStatusTip('Select case directory')
        newcase_act.triggered.connect(self.open_directory_dialog)

        return newcase_act

    def import_action(self):
        import_act = QAction('&Import Timeline', self)
        import_act.setShortcut('Ctrl+I')
        import_act.setStatusTip('Import timeline')
        import_act.triggered.connect(self.open_file_dialog)

        return import_act

    def exit_action(self):
        exit_act = QAction('&Exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit application')
        exit_act.triggered.connect(qApp.quit)

        return exit_act

    def open_directory_dialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        # get database name and database directory
        database_name = os.path.basename(directory)
        if database_name != '' and directory != '':
            self.db = Database(database_name, directory)

            # at the moment, case name == database name
            self.case_name = database_name
            self.case_directory = directory

    def open_file_dialog(self):
        if self.case_name == '':
            dlg = QMessageBox(self)
            dlg.setWindowTitle("DroneTimeline")
            dlg.setText("Please select case directory before importing a timeline.")
            dlg.setStandardButtons(QMessageBox.Ok)
            dlg.setIcon(QMessageBox.Information)
            dlg.exec_()

        else:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)",
                                                       options=options)
            if file_name:
                print(file_name)
                self.timeline_paths.append(file_name)

                # insert timeline to database
                table_name = os.path.basename(file_name)
                table_name = os.path.splitext(table_name)[0]
                self.db.insert(table_name, file_name)

                self.window_trig()

    def window_trig(self):
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        # database
        db = QSqlDatabase("QSQLITE")
        db.setDatabaseName("src.db")
        db.open()

        sub = QMdiSubWindow()
        sub.setWindowTitle("Sub Window")

        # construct the top level widget and layout
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # define widget
        search = QLineEdit()
        table = QTableView()
        self.model = QSqlTableModel(db=db)
        table.setModel(self.model)
        self.model.setTable("timeline-sorted")
        self.model.select()
        search.textChanged.connect(self.update_filter)

        # add widget
        layout.addWidget(search)
        layout.addWidget(table)
        widget.setLayout(layout)

        # set widget
        sub.setWidget(widget)

        # add subwindow and show
        self.mdi.addSubWindow(sub)
        sub.show()

    def update_filter(self, s):
        filter_str = 'message LIKE "%{}%"'.format(s)
        self.model.setFilter(filter_str)


def main():
    app = QApplication(sys.argv)
    _ = GUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()