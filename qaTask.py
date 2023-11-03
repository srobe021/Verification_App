import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,\
    QLineEdit, QFileDialog, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import QFileSystemWatcher, QDateTime
from zipfile import ZipFile, ZIP_DEFLATED

class FileCompressor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TE Verification Tracker")
        self.infiles = []
        self.destination = ""
        self.init_ui()

         # add QFileSystemWatcher for desktop
        self.fileWatcher = QFileSystemWatcher(self)
        self.fileWatcher.addPath(os.path.expanduser("~/Desktop"))  # adjust the path if need
        self.fileWatcher.directoryChanged.connect(self.directory_changed)

        # disable watcher initially
        self.fileWatcher.blockSignals(True)

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.feature_input = QLineEdit(self)
        self.feature_input.setPlaceholderText('Feature')
        self.layout.addWidget(self.feature_input)
        
        self.ticket_number_input = QLineEdit(self)
        self.ticket_number_input.setPlaceholderText('Ticket Number (required)')
        self.layout.addWidget(self.ticket_number_input)
        
        self.environment_input = QLineEdit(self)
        self.environment_input.setPlaceholderText('Environment (required)')
        self.layout.addWidget(self.environment_input)

        self.btn_destination = QPushButton('Select destination', self)
        self.btn_destination.clicked.connect(self.select_destination)
        self.layout.addWidget(self.btn_destination)

        self.btn_start_verification = QPushButton('Start Verification', self)
        self.btn_start_verification.clicked.connect(self.start_verification)
        self.layout.addWidget(self.btn_start_verification)

        self.btn_select_files = QPushButton('Select Files', self)
        self.btn_select_files.clicked.connect(self.select_files)
        self.layout.addWidget(self.btn_select_files)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Selected files")
        self.layout.addWidget(self.tree)
        
        self.btn_compress_files = QPushButton('Compress Files', self)
        self.btn_compress_files.clicked.connect(self.compress_files)
        self.layout.addWidget(self.btn_compress_files)

        self.btn_restart = QPushButton('Restart', self)
        self.btn_restart.clicked.connect(self.restart)
        self.layout.addWidget(self.btn_restart)

    def select_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        selected_files, _ = QFileDialog.getOpenFileNames(parent=self,
                                                      caption="Select files to compress", 
                                                      filter="Images or Videos (*.png *.jpg *.mov);;\
                                                              Images (*.png *.jpg);;\
                                                              Videos (*.mp4 *.mov)", 
                                                      options=options)
                                                      
        ticket_num = self.ticket_number_input.text().strip()
        environment = self.environment_input.text().strip()
        feature = self.feature_input.text().strip()

        if not ticket_num or not environment:
            print("Ticket Number and Environment fields are required")
            return

        # only add new files that are not already in self.infiles
        new_files = [x for x in selected_files if x not in self.infiles]
        counter = len(self.infiles) + 1  # initialize counter based on current infile number

        for file_path in new_files:
            base_name = f"{ticket_num}_{environment}_{feature}_{counter}"
            extension = os.path.splitext(file_path)[-1]
            new_file_name = f"{base_name}{extension}"
            parent_dir = os.path.dirname(file_path)
            new_file_path = os.path.join(parent_dir, new_file_name)

            try:
                os.rename(file_path, new_file_path)  # rename the file
                self.infiles.append(new_file_path)
                QTreeWidgetItem(self.tree, [new_file_name])
                counter += 1  # Increase the counter
            except Exception as e:
                print(f"Error occurred while renaming file {file_path}: {e}")

    def select_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        selected_files, _ = QFileDialog.getOpenFileNames(parent=self,
                                                      caption="Select files to compress", 
                                                      filter="Images or Videos (*.png *.jpg *.mov);;\
                                                              Images (*.png *.jpg);;\
                                                              Videos (*.mp4 *.mov)", 
                                                      options=options)
                                                      
        ticket_num = self.ticket_number_input.text().strip()
        environment = self.environment_input.text().strip()
        feature = self.feature_input.text().strip()

        if not ticket_num or not environment:
            print("Ticket Number and Environment fields are required")
            return

        # only add new files that are not already in self.infiles
        new_files = [x for x in selected_files if x not in self.infiles]
        counter = len(self.infiles) + 1  # initialize counter based on current infile number

        for file_path in new_files:
            base_name = f"{ticket_num}_{environment}_{feature}_{counter}"
            extension = os.path.splitext(file_path)[-1]
            new_file_name = f"{base_name}{extension}"
            parent_dir = os.path.dirname(file_path)
            new_file_path = os.path.join(parent_dir, new_file_name)

            try:
                os.rename(file_path, new_file_path)  # rename the file
                self.infiles.append(new_file_path)
                QTreeWidgetItem(self.tree, [new_file_name])
                counter += 1  # Increase the counter
            except Exception as e:
                print(f"Error occurred while renaming file {file_path}: {e}")

            
    def select_destination(self):
        self.destination = QFileDialog.getExistingDirectory(parent=self, caption="Select destination folder")
        print(f"Selected destination: {self.destination}")

    def start_verification(self):
        self.infiles = []  # Clear self.infiles
        self.tree.clear()  # Clear tree widget
        self.fileWatcher.blockSignals(False)
        self.last_check_time = QDateTime.currentDateTime().toSecsSinceEpoch()  # Set the last_check_time to the current time
        print("File Verification Started!")

        self.btn_start_verification.setEnabled(False)  # Disable verification button

    def directory_changed(self, path):
        if len(self.infiles) < 40:
            currentFiles = set(os.listdir(path))
            lastTimeFiles = set([os.path.basename(x) for x in self.infiles])
            newFiles = list(currentFiles - lastTimeFiles)

            ticket_num = self.ticket_number_input.text().strip()  # Add This
            environment = self.environment_input.text().strip()  # Add This
            feature = self.feature_input.text().strip()  # Add This

            if not ticket_num or not environment:
                print("Ticket Number and Environment fields are required")
                return

            newlyAddedFiles = []
            for file in newFiles:
                file_path = os.path.join(path, file)
                try:
                    if os.path.getmtime(file_path) > self.last_check_time:
                        newlyAddedFiles.append(file_path)
                except FileNotFoundError:
                    print(f"The file {file_path} was not found.")
                
            newlyAddedFiles.sort(key=os.path.getmtime, reverse=True)  # Most recent files first
            newlyAddedFiles = newlyAddedFiles[:40 - len(self.infiles)]  # Trim the list if there are more than 40

            counter = len(self.infiles) + 1  # initialize counter base on current infile number

            for file_path in newlyAddedFiles:
                base_name = f"{ticket_num}_{environment}_{feature}_{counter}"
                extension = os.path.splitext(file_path)[-1]
                new_file_name = f"{base_name}{extension}"
                new_file_path = os.path.join(path, new_file_name)
                
                try:
                    os.rename(file_path, new_file_path)  # rename the file
                    self.infiles.append(new_file_path)
                    QTreeWidgetItem(self.tree, [new_file_name])
                    counter += 1  # Increase the counter
                except Exception as e:
                    print(f"Error occurred while renaming file {file}: {e}")


    def compress_files(self):
        ticket_num = self.ticket_number_input.text().strip()
        environment = self.environment_input.text().strip()
        if not ticket_num or not environment:
            print("Ticket Number and Environment fields are required")
        elif not self.infiles:
            print("Please select at least one file")
        elif not self.destination:
            print("Please select a directory to save the compressed file")
        else:
            save_path = os.path.join(self.destination, f"{ticket_num}_{environment}.zip")
            with ZipFile(save_path, 'w', ZIP_DEFLATED) as zipf: 
                for file in self.infiles:
                    try:
                        zipf.write(file, arcname=os.path.basename(file))
                    except Exception as e:
                        print(f"An error occurred while compressing {file}. Error: {str(e)}")
            self.infiles = [] 
            self.tree.clear() 
            print(f"Files saved in {save_path}")

         # Clear the files after compression
        self.infiles = [] 
        self.tree.clear() 
        self.btn_start_verification.setEnabled(True)

    def restart(self):
        """
        Clears all fields, and restarts everything from initial state.
        """
        self.infiles = []
        self.destination = ""
        self.last_check_time = None
        self.fileWatcher.blockSignals(True)

        # Clear fields and tree widget
        self.feature_input.clear()
        self.ticket_number_input.clear()
        self.environment_input.clear()
        self.tree.clear()
        self.btn_start_verification.setEnabled(True)

        print("Restarted!")


def main():
    app = QApplication(sys.argv)
    compressor = FileCompressor()
    compressor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
