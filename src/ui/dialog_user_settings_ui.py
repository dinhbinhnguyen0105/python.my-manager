# Form implementation generated from reading ui file '/Volumes/KINGSTON/Dev/python/python.my-manager.v1/ui/dialog_user_settings.ui'
#
# Created by: PyQt6 UI code generator 6.8.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog_UserSettings(object):
    def setupUi(self, Dialog_UserSettings):
        Dialog_UserSettings.setObjectName("Dialog_UserSettings")
        Dialog_UserSettings.resize(480, 448)
        Dialog_UserSettings.setStyleSheet("#Dialog_UserSettings {\n"
"  font-family: \"Courier New\";\n"
"  background-color: #FFFFFF;\n"
"}\n"
"QGroupBox {\n"
"  font-family: \"Courier New\";\n"
"  font-size: 13px;\n"
"  background-color: rgba(248, 249, 250, 1);\n"
"}\n"
"QLineEdit {\n"
"  padding: 4px 0;\n"
"  border: 1px solid #ced4da;\n"
"  border-radius: 8px;\n"
"  margin-left: 8px;\n"
"  padding-left: 4px;\n"
"  background-color: #FFFFFF;\n"
"  color:#212529;\n"
"}\n"
"QPlainTextEdit {\n"
"    background-color: #FFFFFF;\n"
"  color:#212529;\n"
"}\n"
"QLabel {\n"
"  font-family: \"Courier New\";\n"
"  font-size: 13px;\n"
"  color: rgb(90, 93, 97);\n"
"}\n"
"QRadioButton {\n"
"  font-family: \"Courier New\";\n"
"  font-size: 13px;\n"
"  color: #212529;\n"
"}\n"
"QComboBox {\n"
"  font-family: \"Courier New\";\n"
"  font-size: 13px;\n"
"  color: #212529;\n"
"}\n"
"QPushButton {\n"
"  color: #212529;\n"
"}\n"
"\n"
"QCheckBox{\n"
"  color: #212529;\n"
"}")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Dialog_UserSettings)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(parent=Dialog_UserSettings)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_5.setContentsMargins(8, 4, 8, 4)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.proxy_radio = QtWidgets.QRadioButton(parent=self.groupBox)
        self.proxy_radio.setObjectName("proxy_radio")
        self.gridLayout_4.addWidget(self.proxy_radio, 0, 1, 1, 1)
        self.udd_radio = QtWidgets.QRadioButton(parent=self.groupBox)
        self.udd_radio.setObjectName("udd_radio")
        self.gridLayout_4.addWidget(self.udd_radio, 0, 0, 1, 1)
        self.gridLayout_5.addLayout(self.gridLayout_4, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.fields_container = QtWidgets.QGroupBox(parent=Dialog_UserSettings)
        self.fields_container.setEnabled(True)
        self.fields_container.setTitle("")
        self.fields_container.setFlat(False)
        self.fields_container.setCheckable(False)
        self.fields_container.setObjectName("fields_container")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout(self.fields_container)
        self.horizontalLayout_6.setContentsMargins(8, 4, 8, 4)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.udd_container = QtWidgets.QWidget(parent=self.fields_container)
        self.udd_container.setObjectName("udd_container")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.udd_container)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_ = QtWidgets.QHBoxLayout()
        self.verticalLayout_.setObjectName("verticalLayout_")
        self.udd_input_container = QtWidgets.QWidget(parent=self.udd_container)
        self.udd_input_container.setStyleSheet("")
        self.udd_input_container.setObjectName("udd_input_container")
        self.gridLayout_11 = QtWidgets.QGridLayout(self.udd_input_container)
        self.gridLayout_11.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_11.setHorizontalSpacing(4)
        self.gridLayout_11.setObjectName("gridLayout_11")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setSpacing(0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.udd_label = QtWidgets.QLabel(parent=self.udd_input_container)
        self.udd_label.setObjectName("udd_label")
        self.verticalLayout_11.addWidget(self.udd_label)
        self.udd_input = QtWidgets.QLineEdit(parent=self.udd_input_container)
        self.udd_input.setObjectName("udd_input")
        self.verticalLayout_11.addWidget(self.udd_input)
        self.gridLayout_11.addLayout(self.verticalLayout_11, 0, 0, 1, 1)
        self.verticalLayout_.addWidget(self.udd_input_container)
        self.udd_is_selected_checkbox = QtWidgets.QCheckBox(parent=self.udd_container)
        self.udd_is_selected_checkbox.setObjectName("udd_is_selected_checkbox")
        self.verticalLayout_.addWidget(self.udd_is_selected_checkbox)
        self.horizontalLayout.addLayout(self.verticalLayout_)
        self.verticalLayout_2.addWidget(self.udd_container)
        self.proxy_container = QtWidgets.QWidget(parent=self.fields_container)
        self.proxy_container.setStyleSheet("")
        self.proxy_container.setObjectName("proxy_container")
        self.gridLayout_12 = QtWidgets.QGridLayout(self.proxy_container)
        self.gridLayout_12.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_12.setHorizontalSpacing(4)
        self.gridLayout_12.setObjectName("gridLayout_12")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout()
        self.verticalLayout_12.setSpacing(0)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.proxy_label = QtWidgets.QLabel(parent=self.proxy_container)
        self.proxy_label.setObjectName("proxy_label")
        self.verticalLayout_12.addWidget(self.proxy_label)
        self.proxy_input = QtWidgets.QLineEdit(parent=self.proxy_container)
        self.proxy_input.setObjectName("proxy_input")
        self.verticalLayout_12.addWidget(self.proxy_input)
        self.gridLayout_12.addLayout(self.verticalLayout_12, 0, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.proxy_container)
        self.create_new_btn = QtWidgets.QPushButton(parent=self.fields_container)
        self.create_new_btn.setObjectName("create_new_btn")
        self.verticalLayout_2.addWidget(self.create_new_btn)
        self.horizontalLayout_6.addLayout(self.verticalLayout_2)
        self.verticalLayout.addWidget(self.fields_container)
        self.table_view = QtWidgets.QTableView(parent=Dialog_UserSettings)
        self.table_view.setObjectName("table_view")
        self.verticalLayout.addWidget(self.table_view)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=Dialog_UserSettings)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(Dialog_UserSettings)
        QtCore.QMetaObject.connectSlotsByName(Dialog_UserSettings)

    def retranslateUi(self, Dialog_UserSettings):
        _translate = QtCore.QCoreApplication.translate
        Dialog_UserSettings.setWindowTitle(_translate("Dialog_UserSettings", "Dialog"))
        self.proxy_radio.setText(_translate("Dialog_UserSettings", "Proxy"))
        self.udd_radio.setText(_translate("Dialog_UserSettings", "User dir"))
        self.udd_label.setText(_translate("Dialog_UserSettings", "value"))
        self.udd_is_selected_checkbox.setText(_translate("Dialog_UserSettings", "Is selected"))
        self.proxy_label.setText(_translate("Dialog_UserSettings", "value"))
        self.create_new_btn.setText(_translate("Dialog_UserSettings", "Save"))
