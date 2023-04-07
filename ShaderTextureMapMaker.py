import sys
import os
import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, QColorDialog


# Drag and Drop for the output FOlder
class FolderLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        folder_path = event.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(folder_path):
            self.setText(folder_path)
        else:
            QMessageBox.warning(self, "Invalid Folder", "Please drop a folder.")


# Drag and Drop Support for the QLabel
class DnDImageLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        image_path = event.mimeData().urls()[0].toLocalFile()
        self.parent().process_dropped_image(image_path)


class AppDemo(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        # sets up an empty array for the loaded texture maps
        self.loaded_files = []

        self.preview_label = DnDImageLabel(self)
        layout.addWidget(self.preview_label)
        self.setWindowTitle("Genies Face Jewelry Texture Mapper")

        self.square_dict = {
            'Metallic': (0, 0),
            'Smoothness': (0, 1),
            'Emission': (0, 2),
            'Fresnel': (0, 3),
            'Fuzziness': (1, 0),
            'OGMtSm': (1, 1),
            'Red_Mask': (1, 2),
            'Blue_Mask': (1, 3),
            'Iridescent_Red': (2, 0),
            'Iridescent_Green': (2, 1),
            'Iridescent_Blue': (2, 2),
            'Iridescent_Mask': (2, 3),
            'Glitter_Red': (3, 0),
            'Glitter_Green': (3, 1),
            'Glitter_Blue': (3, 2),
            'Glitter_Mask': (3, 3)
        }

        hbox = QHBoxLayout()

        self.combo_box = QComboBox()
        self.combo_box.addItems(list(self.square_dict.keys())[:5])
        hbox.addWidget(self.combo_box)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 255)
        self.slider.setValue(128)
        self.slider.valueChanged.connect(self.update_alpha)
        hbox.addWidget(self.slider)

        self.ogmtsm_label = QLabel("OGMtSM")
        hbox.addWidget(self.ogmtsm_label)

        self.ogmtsm_combo_box = QComboBox()
        self.ogmtsm_combo_box.addItems(["Off", "On"])
        self.ogmtsm_combo_box.currentIndexChanged.connect(self.update_ogmtsm)
        hbox.addWidget(self.ogmtsm_combo_box)

        self.iridescence_button = QPushButton("Iridescence")
        self.iridescence_button.clicked.connect(self.set_iridescence_color)
        hbox.addWidget(self.iridescence_button)

        self.glitter_button = QPushButton("Glitter")
        self.glitter_button.clicked.connect(self.set_glitter_color)
        hbox.addWidget(self.glitter_button)

        layout.addLayout(hbox)

        self.folder_line_edit = FolderLineEdit()
        layout.addWidget(self.folder_line_edit)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_image)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

        self.original_grid = self.create_original_grid()
        self.update_preview()

    def create_original_grid(self):
        grid = np.zeros((2048, 2048, 4), dtype=np.uint8)
        for key, (x, y) in self.square_dict.items():
            color_value = np.random.randint(0, 255)
            grid[x * 512:(x + 1) * 512, y * 512:(y + 1) * 512, :3] = color_value
            grid[x * 512:(x + 1) * 512, y * 512:(y + 1) * 512, 3] = 128
        return grid

    def update_preview(self):
        preview = cv2.resize(self.original_grid, (512, 512), interpolation=cv2.INTER_AREA)
        qimage = QImage(preview.data, preview.shape[1], preview.shape[0], preview.strides[0], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        self.preview_label.setPixmap(pixmap)

    def update_alpha(self):
        alpha = self.slider.value()
        square_key = self.combo_box.currentText()
        x, y = self.square_dict[square_key]
        self.original_grid[x * 512:(x + 1) * 512, y * 512:(y + 1) * 512, 3] = alpha
        self.update_preview()

    def update_ogmtsm(self, index):
        alpha = 255 if index == 1 else 0
        x, y = self.square_dict['OGMtSm']
        self.original_grid[x * 512:(x + 1) * 512, y * 512:(y + 1) * 512, 3] = alpha
        self.update_preview()

    def set_iridescence_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b, _ = color.getRgb()
            self.update_square_alpha('Iridescent_Red', r)
            self.update_square_alpha('Iridescent_Green', g)
            self.update_square_alpha('Iridescent_Blue', b)
            self.update_square_alpha('Iridescent_Mask', 1)
            self.update_preview()

    def set_glitter_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b, _ = color.getRgb()
            self.update_square_alpha('Glitter_Red', r)
            self.update_square_alpha('Glitter_Green', g)
            self.update_square_alpha('Glitter_Blue', b)
            self.update_square_alpha('Glitter_Mask', 1)
            self.update_preview()

    def update_square_alpha(self, square_key, alpha):
        x, y = self.square_dict[square_key]
        self.original_grid[x * 512:(x + 1) * 512, y * 512:(y + 1) * 512, 3] = alpha

    def process_dropped_image(self, image_path):



        # Read the image
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)

        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Split the channels
        red, green, blue = cv2.split(image)

        # Add an alpha channel and set its values to zero
        alpha = np.zeros_like(red)

        # Merge the channels with the added alpha channel
        image_with_alpha = cv2.merge((red, green, blue, alpha))

        # Get the image name
        image_name = os.path.basename(image_path)

        self.loaded_files.append(image_name)
        # Crop the image
        cropped_image = image_with_alpha[2048:4096, 0:2048]

        if 'RGBMask' in image_name:
            # Convert the red and blue channels to grayscale
            red_gray = cv2.cvtColor(cv2.merge((red, red, red)), cv2.COLOR_RGB2GRAY)
            blue_gray = cv2.cvtColor(cv2.merge((blue, blue, blue)), cv2.COLOR_RGB2GRAY)

            # Resize the grayscale images to fit the squares
            red_resized = cv2.resize(red_gray, (512, 512))
            blue_resized = cv2.resize(blue_gray, (512, 512))

            # Update the alpha of the squares with the grayscale images
            self.original_grid[512:1024, 1024:1536, 3] = red_resized
            self.original_grid[512:1024, 1536:2048, 3] = blue_resized


        elif 'Normal' in image_name:
            # Assign red and green channels from the cropped image with alpha to the original grid's corresponding channels
            self.original_grid[:, :, :2] = cropped_image[:, :, :2]

            # Set the blue channel values to zero
            self.original_grid[:, :, 2] = 0

        else:
            QMessageBox.warning(self, "Invalid Image", "Please use an image with 'RGBMask' or 'Normal' in its name.")
            return

        self.update_preview()

    def export_image(self):
        folder_path = self.folder_line_edit.text()

        if not folder_path:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder to export the image.")
            return

        # Get the base name from the input images
        base_name = None
        for file_name in self.loaded_files:
            if 'RGBMask' in file_name:
                base_name = file_name.replace('RGBMask', '_packedTexture')
                break
            elif 'Normal' in file_name:
                base_name = file_name.replace('Normal', '_packedTexture')
                break

        if base_name is None:
            QMessageBox.warning(self, "No Valid Image",
                                "Please drop a valid image with 'RGBMask' or 'Normal' in its name.")
            return

        # Convert the RGB image to BGR format
        bgr_image = cv2.cvtColor(self.original_grid, cv2.COLOR_RGBA2BGRA)

        # Save the image
        export_path = os.path.join(folder_path, base_name)
        cv2.imwrite(export_path, bgr_image)

        QMessageBox.information(self, "Image Exported", f"The image was successfully exported to {export_path}.")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_win = AppDemo()
    main_win.show()

    sys.exit(app.exec())
