# Form implementation generated from reading ui file '/Volumes/KINGSTON/Dev/python/python.my-manager.v1/ui/mainwindow.ui'
#
# Created by: PyQt6 UI code generator 6.8.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 600)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setContentsMargins(8, 8, 8, 8)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.sidebar_container = QtWidgets.QWidget(parent=self.centralwidget)
        self.sidebar_container.setObjectName("sidebar_container")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.sidebar_container)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.sidebar_user_btn = QtWidgets.QPushButton(parent=self.sidebar_container)
        self.sidebar_user_btn.setMinimumSize(QtCore.QSize(0, 60))
        self.sidebar_user_btn.setMaximumSize(QtCore.QSize(60, 60))
        self.sidebar_user_btn.setObjectName("sidebar_user_btn")
        self.verticalLayout.addWidget(self.sidebar_user_btn)
        self.sidebar_re_btn = QtWidgets.QPushButton(parent=self.sidebar_container)
        self.sidebar_re_btn.setMinimumSize(QtCore.QSize(0, 60))
        self.sidebar_re_btn.setMaximumSize(QtCore.QSize(60, 60))
        self.sidebar_re_btn.setObjectName("sidebar_re_btn")
        self.verticalLayout.addWidget(self.sidebar_re_btn)
        self.sidebar_misc_btn = QtWidgets.QPushButton(parent=self.sidebar_container)
        self.sidebar_misc_btn.setMinimumSize(QtCore.QSize(0, 60))
        self.sidebar_misc_btn.setMaximumSize(QtCore.QSize(60, 60))
        self.sidebar_misc_btn.setObjectName("sidebar_misc_btn")
        self.verticalLayout.addWidget(self.sidebar_misc_btn)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.sidebar_container)
        self.line = QtWidgets.QFrame(parent=self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.content_container = QtWidgets.QStackedWidget(parent=self.centralwidget)
        self.content_container.setObjectName("content_container")
        self.horizontalLayout.addWidget(self.content_container)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.sidebar_user_btn.setText(_translate("MainWindow", "User"))
        self.sidebar_re_btn.setText(_translate("MainWindow", "RE"))
        self.sidebar_misc_btn.setText(_translate("MainWindow", "Misc"))
