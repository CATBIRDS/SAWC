from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QMainWindow, QGridLayout, QMenu, QAction, QCheckBox, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QPixmap, QCursor, QIcon
from PyQt5.QtCore import Qt
import mmap
import os
from pathlib import Path
from PIL import Image
import subprocess
import sys


# Globals
image_file = ''
audio_file = ''
default_limit = 6000000.0
dimensions = [0,0] # [X,Y]
quality = [64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 500]
warning = 'NOTE: Your audio is larger than the chosen filesize limit. Your audio may have noticeable compression.'
majorWarning = 'NOTE: Your audio is larger than the chosen filesize limit. Your audio may have noticeable compression. \n\nWARNING: Your file is significantly higher than your chosen filesize limit! It is possible that no amount of compression will make this audio fit into the specified size! \nConsider increasing the limit, or trimming your audio.'
    

class FFMPEGHandler():
    def __init__(self):
        super().__init__()

    def audioConversion(self, parent, desired):
        global audio_file
        global image_file
        # Compare filesize to the desired file size
        if desired == '':
                desired = default_limit
        else:
            desired = float(desired) * 1000000
        # if image file exists, reduce the available desired space to accommodate
        if os.path.exists(image_file):
            desired -= os.path.getsize(image_file) * 2
        return self.determineQuality(self, desired)

    def getDuration(self, parent):
        global audio_file
        result = subprocess.Popen(["ffprobe", f"{os.path.split(audio_file)[1]}"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell=True)
        for x in result.stdout.readlines():
            if "Duration" in x.decode("utf-8"):
                duration = x[12:23].decode("utf-8")
                # parse hours, minutes, seconds from the duration string
                hours = int(duration[0:2])
                minutes = int(duration[3:5])
                seconds = int(duration[6:8])
                # calculate total seconds
                return hours * 3600 + minutes * 60 + seconds
        
    def determineQuality(self, parent, desired_filesize):
        global audio_file
        global default_limit
        global quality
        # Find the duration of the file, assuming it is audio
        duration = self.getDuration(self)
        if desired_filesize == '':
            desired_filesize = default_limit
        # Determine required bitrate to fit the duration into the desired file size
        print(f"{desired_filesize}")
        print(f"{duration}")
        bitrate = float(desired_filesize)  * 8 / 1000 / float(duration)
        # determine the closest value in the quality list to the bitrate that does not exceed bitrate
        for i in range(len(quality)):
            if quality[i] >= bitrate:
                try:
                    return quality[i-1]
                except ValueError:
                    return quality[0]
        return quality[10]
    
    def createWebM(self, parent, desired):
        global image_file
        global audio_file
        global quality
        global dimensions
        # Create a webm file using ffmpeg
        desired_quality = self.audioConversion(self, desired)
        # Get artist and title from the audio file
        artist = ''
        title = ''
        metadata = ''
        comment = ''
        result = subprocess.Popen(["ffprobe", f"{os.path.split(audio_file)[1]}"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell=True)
        for x in result.stdout.readlines():
            if "ARTIST" in x.decode("utf-8"):
                artist = x[22:].decode("utf-8")
            if "TITLE" in x.decode("utf-8"):
                title = x[22:].decode("utf-8")
            if "COMMENT" in x.decode("utf-8"):
                comment = x[22:].decode("utf-8")
        shill = comment + ' | This WebM was created using the Static Audio WebM Generator - github.com/CATBIRDS/SAWC'
        # If we don't have any metadata, use the filename
        if artist == '':
            if title == '':
                metadata = f"{Path(audio_file).stem}"
            else:
                metadata = f"{title}"
        elif title == '':
            metadata = f"{artist}"
        else:
            metadata = f"{artist} - {title}"

        # Create the webm file
        print(dimensions[0])
        print(dimensions[1])
        subprocess.call(["ffmpeg", "-framerate", "1", "-y", "-i", f"{os.path.split(image_file)[1]}", "-i", f"{os.path.split(audio_file)[1]}", "-c:v", "libvpx", "-b:v", "2M", "-c:a", "libvorbis", "-q:a", f"{quality.index(desired_quality)}", "-g", "10000", "-force_key_frames", "0", "-metadata", f"title={metadata}", "-metadata", f"comment={shill}",  "-vf", f"scale={dimensions[0]}:{dimensions[1]}", f"{os.path.split(audio_file)[1]}.webm"])
        output_file = str(f"{os.path.split(audio_file)[1]}.webm")
        # if longer than 5 minutes, evil bit magic
        if self.getDuration(self) > 300:
            self.bitHack(output_file)
    
    def bitHack(self, filename):
        # Replace the 4 bytes following the offset of hex value 0x448988 with 0x41124F80
        # Why? Don't worry about it.
        with open(filename, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0)
            offset = mm.find(b'\x44\x89\x88')
            mm.seek(offset)
            mm.write(b'\x41\x12\x4F\x80')
            mm.close()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        global image_file
        global audio_file
        global warning
        ffmpeg = FFMPEGHandler()
        icon = QPixmap(32, 32)
        icon.fill(Qt.transparent)
        self.window = QWidget()
        self.window.setWindowIcon(QIcon(icon))
        self.window.setWindowTitle('Static Audio WebM Creator')
        self.layout = QGridLayout()
        # Cover Image Picker
        self.image_button = QPushButton('Pick a cover image')
        # Cover Image Viewer
        self.filename_label = QLabel()
        self.filename_label.setText('No image selected.')
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setStyleSheet('border: 1px solid black')
        self.image_menu = QMenu(self.image_label)
        self.clear_action = QAction('Clear', self.image_menu)
        self.resize_action = QAction('Resize', self.image_menu)
        self.image_menu.addAction(self.clear_action)
        self.image_menu.addAction(self.resize_action)
        self.clear_action.triggered.connect(lambda: self.clearImage(self))
        self.resize_action.triggered.connect(lambda: ImageResizeWindow(self))
        self.image_label.setContextMenuPolicy(Qt.CustomContextMenu) 
        
        # Music File Picker
        self.music_button = QPushButton('Pick an audio file')
        self.music_label = QLabel()
        self.music_label.setText('No audio selected.')
        # File Size Input
        self.large_preset = QCheckBox('Use /wsg/ Filesize Limit (6MB)')
        self.large_preset.setChecked(True)
        self.size_warning = QLabel()
        #align to top of cell
        self.size_warning.setAlignment(Qt.AlignTop)
        self.size_warning.setWordWrap(True)
        self.size_warning.setStyleSheet('color: #ff6600; font-weight: bold')
        self.size_warning.setText(warning)
        self.size_warning.hide()
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText('6.0')
        self.size_input.setEnabled(False)
        # run togglePreset() when large_preset is toggled
        self.large_preset.stateChanged.connect(lambda: self.togglePreset(self))
        # Only allow positive integers in the input box
        self.size_input.setValidator(QDoubleValidator())
        # hide the warning if the input value is bigger than the audio file size
        self.size_input.textChanged.connect(lambda: self.size_warning.hide() if self.willAudioFit(self) else self.size_warning.show())
        self.size_input.textChanged.connect(lambda: self.size_warning.setText(majorWarning) if self.youreBoned(self) else self.size_warning.setText(warning))
        self.size_label = QLabel()
        self.size_suffix = QLabel()
        self.size_label.setText('Size:')
        self.size_suffix.setText('MB')
        # Put size input, label, and suffix in a container
        self.size_container = QHBoxLayout()
        self.size_container.addWidget(self.size_label)
        self.size_container.addWidget(self.size_input)
        self.size_container.addWidget(self.size_suffix)
        # Run button
        self.run_button = QPushButton('Generate WebM')
        self.run_button.setEnabled(False)
        # attach the button to the ffmpeg function
        self.run_button.clicked.connect(lambda: ffmpeg.createWebM(self, self.size_input.text()))
        # File Dialog Connection
        self.image_button.clicked.connect(lambda: FileDialog(self))
        # Music Dialog Connection
        self.music_button.clicked.connect(lambda: MusicDialog(self))
        # Add the buttons and labels to the layout
        self.layout.addWidget(self.image_button, 0, 0, 1, 1)
        self.layout.addWidget(self.filename_label, 1, 0, 1, 1)
        self.layout.addWidget(self.image_label, 2, 0, 2, 1)
        self.layout.addWidget(self.music_button, 0, 1, 1, 1)
        self.layout.addWidget(self.music_label, 1, 1, 1, 1)
        self.layout.addWidget(self.size_warning, 2, 1, 1, 1)
        self.layout.addWidget(self.large_preset, 3, 1, 1, 1)
        self.layout.addLayout(self.size_container, 4, 1, 1, 1)
        self.layout.addWidget(self.run_button, 5, 0, 2, 1)

        self.window.setLayout(self.layout)
        self.window.show()

    def togglePreset(self, parent):
        global audio_file
        if audio_file != '':
            file_size = os.path.getsize(audio_file)
            if parent.large_preset.isChecked():
                parent.size_input.setDisabled(True)
                if file_size > default_limit:
                    parent.size_warning.show()
                else:
                    parent.size_warning.hide()
            else:
                try:
                    if int(parent.size_input.text()) * 1000000 > file_size:
                        parent.size_warning.hide()
                    else:
                        parent.size_warning.show()
                except ValueError:
                    parent.size_warning.hide()
                parent.size_input.setDisabled(False)
        else:
            if parent.large_preset.isChecked():
                parent.size_input.setDisabled(True)
            else:
                parent.size_input.setDisabled(False)
    
    def clearImage(self, parent):
        global image_file
        global dimensions
        parent.image_label.clear()
        parent.filename_label.setText('No image selected.')
        image_file = ''
        dimensions = [0,0]
        self.image_label.customContextMenuRequested.disconnect()
        parent.run_button.setEnabled(False)
    
    def willAudioFit(self, parent):
        global audio_file
        global default_limit
        if not audio_file:
            return True
        try:
            input = float(parent.size_input.text())
            if input * 1000000 > os.path.getsize(audio_file):
                return True
            else:
                return False
        except ValueError:
            if default_limit > os.path.getsize(audio_file):
                return True
            else:
                return False
    
    def youreBoned(self, parent):
        global audio_file
        global default_limit
        if not audio_file:
            return False
        try:
            input = float(parent.size_input.text())
            if input * 1000000 * 20 < os.path.getsize(audio_file):
                return True
            else:
                return False
        except ValueError:
            if default_limit * 20 < os.path.getsize(audio_file):
                return True
            else:
                return False


class MusicDialog(QFileDialog):
    def __init__(self, parent):
        super().__init__()
        global audio_file
        global default_limit
        global warning
        global majorWarning
        # Open a file dialog for the user to pick a jpeg file
        file_path = QFileDialog.getOpenFileName(window, 'Open file', '', 'Audio (*.AAC *.ALAC *.APE *.DSF *.FLAC *.MP1 *.MP2 *.MP3 *.OGG *.WAV *.WMA);;All Files (*)')
        # If the user picked a file, set image_file to the file data and display the image in the image label
        if file_path[0]:
            audio_file = file_path[0]
            parent.music_label.setText(f'{os.path.split(file_path[0])[1]} ({round(os.path.getsize(file_path[0]) / 1000000, 1)} MB)')
            # get file size in MB
            file_size = os.path.getsize(audio_file)
            if parent.large_preset.isChecked():
                if file_size > default_limit:
                    parent.size_warning.show()
                    if file_size > default_limit * 20:
                        parent.size_warning.setText(majorWarning)
                    else:
                        parent.size_warning.setText(warning)
                else:
                    parent.size_warning.hide()
            else:
                try:
                    if float(parent.size_input.text()) * 1000000 > file_size:
                        parent.size_warning.hide()
                        if file_size > default_limit * 20:
                            parent.size_warning.setText(majorWarning)
                        else:
                            parent.size_warning.setText(warning)
                    else:
                        parent.size_warning.show()
                except ValueError:
                    parent.size_warning.hide()
            if os.path.exists(audio_file) and os.path.exists(image_file):
                parent.run_button.setEnabled(True)
                               

class FileDialog(QFileDialog):
    def __init__(self, parent):
        super().__init__()
        global image_file
        global dimensions
        # Open a file dialog for the user to pick a jpeg file
        file_path = QFileDialog.getOpenFileName(window, 'Open file', '', 'Images (*.APNG *.BMP *.GIF *.JFIF *.JPEG *.JPG *.PNG *.SVG *.TGA *.TIF *.TIFF *.WEBP);;All Files (*)')
        # If the user picked a file, set image_file to the file data and display the image in the image label
        if file_path[0]:
            # resize the image to fit the image label, and display the image
            parent.image_label.setPixmap(QPixmap(file_path[0]).scaled(parent.image_label.size(), Qt.KeepAspectRatio))
            parent.image_label.show()
            # Set image_file to the file path, so we can retain access to the full file after we've smashed it for the image label
            image_file = file_path[0]
            dimensions = [QPixmap(file_path[0]).width(), QPixmap(file_path[0]).height()]
            if os.path.getsize(image_file) > 1000000:
                display_size = f"{round(os.path.getsize(image_file) / 1000000, 1)} MB"
            else:
                display_size = f"{round(os.path.getsize(image_file) / 1000, 1)} KB"
            parent.filename_label.setText(os.path.split(image_file)[1] + f' ({dimensions[0]} x {dimensions[1]}, {display_size})')
            parent.image_label.customContextMenuRequested.connect(lambda: parent.image_menu.exec_(QCursor.pos()))
            if os.path.exists(audio_file) and os.path.exists(image_file):
                parent.run_button.setEnabled(True)


class ImageResizeWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        global image_file
        # Add a checkbox and two input boxes for the user to enter the width and height of the image
        self.working_image = QPixmap(image_file)
        # Get current Aspect Ratio of the image file
        self.aspect_ratio = self.working_image.width() / self.working_image.height()
        # When the checkbox is checked, the height box is disabled
        self.checkbox = QCheckBox('Lock Aspect Ratio')
        self.onlyInt = QIntValidator()
        self.width_input = QLineEdit()
        self.width_input.setValidator(self.onlyInt)
        # Set width input placeholder text to the current width of the image file
        self.width_input.setPlaceholderText(str(self.working_image.width()))
        self.height_input = QLineEdit()
        self.height_input.setValidator(self.onlyInt)
        # Set height input placeholder text to the current height of the image file
        self.height_input.setPlaceholderText(str(self.working_image.height()))
        # Add the checkbox and input boxes to the layout
        layout = QGridLayout()
        layout.addWidget(self.checkbox, 0, 0, 1, 1)
        layout.addWidget(self.width_input, 0, 1, 1, 1)
        layout.addWidget(self.height_input, 0, 2, 1, 1)
        # Create a window to hold the layout
        self.window = QWidget()
        self.window.setLayout(layout)
        # When the user clicks the checkbox, disable the height box
        self.checkbox.stateChanged.connect(lambda: self.height_input.setDisabled(self.checkbox.isChecked()))
        # If the height box is disabled, set the height to the width times the aspect ratio
        self.width_input.textChanged.connect(lambda: self.height_input.setText(self.ratio(self.width_input.text(), self.aspect_ratio)) if self.checkbox.isChecked() else None)
        # When the user clicks the 'Resize' button, resize the image
        resize_button = QPushButton('Resize')
        resize_button.clicked.connect(lambda: self.resizeImageHelper(self, parent))
        # Add the button to the layout
        layout.addWidget(resize_button, 1, 0, 1, 1)
        # Show the window
        self.window.show()

    def resizeImageHelper(self, parent, main):
        global image_file
        global dimensions
        # Get the width and height from the input boxes
        width = self.width_input.text()
        height = self.height_input.text()
        # If the width and height are not empty, resize the image and set the global output dimensions
        if width or height:
            # If either the width or height is empty, set them to the value of dimensions
            if not width:
                width = dimensions[0]
            if not height:
                height = dimensions[1]
            dimensions = [round(float(width)), round(float(height))]
            # Create a new QPixmap object with the new width and height
            working_image = QPixmap(image_file).scaled(round(float(width)), round(float(height)))
            # Set the image label to the new image
            main.image_label.setPixmap(working_image.scaled(main.image_label.size(), Qt.KeepAspectRatio))
            main.image_label.show()
            # if image filesize is larger than 1MB
            if os.path.getsize(image_file) > 1000000:
                display_size = f"{round(os.path.getsize(image_file) / 1000000, 1)} MB"
            else:
                display_size = f"{round(os.path.getsize(image_file) / 1000, 1)} KB"
            # Set the filename label to the new image filename and size
            main.filename_label.setText(os.path.split(image_file)[1] + f' ({dimensions[0]} x {dimensions[1]}, {display_size})')

            # Add a new menu item to the image menu
            self.reset_action = QAction('Reset Image Size', main.image_menu)
            main.image_menu.addAction(self.reset_action)
            # When the menu item is clicked, reset the image to the original size
            self.reset_action.triggered.connect(lambda: self.reset(self, main))

        # Close the window
        parent.window.close()

    def reset(self, parent, main):
        global dimensions
        global image_file
        main.image_label.setPixmap(QPixmap(image_file).scaled(main.image_label.size(), Qt.KeepAspectRatio))
        dimensions = [QPixmap(image_file).width(), QPixmap(image_file).height()]
        main.filename_label.setText(os.path.split(image_file)[1] + ' (' + str(dimensions[0]) + 'x' + str(dimensions[1]) + ')')
        main.image_menu.removeAction(self.reset_action)

    def ratio(self, width, ratio):
        if width:
            return str(round(float(width) * ratio))
        else:
            return ''


# The entire program, crammed into one function
def superFast():
    global image_file
    global audio_file
    global quality
    global default_limit
    im = Image.open(image_file)
    width, height = im.size
    durationResult = subprocess.Popen(["ffprobe", f"{os.path.split(audio_file)[1]}"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell=True)
    for x in durationResult.stdout.readlines():
        if "Duration" in x.decode("utf-8"):
            duration = x[12:23].decode("utf-8")
            hours = int(duration[0:2])
            minutes = int(duration[3:5])
            seconds = int(duration[6:8])
            duration = hours * 3600 + minutes * 60 + seconds
    bitrate = float(default_limit) * 8 / 1000 / float(duration)
    for i in range(len(quality)):
        if quality[i] >= bitrate:
            try:
                qValue = quality[i-1]
                break
            except ValueError:
                qValue = quality[0]
                break
    if not qValue:
        qValue = quality[10]
    metadataResult = subprocess.Popen(["ffprobe", f"{os.path.split(audio_file)[1]}"], stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell=True)
    comment = ''
    for x in metadataResult.stdout.readlines():
        if "ARTIST" in x.decode("utf-8"):
            artist = x[22:].decode("utf-8")
        if "TITLE" in x.decode("utf-8"):
            title = x[22:].decode("utf-8")
        if "COMMENT" in x.decode("utf-8"):
            comment = x[22:].decode("utf-8")
    shill = comment + ' | This WebM was created using the Static Audio WebM Generator - github.com/CATBIRDS/SAWC'
    if artist == '':
        if title == '':
            metadata = f"{Path(audio_file).stem}"
        else:
            metadata = f"{title}"
    elif title == '':
        metadata = f"{artist}"
    else:
        metadata = f"{artist} - {title}"
    subprocess.call(["ffmpeg", "-framerate", "1", "-y", "-i", f"{os.path.split(image_file)[1]}", "-i", f"{os.path.split(audio_file)[1]}", "-c:v", "libvpx", "-b:v", "2M", "-c:a", "libvorbis", "-q:a", f"{quality.index(qValue)}", "-g", "10000", "-force_key_frames", "0", "-metadata", f"title={metadata}", "-metadata", f"comment={shill}",  "-vf", f"scale={width}:{height}", f"{os.path.split(audio_file)[1]}.webm"])
    if duration > 300:
        with open(str(f"{os.path.split(audio_file)[1]}.webm"), 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0)
            offset = mm.find(b'\x44\x89\x88')
            mm.seek(offset)
            mm.write(b'\x41\x12\x4F\x80')
            mm.close()

# If someone drags and drops a file onto the app, run the program in "speed mode"
# This was added last minute, so sorry if it's a bit ugly
if len(sys.argv) == 3:
    extension_1 = os.path.splitext(sys.argv[1])[1]
    if extension_1 in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        image_file = sys.argv[1]
    elif extension_1 in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.m4b', '.m4p', '.m4r', '.m4v', '.mp4', '.mpa', '.mpc', '.mpp', '.mpv', '.oga', '.ogg', '.opus', '.spx', '.wv', '.ape']:
        audio_file = sys.argv[1]
    extension_2 = os.path.splitext(sys.argv[2])[1]
    if extension_2 in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        image_file = sys.argv[2]
    elif extension_2 in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.m4b', '.m4p', '.m4r', '.m4v', '.mp4', '.mpa', '.mpc', '.mpp', '.mpv', '.oga', '.ogg', '.opus', '.spx', '.wv', '.ape']:
        audio_file = sys.argv[2]
    superFast()
else:  
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec())