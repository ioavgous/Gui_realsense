#!/usr/bin/env python3

import sys, cv2, datetime, csv
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QPushButton,\
    QVBoxLayout, QWidget, QLabel, QSpinBox, QErrorMessage, QFileDialog
from PyQt6.QtGui import QImage, QPixmap
from camera_functionalities import Camera


class ImageWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)

    def hasHeightForWidth(self):
        return self.pixmap() is not None

    def heightForWidth(self, w):
        if self.pixmap():
            try:
                return int(w * (self.pixmap().height() / self.pixmap().width()))
            except ZeroDivisionError:
                return 0


def resize_image(image_data, max_img_width, max_img_height):
    scale_percent = min(max_img_width / image_data.shape[1], max_img_height / image_data.shape[0])
    width = int(image_data.shape[1] * scale_percent)
    height = int(image_data.shape[0] * scale_percent)
    newSize = (width, height)
    image_resized = cv2.resize(image_data, newSize, None, None, None, cv2.INTER_AREA)
    return image_resized


def pixmap_from_cv_image(cv_image):
    height, width, _ = cv_image.shape
    bytesPerLine = 3 * width
    qImg = QImage(cv_image.data, width, height, bytesPerLine, QImage.Format.Format_RGB888).rgbSwapped()
    return QPixmap(qImg)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Dataset Collector GUI")
        main_layout = QVBoxLayout()
        top_bar_layout = QHBoxLayout()
        image_bar_layout = QHBoxLayout()
        self.source_image_data = None
        self.result_image_data = None
        self.max_img_height = 400
        self.max_img_width = 600
        self.rs_cam = Camera()
        self.counter = 0
        self.name = None
        self.csv_list = []

        # Start Streaming, Stop Streaming and Save Dataset Buttons
        self.activate_stream = QPushButton('Activate Streams')
        self.activate_stream.clicked.connect(self.choose_source_image)
        self.stop_stream_button = QPushButton ('Stop Streams')
        self.capture_button = QPushButton('Capture Image')
        self.stop_stream_button.hide()
        self.capture_button.clicked.connect(self.capture_callback)
        self.capture_button.hide()

        self.stop_stream_button.clicked.connect(self.stopstreaming)
        self.save_button = QPushButton('Save Image')
        self.save_button.hide()

        for btn in [self.activate_stream, self.stop_stream_button, self.capture_button]:
            btn.setFixedHeight(30)
            btn.setFixedWidth(100)

        top_bar_layout.addWidget(self.activate_stream)
        top_bar_layout.addWidget(self.stop_stream_button)
        top_bar_layout.addWidget(self.capture_button)

        self.source_image = ImageWidget()
        self.source_image.setMaximumSize(self.max_img_width, self.max_img_height)

        source_image_layout = QVBoxLayout()
        source_image_layout.addWidget(self.source_image)

        image_bar_layout.addLayout(source_image_layout)

        bottom_bar_layout = QHBoxLayout()

        self.terminal = QLabel("Enter the Class Measured for each image patch:")
        self.save_button.clicked.connect(self.save_as_file)
        self.save_button.setFixedWidth(100)
        self.class_selection = QSpinBox()
        self.class_selection.setMinimum(0)
        self.class_selection.setMaximum(3)
        self.class_selection.setValue(0)
        self.class_selection.setFixedWidth(100)
        self.class_selection.setPrefix('Class:')
        self.enter_button = QPushButton('Enter')
        self.enter_button.setFixedHeight(30)
        self.enter_button.setFixedWidth(100)
        self.enter_button.clicked.connect(self.enter_values)

        bottom_bar_layout.addWidget(self.save_button)
        bottom_bar_layout.addWidget(self.terminal)
        self.terminal.hide()
        bottom_bar_layout.addWidget(self.class_selection)
        self.class_selection.hide()
        bottom_bar_layout.addWidget(self.enter_button)
        self.enter_button.hide()

        main_layout.addLayout(top_bar_layout)
        main_layout.addLayout(image_bar_layout)
        main_layout.addLayout(bottom_bar_layout)
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def stopstreaming(self):
        print("Deactivate Camera")
        self.rs_cam.deactivate = True
        self.rs_cam.image_captured = None
        self.activate_stream.show()
        self.stop_stream_button.hide()
        self.capture_button.hide()

    def choose_source_image(self):
        print("Activate Camera")
        self.rs_cam.deactivate = False
        self.stop_stream_button.show()
        self.activate_stream.hide()
        self.capture_button.show()
        self.rs_cam.color_stream()

    def capture_callback(self):
        source_image_resized = resize_image(self.rs_cam.image_captured, self.max_img_width, self.max_img_height)
        self.source_image.setPixmap(pixmap_from_cv_image(source_image_resized))
        self.result_image_data = self.rs_cam.image_captured
        self.save_button.show()

    def enter_values(self):
        if self.counter == 15:
            self.terminal.setText("You have entered:" + str(self.class_selection.value()) +
                                  "for the " + str(self.counter) + " image patch")
            self.csv_list.append(self.class_selection.value())
            with open(self.name + '.csv', 'w', encoding='UTF8') as f:
                writer = csv.writer(f)
                counter = 0
                tmp = []
                for i in self.csv_list:
                    counter += 1
                    tmp.append(i)
                    if counter % 4 == 0 and counter != 0:
                        writer.writerow(tmp)
                        tmp = []

            self.csv_list = []
            self.terminal.setText("Enter the Class Measured for each image patch:")
            self.counter = 0
            self.class_selection.hide()
            self.enter_button.hide()
            self.terminal.hide()
            self.capture_button.show()
            return

        print(self.counter)
        self.counter += 1
        self.terminal.setText("You have entered: " + str(self.class_selection.value()) +
                              " for the " + str(self.counter) + " image patch")
        self.csv_list.append(self.class_selection.value())


    def save_as_file(self):
        capt_time = datetime.datetime.now()
        self.name = str(capt_time.year)+'_'+ str(capt_time.month)+ '_' + str(capt_time.day)\
                + 'T'+ str(capt_time.hour)+'_'+ str(capt_time.minute)+'_'+ str(capt_time.second)

        cv2.imwrite(self.name+'.jpg', self.result_image_data)
        print("Image Saved")
        print("Enter the Class Measured for each image patch:")
        self.save_button.hide()
        self.capture_button.hide()
        self.terminal.show()
        self.class_selection.show()
        self.enter_button.show()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
