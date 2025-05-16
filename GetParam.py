import sys
import re
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit


class LinkParameterExtractor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 创建布局
        layout = QVBoxLayout()

        # 创建输入链接的标签和输入框
        self.link_label = QLabel("请输入链接:")
        self.link_input = QLineEdit()
        layout.addWidget(self.link_label)
        layout.addWidget(self.link_input)

        # 创建提取参数的按钮
        self.extract_button = QPushButton("提取参数")
        self.extract_button.clicked.connect(self.extract_parameters)
        layout.addWidget(self.extract_button)

        # 创建显示提取结果的文本编辑框
        self.result_text_edit = QTextEdit()
        self.result_text_edit.setReadOnly(True)
        layout.addWidget(self.result_text_edit)

        # 设置布局
        self.setLayout(layout)
        self.setWindowTitle('链接参数提取器')
        self.setGeometry(300, 300, 400, 200)
        self.show()

    def extract_parameters(self):
        url = self.link_input.text()
        pattern_1s = r'1s([^!]*)'
        pattern_139_96h = r'(\d+\.\d+)h'
        pattern_103t = r'(\d+\.\d+)t'

        result_1s = re.search(pattern_1s, url)
        result_139_96h = re.search(pattern_139_96h, url)
        result_103t = re.search(pattern_103t, url)

        parameters = {}
        if result_1s:
            parameters['panoId'] = result_1s.group(1)
        if result_139_96h:
            parameters['旋转角'] = result_139_96h.group(1)
        if result_103t:
            parameters['俯仰角'] = result_103t.group(1)

        result_text = ""
        for key, value in parameters.items():
            result_text += f"{key}: {value}\n"

        if not result_text:
            result_text = "未提取到有效参数"

        self.result_text_edit.setPlainText(result_text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LinkParameterExtractor()
    sys.exit(app.exec_())