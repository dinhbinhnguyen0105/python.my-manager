# Form implementation generated from reading ui file '/Volumes/KINGSTON/Dev/python/python.my-manager.v1/ui/sidebar.ui'
#
# Created by: PyQt6 UI code generator 6.8.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_sidebar_container(object):
    def setupUi(self, sidebar_container):
        sidebar_container.setObjectName("sidebar_container")
        sidebar_container.resize(61, 600)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(sidebar_container)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(4)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.user_btn = QtWidgets.QPushButton(parent=sidebar_container)
        self.user_btn.setMinimumSize(QtCore.QSize(0, 60))
        self.user_btn.setMaximumSize(QtCore.QSize(60, 60))
        self.user_btn.setObjectName("user_btn")
        self.verticalLayout.addWidget(self.user_btn)
        self.re_btn = QtWidgets.QPushButton(parent=sidebar_container)
        self.re_btn.setMinimumSize(QtCore.QSize(0, 60))
        self.re_btn.setMaximumSize(QtCore.QSize(60, 60))
        self.re_btn.setObjectName("re_btn")
        self.verticalLayout.addWidget(self.re_btn)
        self.misc_btn = QtWidgets.QPushButton(parent=sidebar_container)
        self.misc_btn.setMinimumSize(QtCore.QSize(0, 60))
        self.misc_btn.setMaximumSize(QtCore.QSize(60, 60))
        self.misc_btn.setObjectName("misc_btn")
        self.verticalLayout.addWidget(self.misc_btn)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(sidebar_container)
        QtCore.QMetaObject.connectSlotsByName(sidebar_container)

    def retranslateUi(self, sidebar_container):
        _translate = QtCore.QCoreApplication.translate
        sidebar_container.setWindowTitle(_translate("sidebar_container", "Form"))
        self.user_btn.setText(_translate("sidebar_container", "User"))
        self.re_btn.setText(_translate("sidebar_container", "RE"))
        self.misc_btn.setText(_translate("sidebar_container", "Misc"))
