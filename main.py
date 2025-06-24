#!/usr/bin/env python3
"""
UART Command Sender for CH341 Chip
A GUI application for sending commands over UART using CH341 USB-to-Serial converter
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QWidget, QLabel, QComboBox, QPushButton, 
                             QLineEdit, QTextEdit, QListWidget, QCheckBox, QGroupBox,
                             QMessageBox, QFileDialog, QSplitter, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QTextCursor, QColor
import serial
import serial.tools.list_ports
import threading
import time
import json
from datetime import datetime

class SerialReaderThread(QThread):
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, serial_connection):
        super().__init__()
        self.serial_connection = serial_connection
        self.is_running = True
    
    def run(self):
        while self.is_running:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.read(self.serial_connection.in_waiting)
                        if data:
                            self.data_received.emit(data)
                self.msleep(10)  # Small delay to prevent high CPU usage
            except Exception as e:
                if self.is_running:  # Only emit error if we're supposed to be running
                    self.error_occurred.emit(str(e))
                break
    
    def stop(self):
        self.is_running = False

class UARTCommandSender(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UART Command Sender - CH341")
        self.setGeometry(100, 100, 900, 700)
        
        # Serial connection
        self.serial_connection = None
        self.is_connected = False
        self.reader_thread = None
        
        # Command history
        self.command_history = []
        self.history_index = -1
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Connection settings group
        self.setup_connection_group(main_layout)
        
        # Command input group
        self.setup_command_group(main_layout)
        
        # Create splitter for terminal and quick commands
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Terminal output group
        self.setup_terminal_group(splitter)
        
        # Quick commands group
        self.setup_quick_commands_group(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
        
    def setup_connection_group(self, parent_layout):
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QGridLayout(conn_group)
        
        # Port selection
        conn_layout.addWidget(QLabel("Port:"), 0, 0)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        conn_layout.addWidget(self.port_combo, 0, 1)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)
        conn_layout.addWidget(self.refresh_button, 0, 2)
        
        # Baud rate
        conn_layout.addWidget(QLabel("Baud Rate:"), 0, 3)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("115200")
        conn_layout.addWidget(self.baud_combo, 0, 4)
        
        # Data bits
        conn_layout.addWidget(QLabel("Data Bits:"), 1, 0)
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        conn_layout.addWidget(self.databits_combo, 1, 1)
        
        # Parity
        conn_layout.addWidget(QLabel("Parity:"), 1, 2)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")
        conn_layout.addWidget(self.parity_combo, 1, 3)
        
        # Stop bits
        conn_layout.addWidget(QLabel("Stop Bits:"), 1, 4)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        conn_layout.addWidget(self.stopbits_combo, 1, 5)
        
        # Connect button and status
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setStyleSheet("QPushButton { padding: 8px 16px; font-weight: bold; }")
        button_layout.addWidget(self.connect_button)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        button_layout.addWidget(self.status_label)
        button_layout.addStretch()
        
        conn_layout.addLayout(button_layout, 2, 0, 1, 6)
        parent_layout.addWidget(conn_group)
        
    def setup_command_group(self, parent_layout):
        cmd_group = QGroupBox("Command Input")
        cmd_layout = QVBoxLayout(cmd_group)
        
        # Command entry and send button
        input_layout = QHBoxLayout()
        self.command_entry = QLineEdit()
        self.command_entry.setFont(QFont("Consolas", 10))
        self.command_entry.returnPressed.connect(self.send_command)
        self.command_entry.installEventFilter(self)  # For history navigation
        input_layout.addWidget(self.command_entry)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setEnabled(False)
        self.send_button.setStyleSheet("QPushButton { padding: 8px 16px; }")
        input_layout.addWidget(self.send_button)
        
        cmd_layout.addLayout(input_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        # Line ending
        options_layout.addWidget(QLabel("Line Ending:"))
        self.line_ending_combo = QComboBox()
        self.line_ending_combo.addItems(["None", "\\r", "\\n", "\\r\\n"])
        self.line_ending_combo.setCurrentText("\\r\\n")
        options_layout.addWidget(self.line_ending_combo)
        
        # Format
        options_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["ASCII", "HEX"])
        options_layout.addWidget(self.format_combo)
        
        # Auto scroll
        self.auto_scroll_checkbox = QCheckBox("Auto Scroll")
        self.auto_scroll_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_scroll_checkbox)
        
        options_layout.addStretch()
        cmd_layout.addLayout(options_layout)
        
        parent_layout.addWidget(cmd_group)
        
    def setup_terminal_group(self, parent_widget):
        terminal_group = QGroupBox("Terminal Output")
        terminal_layout = QVBoxLayout(terminal_group)
        
        # Terminal text area
        self.terminal_text = QTextEdit()
        self.terminal_text.setFont(QFont("Consolas", 9))
        self.terminal_text.setReadOnly(True)
        terminal_layout.addWidget(self.terminal_text)
        
        # Terminal control buttons
        terminal_controls = QHBoxLayout()
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_terminal)
        terminal_controls.addWidget(clear_button)
        
        save_log_button = QPushButton("Save Log")
        save_log_button.clicked.connect(self.save_log)
        terminal_controls.addWidget(save_log_button)
        
        load_commands_button = QPushButton("Load Commands")
        load_commands_button.clicked.connect(self.load_commands)
        terminal_controls.addWidget(load_commands_button)
        
        save_commands_button = QPushButton("Save Commands")
        save_commands_button.clicked.connect(self.save_commands)
        terminal_controls.addWidget(save_commands_button)
        
        terminal_controls.addStretch()
        terminal_layout.addLayout(terminal_controls)
        
        parent_widget.addWidget(terminal_group)
        
    def setup_quick_commands_group(self, parent_widget):
        quick_group = QGroupBox("Quick Commands")
        quick_layout = QVBoxLayout(quick_group)
        
        # Quick commands list
        self.quick_commands_list = QListWidget()
        self.quick_commands_list.setFont(QFont("Consolas", 9))
        self.quick_commands_list.itemDoubleClicked.connect(self.send_quick_command)
        quick_layout.addWidget(self.quick_commands_list)
        
        # Quick commands control buttons
        quick_controls = QHBoxLayout()
        
        add_button = QPushButton("Add Current")
        add_button.clicked.connect(self.add_quick_command)
        quick_controls.addWidget(add_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_quick_command)
        quick_controls.addWidget(remove_button)
        
        send_selected_button = QPushButton("Send Selected")
        send_selected_button.clicked.connect(self.send_quick_command)
        quick_controls.addWidget(send_selected_button)
        
        quick_controls.addStretch()
        quick_layout.addLayout(quick_controls)
        
        parent_widget.addWidget(quick_group)
        
        # Load default quick commands
        self.load_default_quick_commands()
        
    def eventFilter(self, obj, event):
        """Handle key events for command history navigation"""
        if obj == self.command_entry and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self.history_up()
                return True
            elif event.key() == Qt.Key.Key_Down:
                self.history_down()
                return True
        return super().eventFilter(obj, event)
        
    def refresh_ports(self):
        """Refresh the list of available serial ports"""
        self.port_combo.clear()
        ports = []
        for port in serial.tools.list_ports.comports():
            # Highlight CH341 ports
            if "CH340" in port.description or "CH341" in port.description:
                display_text = f"{port.device} - {port.description} [CH341]"
            else:
                display_text = f"{port.device} - {port.description}"
            
            self.port_combo.addItem(display_text, port.device)
            ports.append(display_text)
        
        # Auto-select first CH341 port if available
        if ports:
            ch341_ports = [i for i, p in enumerate(ports) if "[CH341]" in p]
            if ch341_ports:
                self.port_combo.setCurrentIndex(ch341_ports[0])
                
    def get_parity(self):
        """Convert parity string to pyserial constant"""
        parity_map = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD,
            "Mark": serial.PARITY_MARK,
            "Space": serial.PARITY_SPACE
        }
        return parity_map.get(self.parity_combo.currentText(), serial.PARITY_NONE)
    
    def get_stopbits(self):
        """Convert stopbits string to pyserial constant"""
        stopbits_map = {
            "1": serial.STOPBITS_ONE,
            "1.5": serial.STOPBITS_ONE_POINT_FIVE,
            "2": serial.STOPBITS_TWO
        }
        return stopbits_map.get(self.stopbits_combo.currentText(), serial.STOPBITS_ONE)
    
    def toggle_connection(self):
        """Connect or disconnect from serial port"""
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to the selected serial port"""
        try:
            port = self.port_combo.currentData()
            
            if not port:
                QMessageBox.warning(self, "Error", "Please select a port")
                return
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=int(self.baud_combo.currentText()),
                bytesize=int(self.databits_combo.currentText()),
                parity=self.get_parity(),
                stopbits=self.get_stopbits(),
                timeout=1
            )
            
            self.is_connected = True
            self.connect_button.setText("Disconnect")
            self.connect_button.setStyleSheet("QPushButton { padding: 8px 16px; font-weight: bold; background-color: #ff6b6b; }")
            self.send_button.setEnabled(True)
            self.status_label.setText(f"Connected to {port}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # Start reading thread
            self.reader_thread = SerialReaderThread(self.serial_connection)
            self.reader_thread.data_received.connect(self.handle_received_data)
            self.reader_thread.error_occurred.connect(self.handle_read_error)
            self.reader_thread.start()
            
            self.log_message(f"Connected to {port} at {self.baud_combo.currentText()} baud", "SYSTEM")
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            self.log_message(f"Connection failed: {str(e)}", "ERROR")
    
    def disconnect(self):
        """Disconnect from serial port"""
        try:
            if self.reader_thread:
                self.reader_thread.stop()
                self.reader_thread.wait(1000)  # Wait up to 1 second
            
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.is_connected = False
            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("QPushButton { padding: 8px 16px; font-weight: bold; }")
            self.send_button.setEnabled(False)
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            
            self.log_message("Disconnected", "SYSTEM")
            
        except Exception as e:
            self.log_message(f"Disconnect error: {str(e)}", "ERROR")
    
    def handle_received_data(self, data):
        """Handle data received from serial port"""
        try:
            decoded_data = data.decode('utf-8', errors='replace')
            self.log_message(decoded_data, "RECEIVED", add_timestamp=False)
        except:
            # If UTF-8 decoding fails, show as hex
            hex_data = ' '.join([f'{b:02X}' for b in data])
            self.log_message(f"HEX: {hex_data}", "RECEIVED")
    
    def handle_read_error(self, error_msg):
        """Handle read errors from serial thread"""
        self.log_message(f"Read error: {error_msg}", "ERROR")
    
    def send_command(self):
        """Send command over serial"""
        if not self.is_connected:
            QMessageBox.warning(self, "Warning", "Not connected to any port")
            return
        
        command = self.command_entry.text()
        if not command:
            return
        
        try:
            # Add to command history
            if command not in self.command_history:
                self.command_history.append(command)
            self.history_index = len(self.command_history)
            
            # Process command based on format
            if self.format_combo.currentText() == "HEX":
                # Remove spaces and convert hex string to bytes
                hex_string = command.replace(" ", "")
                if len(hex_string) % 2 != 0:
                    QMessageBox.warning(self, "Error", "Hex string must have even number of characters")
                    return
                data = bytes.fromhex(hex_string)
            else:
                # ASCII format
                data = command.encode('utf-8')
                
                # Add line ending if specified
                line_ending = self.line_ending_combo.currentText()
                if line_ending != "None":
                    line_ending = line_ending.replace("\\r", "\r").replace("\\n", "\n")
                    data += line_ending.encode('utf-8')
            
            # Send data
            self.serial_connection.write(data)
            
            # Log sent command
            display_command = command
            if self.format_combo.currentText() == "HEX":
                display_command = f"HEX: {command}"
            self.log_message(display_command, "SENT")
            
            # Clear command entry
            self.command_entry.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Send Error", f"Failed to send command: {str(e)}")
            self.log_message(f"Send error: {str(e)}", "ERROR")
    
    def log_message(self, message, msg_type="INFO", add_timestamp=True):
        """Add message to terminal output"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3] if add_timestamp else ""
        
        # Color coding based on message type
        color_map = {
            "SENT": "#0066cc",     # Blue
            "RECEIVED": "#008000", # Green
            "ERROR": "#cc0000",    # Red
            "SYSTEM": "#800080",   # Purple
            "INFO": "#000000"      # Black
        }
        
        # Format message
        if add_timestamp:
            formatted_message = f"[{timestamp}] [{msg_type}] {message}"
        else:
            formatted_message = message
        
        # Insert message with color
        cursor = self.terminal_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(f'<span style="color: {color_map.get(msg_type, "#000000")}">{formatted_message}</span><br>')
        
        # Auto-scroll if enabled
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.terminal_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_terminal(self):
        """Clear terminal output"""
        self.terminal_text.clear()
    
    def history_up(self):
        """Navigate up in command history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.setText(self.command_history[self.history_index])
    
    def history_down(self):
        """Navigate down in command history"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.setText(self.command_history[self.history_index])
        elif self.history_index >= len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.command_entry.clear()
    
    def load_default_quick_commands(self):
        """Load default quick commands for common UART testing"""
        default_commands = [
            "AT",
            "AT+GMR",
            "AT+CWLAP",
            "help",
            "version",
            "status",
            "reset",
            "echo off",
            "echo on",
            "info",
            "test",
            "ping"
        ]
        
        for cmd in default_commands:
            self.quick_commands_list.addItem(cmd)
    
    def add_quick_command(self):
        """Add current command to quick commands"""
        command = self.command_entry.text().strip()
        if command:
            # Check if command already exists
            existing_items = [self.quick_commands_list.item(i).text() 
                            for i in range(self.quick_commands_list.count())]
            if command not in existing_items:
                self.quick_commands_list.addItem(command)
    
    def remove_quick_command(self):
        """Remove selected quick command"""
        current_row = self.quick_commands_list.currentRow()
        if current_row >= 0:
            self.quick_commands_list.takeItem(current_row)
    
    def send_quick_command(self):
        """Send selected quick command"""
        current_item = self.quick_commands_list.currentItem()
        if current_item:
            command = current_item.text()
            self.command_entry.setText(command)
            self.send_command()
    
    def save_log(self):
        """Save terminal log to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log", "", "Text files (*.txt);;All files (*.*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.terminal_text.toPlainText())
                QMessageBox.information(self, "Success", f"Log saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save log: {str(e)}")
    
    def save_commands(self):
        """Save quick commands to JSON file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Commands", "", "JSON files (*.json);;All files (*.*)"
        )
        if filename:
            try:
                commands = [self.quick_commands_list.item(i).text() 
                          for i in range(self.quick_commands_list.count())]
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(commands, f, indent=2)
                QMessageBox.information(self, "Success", f"Commands saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save commands: {str(e)}")
    
    def load_commands(self):
        """Load quick commands from JSON file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Commands", "", "JSON files (*.json);;All files (*.*)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    commands = json.load(f)
                
                # Clear existing commands and load new ones
                self.quick_commands_list.clear()
                for cmd in commands:
                    self.quick_commands_list.addItem(cmd)
                
                QMessageBox.information(self, "Success", f"Commands loaded from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load commands: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application closing"""
        if self.is_connected:
            self.disconnect()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("UART Command Sender")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("CH341 Tools")
    
    # Load stylesheet
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass  # Continue without stylesheet if file not found
    
    # Create and show main window
    window = UARTCommandSender()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()