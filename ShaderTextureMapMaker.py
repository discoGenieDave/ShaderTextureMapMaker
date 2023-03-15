import os
import cv2
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QImage, QPixmap, QDragEnterEvent, QDropEvent, QImageReader, QPainter
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QSlider, QComboBox, \
    QHBoxLayout, QColorDialog

# Set up grid parameters
GRID_SIZE = 4
GRID_WIDTH = 512
GRID_HEIGHT = 512
PADDING = 10
TOTAL_WIDTH = GRID_WIDTH + 2 * PADDING
TOTAL_HEIGHT = GRID_HEIGHT + 2 * PADDING + 30

# Set up image parameters
IMAGE_SIZE = 2048
NUM_COLORS = 256

class DirectoryLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        url = event.mimeData().urls()[0].toLocalFile()
        self.setText(url)

class DropLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        filepath = event.mimeData().urls()[0].toLocalFile()
        _, filename = os.path.split(filepath)
        if "RGBMask" in filename.lower():

            # Read the drag and drop image

            img = cv2.imread(filepath)
            img = Image
            # Check if the image is 4096 and resize it if it is
            if img is not None and img.shape[:2] == (4096, 4096):

                # Cropping the image on the lower left using Slicing Indexing
                img_cropped = img[0:2048, 2048:2048]
                self.setPixmap(QPixmap.fromImage(img_cropped))
                pixmap = QPixmap.fromImage(img_cropped)
                self.setPixmap(pixmap)

                # using PIL to extract the channel information from the image
                img_cropped.open()
                red_chan = img_cropped.getchannel('R')
                green_chan = img_cropped.getchannel('G')
                blue_chan = img_cropped.getchannel('B')

        return super().dropEvent(event), red_chan, green_chan, blue_chan






