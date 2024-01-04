import json
import sys
import os
import threading
import random
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,\
    QLineEdit, QFileDialog, QTreeWidget, QTreeWidgetItem, QTextEdit, QBoxLayout, QListWidget, QListWidgetItem, QFrame, QProgressBar
from PyQt5.QtCore import QFileSystemWatcher, QDateTime, Qt, pyqtSignal
from zipfile import ZipFile, ZIP_DEFLATED
import sample

class FileCompressor(QWidget):
    MTCs_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ticket Verification Assistant")
        self.infiles = []
        self.destination = ""
        self.ticket_queue = []
        self.init_ui()

        # add QFileSystemWatcher for desktop
        self.fileWatcher = QFileSystemWatcher(self)
        self.fileWatcher.addPath(os.path.expanduser("~/Desktop"))
        # disable watcher initially
        self.fileWatcher.blockSignals(True)
        self.fileWatcher.directoryChanged.connect(self.directory_changed)

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Connect signal to a function to update UI
        self.MTCs_signal.connect(self.update_ticket_AI_display)

        # For your Acceptance Criteria
        self.AC_input = QLineEdit(self)
        self.AC_input.setPlaceholderText('Acceptance Criteria')
        self.AC_input.setFixedHeight(30)  # Change 50 to the desired height
        self.layout.addWidget(self.AC_input)

        # Add when the button is clicked
        self.AC_button = QPushButton('Submit Acceptance Criteria', self)
        self.AC_button.clicked.connect(self.on_submit)
        self.layout.addWidget(self.AC_button)

        self.ticket_AC_display = QTextEdit(self)
        self.ticket_AC_display.setPlaceholderText('Ticket AC will be displayed here')
        self.layout.addWidget(self.ticket_AC_display)

        # Progress Bar
        self.progressBar = QProgressBar(self)
        self.layout.addWidget(self.progressBar)
        self.progressBar.hide()  # Initially hidden

        self.ticket_AI_display = QTextEdit(self)
        self.ticket_AI_display.setPlaceholderText('AI generated manual test cases will be displayed here')
        self.layout.addWidget(self.ticket_AI_display)

        self.btn_stop_AI = QPushButton('Stop AI', self)
        self.btn_stop_AI.clicked.connect(self.stop_ai)
        self.layout.addWidget(self.btn_stop_AI)

        # Clear AC button
        self.clear_AC_button = QPushButton('Clear Acceptance Criteria', self)
        self.clear_AC_button.clicked.connect(self.clear_ac)
        self.layout.addWidget(self.clear_AC_button)

        # Line separator
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setStyleSheet("background-color: grey;")
        self.layout.addWidget(self.line)

        self.feature_input = QLineEdit(self)
        self.feature_input.setPlaceholderText('Feature')
        self.layout.addWidget(self.feature_input)

        self.ticket_number_input = QLineEdit(self)
        self.ticket_number_input.setPlaceholderText('Ticket Number (Required)')
        self.layout.addWidget(self.ticket_number_input)

        self.environment_input = QLineEdit(self)
        self.environment_input.setPlaceholderText('Environment (Required)')
        self.layout.addWidget(self.environment_input)

        self.device_browser_input = QLineEdit(self)
        self.device_browser_input.setPlaceholderText('Device/Browser')
        self.layout.addWidget(self.device_browser_input)

        self.btn_destination = QPushButton('Select Verification File Destination', self)
        self.btn_destination.clicked.connect(self.select_destination)
        self.layout.addWidget(self.btn_destination)

         #Add label to display the selected file destination
        self.destination_label = QLabel(self)
        self.layout.addWidget(self.destination_label)

        self.btn_start_verification = QPushButton('Start Verification', self)
        self.btn_start_verification.clicked.connect(self.start_verification)
        self.layout.addWidget(self.btn_start_verification)

        self.btn_select_files = QPushButton('Select Files', self)
        self.btn_select_files.clicked.connect(self.select_files)
        self.layout.addWidget(self.btn_select_files)

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Selected Files")
        self.layout.addWidget(self.tree)

        self.btn_compress_files = QPushButton('Compress Files', self)
        self.btn_compress_files.clicked.connect(self.compress_files)
        self.layout.addWidget(self.btn_compress_files)

        self.btn_restart = QPushButton('Clear Inputs', self)
        self.btn_restart.clicked.connect(self.restart)
        self.layout.addWidget(self.btn_restart)


        # Line separator
        self.line = QFrame(self)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setStyleSheet("background-color: grey;")
        self.layout.addWidget(self.line)
    
    def stop_ai(self):
        # Blocks the signals from QFileSystemWatcher, stopping the AI from monitoring
        # You may need to adjust this part to specifically target the AI portion of your program
        self.fileWatcher.blockSignals(True)

        # Stops the progress bar
        self.stop_progress()

        # Clear the text edit display for the AI generated manual test cases
        self.ticket_AI_display.clear()

    def start_progress(self):
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)  # Setting max to 0 creates an 'indeterminate' progress bar
        self.progressBar.show()
        self.AC_button.setEnabled(False)

    def stop_progress(self):
        self.progressBar.setValue(100)  # Full value will complete the progress bar
        self.progressBar.hide()
        self.AC_button.setEnabled(True)

    def update_progress(self):
        value = self.progressBar.value()
        if value < self.progressBar.maximum():
            self.progressBar.setValue(value + 1)
        else:
            self.progressBar.reset()

    def clear_ac(self):
        self.AC_input.clear()
        self.ticket_AC_display.clear()
        self.ticket_AI_display.clear()

    def on_submit(self):
        ac_text = self.AC_input.text().strip()
        # Save the acceptance criteria into ac_data.json
        with open('ac_data.json', 'w') as f:
            json.dump({'Acceptance Criteria': ac_text}, f)
        # Display in the ticket AC display
        self.ticket_AC_display.setText("Acceptance Criteria for selected ticket is: \n"  + ac_text)

        # Call the execute() function of sample.py and fetch the Manual Test Case 
        # Run in a separate thread to prevent UI blocking.
        self.start_progress()  # Start progress bar
        threading.Thread(target=self.fetch_manual_test_cases).start()
    
    def update_ticket_AI_display(self, MTCs):
        self.ticket_AI_display.setText(MTCs)

    def fetch_manual_test_cases(self):
        MTCs = sample.execute()
        self.MTCs_signal.emit(MTCs)
        self.stop_progress()  # Stop progress bar

    def get_tickets(self):
        for _ in range(10):  # generate 10 tickets
            self.ticket_queue.append(f'T{random.randint(10000, 99999)}')
        self.update_ticket_info_display()

    def update_ticket_info_display(self):
        self.ticket_info_display.clear()
        for ticket in self.ticket_queue:
            QListWidgetItem(ticket, self.ticket_info_display)

    def remove_ticket(self, item):
        self.ticket_queue.remove(item.text()) 
        self.update_ticket_info_display()

    def display_AC_and_MTC(self, item):
        # clear previous displays
        self.ticket_AC_display.clear()
        self.ticket_AI_display.clear()

        # here we are just generating random AC and MTC for demonstration.
        # in reality, you need to fetch relevant details either from your server or some local cache.
        random_AC = f"Acceptance Criteria for {item.text()}: \n 1. Some criteria \n 2. Some criteria \n 3. Some criteria"
        random_MTC = f"AI Manual Test Cases for {item.text()}: \n 1. Some test case \n 2. Some test case \n 3. Some test case"

        self.ticket_AC_display.setText(random_AC)
        self.ticket_AI_display.setText(random_MTC)

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
        device_browser = self.device_browser_input.text().strip()  # Get device/browser information
        feature = self.feature_input.text().strip()

        if not ticket_num or not environment or not device_browser:  # check if device/browser information is provided
            print("Ticket Number, Environment, and Device/Browser fields are required")
            return

        # only add new files that are not already in self.infiles
        new_files = [x for x in selected_files if x not in self.infiles]
        counter = len(self.infiles) + 1  # initialize counter based on current infile number

        for file_path in new_files:
            base_name = f"{ticket_num}_{environment}_{device_browser}_{feature}_{counter}"  # include device/browser in basename
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
        device_browser = self.device_browser_input.text().strip() # Device/browser field is optional


        if not ticket_num or not environment:
            print("Ticket Number and Environment fields are required")
            return

        # only add new files that are not already in self.infiles
        new_files = [x for x in selected_files if x not in self.infiles]
        counter = len(self.infiles) + 1  # initialize counter based on current infile number

        for file_path in new_files:
            base_name = f"{ticket_num}_{environment}_{device_browser if device_browser else 'unknown'}_{feature}_{counter}" 
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
        
        # update destination label
        self.destination_label.setText(f"Selected destination: {self.destination}")

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
            device_browser = self.device_browser_input.text().strip()  # Retrieve device/browser information


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
                base_name = f"{ticket_num}_{environment}_{device_browser if device_browser else 'unknown'}_{feature}_{counter}" 
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
        self.device_browser_input.clear()
        self.tree.clear()
        self.btn_start_verification.setEnabled(True)

        print("Restarted!")


    def display_AC_and_MTC(self, item):
        # clear previous displays
        self.ticket_AC_display.clear()
        self.ticket_AI_display.clear()

        import sample  # import the sample module
        MTCs = sample.execute()   # call the execute() function of sample.py     
        self.ticket_AI_display.setText(MTCs)  # show MTCs in its place

def main():
    app = QApplication(sys.argv)
    compressor = FileCompressor()
    compressor.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