class MainWindow(QWidget):
    def __init__(self):
        super().__init__()


        # Set up layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(PADDING, PADDING, PADDING, PADDING)
        self.layout.setSpacing(0)

        # Create QLineEdit for directory input
        self.directory_input = DirectoryLineEdit(self)
        self.directory_input.setPlaceholderText("Drag Output Folder Here")
        self.layout.addWidget(self.directory_input)

        # Create grid of squares
        self.grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.uint8)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                self.grid[i][j] = np.random.randint(NUM_COLORS)

        # Setting Iridescence and Gliiter Mask to White
        self.grid[2][3] = 1
        self.grid[3][3] = 1


        # Create QImage from grid
        self.image = QImage(GRID_SIZE, GRID_SIZE, QImage.Format_RGBA8888)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                gray_value = self.grid[i][j]
                color = QColor(gray_value, gray_value, gray_value)
                self.image.setPixelColor(j, i, color)

        # Create QLabel to display QImage
        self.label = DropLabel(self)
        self.setAcceptDrops(True)
        self.label.setPixmap(QPixmap.fromImage(self.image))
        pixmap = QPixmap.fromImage(self.image)
        pixmap = pixmap.scaled(GRID_WIDTH, GRID_HEIGHT)
        self.label.setPixmap(pixmap)
        self.layout.addWidget(self.label)

        # Set up window properties
        self.setWindowTitle("Shader Texture Mapper")
        self.setFixedSize(TOTAL_WIDTH, TOTAL_HEIGHT)

        # Create slider and combobox
        self.slider_combobox_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.valueChanged.connect(self.update_selected_square)

        self.combobox = QComboBox()
        self.combobox.addItems(['Metallic', 'Smoothness', 'Emission', 'Fresnel', 'Fuzziness'])
        self.combobox.currentIndexChanged.connect(self.update_slider_value)

        self.slider_combobox_layout.addWidget(self.slider)
        self.slider_combobox_layout.addWidget(self.combobox)
        self.layout.addLayout(self.slider_combobox_layout)

        # Add the Color Pickers
        self.setup_color_buttons()

        # Create "Create Texture" button
        self.button = QPushButton("Create Texture", self)
        self.button.clicked.connect(self.create_texture)
        self.layout.addWidget(self.button)

        # Set up window properties
        self.setWindowTitle("Gray Grid")
        self.setFixedSize(TOTAL_WIDTH, TOTAL_HEIGHT)

    def create_image_from_grid(self):
        img = QImage(2048, 2048, QImage.Format_RGBA8888)
        img.fill(Qt.transparent)
        painter = QPainter(img)

        for row in range(4):
            for col in range(4):
                color = self.grid[row][col]
                if isinstance(color, np.ndarray):  # Handle NumPy arrays
                    qimage = QImage(color.data, color.shape[1], color.shape[0], QImage.Format_RGB888)
                    painter.drawImage(col * 512, row * 512, qimage.scaled(512, 512))
                else:
                    rect = QRect(col * 512, row * 512, 512, 512)
                    img.fillRect(rect, QColor(color, color, color, 255))

        painter.end()
        return img




    def update_slider_value(self):
        square_idx = self.combobox.currentIndex()
        square_row = square_idx // GRID_SIZE
        square_col = square_idx % GRID_SIZE
        self.slider.setValue(self.grid[square_row][square_col])

    def update_selected_square(self):
        gray_value = self.slider.value()
        square_idx = self.combobox.currentIndex()
        square_row = square_idx // GRID_SIZE
        square_col = square_idx % GRID_SIZE
        self.grid[square_row][square_col] = gray_value
        self.update_image()


    def update_image(self):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                gray_value = self.grid[i][j]
                color = QColor(gray_value, gray_value, gray_value)
                self.image.setPixelColor(j, i, color)
        pixmap = QPixmap.fromImage(self.image)
        pixmap = pixmap.scaled(GRID_WIDTH, GRID_HEIGHT)
        self.label.setPixmap(pixmap)

    def setup_color_buttons(self):
        self.color_buttons_layout = QHBoxLayout()

        self.og_mtsm_combobox = QComboBox()
        self.og_mtsm_combobox.addItems(["OG MtSM On", "OG MtSM Off"])
        self.og_mtsm_combobox.setCurrentIndex(0 if self.grid[1][0] == 255 else 1)
        self.og_mtsm_combobox.currentIndexChanged.connect(self.toggle_og_mtsm)
        self.color_buttons_layout.addWidget(self.og_mtsm_combobox)



        self.color_buttons_layout.addWidget(self.og_mtsm_combobox)

        self.iridescence_button = QPushButton("Iridescence")
        self.iridescence_button.clicked.connect(self.set_iridescence_color)
        self.color_buttons_layout.addWidget(self.iridescence_button)

        self.glitter_button = QPushButton("Glitter")
        self.glitter_button.clicked.connect(self.set_glitter_color)
        self.color_buttons_layout.addWidget(self.glitter_button)

        self.layout.addLayout(self.color_buttons_layout)

    def toggle_og_mtsm(self, index):
        if index == 1:  # Off (Black)
            self.grid[1][1] = 0
        else:  # On (White)
            self.grid[1][1] = 255
        self.update_image()

    def set_iridescence_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.grid[2][0] = color.red()
            self.grid[2][1] = color.green()
            self.grid[2][2] = color.blue()
            self.update_image()

    def set_glitter_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.grid[3][0] = color.red()
            self.grid[3][1] = color.green()
            self.grid[3][2] = color.blue()
            self.update_image()





    def create_texture(self):
        # Create larger image from grid
        large_grid = cv2.resize(self.grid, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST)
        large_grid = np.repeat(large_grid[:, :, np.newaxis], 4, axis=2)
        large_image = QImage(large_grid, IMAGE_SIZE, IMAGE_SIZE, QImage.Format_RGBA8888)

        # Get the directory from the QLineEdit
        directory = self.directory_input.text()
        if directory:
            # Save the image to the selected directory
            filename = f"{directory}/dress-0069-silvertooth_002.png"
            large_image.save(filename)


if __name__ == "__main__":
    # Set up QApplication
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()