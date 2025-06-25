#!/usr/bin/env python3
"""
UART GUI Module for CH341 Chip
PyQt6-based GUI interface that uses the uart_backend module
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QWidget, QLabel, QComboBox, QPushButton, 
                             QLineEdit, QTextEdit, QListWidget, QCheckBox, QGroupBox,
                             QMessageBox, QFileDialog, QSplitter, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QObject
from PyQt6.QtGui import QFont, QTextCursor, QColor
from datetime import datetime
from typing import Optional, List

from uart_backend import UARTBackend, SerialMessage, SerialPortInfo, QuickCommandsManager
from plugin_system import PluginManager


class SerialGUIBridge(QObject):
    """Bridge to convert backend callbacks to Qt signals"""
    data_received = pyqtSignal(object)  # SerialMessage
    connection_changed = pyqtSignal(bool, str)  # connected, status_text
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self, backend: UARTBackend):
        super().__init__()
        self.backend = backend
        
        # Connect backend callbacks to Qt signals
        self.backend.set_data_received_callback(self._on_data_received)
        self.backend.set_connection_changed_callback(self._on_connection_changed)
        self.backend.set_error_callback(self._on_error_occurred)
    
    def _on_data_received(self, message: SerialMessage):
        self.data_received.emit(message)
    
    def _on_connection_changed(self, connected: bool, status: str):
        self.connection_changed.emit(connected, status)
    
    def _on_error_occurred(self, error_msg: str):
        self.error_occurred.emit(error_msg)


class UARTCommandSenderGUI(QMainWindow):
    """Main GUI class for UART Command Sender"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UART Command Sender - CH341 (Modular)")
        self.setGeometry(100, 100, 900, 700)
          # Initialize backend components
        self.backend = UARTBackend()
        self.quick_commands = QuickCommandsManager()
        self.gui_bridge = SerialGUIBridge(self.backend)
        
        # Initialize plugin system
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins()
        
        # Command history for GUI navigation
        self.history_index = -1
        
        # Connect backend signals to GUI slots
        self.gui_bridge.data_received.connect(self.handle_data_received)
        self.gui_bridge.connection_changed.connect(self.handle_connection_changed)
        self.gui_bridge.error_occurred.connect(self.handle_error)
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
          # Connection settings group
        self.setup_connection_group(main_layout)
        
        # Command input group
        self.setup_command_group(main_layout)
        
        # Plugin control group
        self.setup_plugin_group(main_layout)
        
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
        """Setup connection settings group"""
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
        self.baud_combo.currentTextChanged.connect(self.update_backend_config)
        conn_layout.addWidget(self.baud_combo, 0, 4)
        
        # Data bits
        conn_layout.addWidget(QLabel("Data Bits:"), 1, 0)
        self.databits_combo = QComboBox()
        self.databits_combo.addItems(["5", "6", "7", "8"])
        self.databits_combo.setCurrentText("8")
        self.databits_combo.currentTextChanged.connect(self.update_backend_config)
        conn_layout.addWidget(self.databits_combo, 1, 1)
        
        # Parity
        conn_layout.addWidget(QLabel("Parity:"), 1, 2)
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")
        self.parity_combo.currentTextChanged.connect(self.update_backend_config)
        conn_layout.addWidget(self.parity_combo, 1, 3)
        
        # Stop bits
        conn_layout.addWidget(QLabel("Stop Bits:"), 1, 4)
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "1.5", "2"])
        self.stopbits_combo.setCurrentText("1")
        self.stopbits_combo.currentTextChanged.connect(self.update_backend_config)
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
        """Setup command input group"""
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
        
    def setup_plugin_group(self, parent_layout):
        """Setup plugin control group"""
        plugin_group = QGroupBox("Plugin Commands")
        plugin_layout = QGridLayout(plugin_group)
        
        # Plugin selection
        plugin_layout.addWidget(QLabel("Plugin:"), 0, 0)
        self.plugin_combo = QComboBox()
        self.plugin_combo.addItem("Select Plugin...")
        plugin_layout.addWidget(self.plugin_combo, 0, 1)
        
        # Refresh plugins button
        self.refresh_plugins_button = QPushButton("Refresh")
        self.refresh_plugins_button.clicked.connect(self.refresh_plugins)
        plugin_layout.addWidget(self.refresh_plugins_button, 0, 2)
        
        # Command selection
        plugin_layout.addWidget(QLabel("Command:"), 1, 0)
        self.plugin_command_combo = QComboBox()
        self.plugin_command_combo.addItem("Select Command...")
        plugin_layout.addWidget(self.plugin_command_combo, 1, 1, 1, 2)
        
        # Parameter input area
        self.plugin_params_widget = QWidget()
        self.plugin_params_layout = QGridLayout(self.plugin_params_widget)
        plugin_layout.addWidget(self.plugin_params_widget, 2, 0, 1, 3)
        
        # Send plugin command button
        self.send_plugin_button = QPushButton("Send Plugin Command")
        self.send_plugin_button.clicked.connect(self.send_plugin_command)
        self.send_plugin_button.setEnabled(False)
        plugin_layout.addWidget(self.send_plugin_button, 3, 0, 1, 3)
        
        # Response parsing area
        self.plugin_response_text = QTextEdit()
        self.plugin_response_text.setMaximumHeight(100)
        self.plugin_response_text.setReadOnly(True)
        self.plugin_response_text.setPlaceholderText("Plugin response parsing will appear here...")
        plugin_layout.addWidget(QLabel("Parsed Response:"), 4, 0)
        plugin_layout.addWidget(self.plugin_response_text, 5, 0, 1, 3)
        
        # Connect signals
        self.plugin_combo.currentTextChanged.connect(self.on_plugin_selected)
        self.plugin_command_combo.currentTextChanged.connect(self.on_plugin_command_selected)
        
        # Initialize with available plugins
        self.refresh_plugins()
        
        parent_layout.addWidget(plugin_group)
        
    def setup_terminal_group(self, parent_widget):
        """Setup terminal output group"""
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
        """Setup quick commands group"""
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
        
        # Load quick commands
        self.load_quick_commands()
        
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
    
    def update_backend_config(self):
        """Update backend configuration when GUI settings change"""
        self.backend.update_config(
            baudrate=int(self.baud_combo.currentText()),
            bytesize=int(self.databits_combo.currentText()),
            parity=self.parity_combo.currentText(),
            stopbits=self.stopbits_combo.currentText()
        )
    
    def refresh_ports(self):
        """Refresh the list of available serial ports"""
        self.port_combo.clear()
        ports = self.backend.get_available_ports()
        
        ch341_found = False
        for i, port in enumerate(ports):
            self.port_combo.addItem(str(port), port.device)
            if port.is_ch341 and not ch341_found:
                self.port_combo.setCurrentIndex(i)
                ch341_found = True
        
        if not ch341_found and ports:
            self.port_combo.setCurrentIndex(0)
    
    def toggle_connection(self):
        """Toggle connection state"""
        if self.backend.is_connected:
            self.backend.disconnect()
        else:
            port = self.port_combo.currentData()
            if port:
                self.update_backend_config()
                self.backend.connect(port)
    
    def handle_connection_changed(self, connected: bool, status: str):
        """Handle connection status changes from backend"""
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.send_button.setEnabled(connected)
        
        if connected:
            self.connect_button.setStyleSheet("QPushButton { padding: 8px 16px; font-weight: bold; background-color: #ff6b6b; }")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.connect_button.setStyleSheet("QPushButton { padding: 8px 16px; font-weight: bold; }")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        
        self.status_label.setText(status)
        self.log_message(status, "SYSTEM")
    
    def handle_error(self, error_msg: str):
        """Handle errors from backend"""
        self.log_message(error_msg, "ERROR")
        QMessageBox.warning(self, "Error", error_msg)
    
    def format_received_data(self, data: bytes, timestamp) -> str:
        """Format received data for display"""
        try:
            # Try to decode as text first
            text = data.decode('utf-8', errors='replace')
            # Show both text and hex for better debugging
            hex_str = ' '.join(f'{b:02X}' for b in data)
            return f"TEXT: {text} | HEX: {hex_str}"
        except:
            # Fall back to hex only
            hex_str = ' '.join(f'{b:02X}' for b in data)
            return f"HEX: {hex_str}"
    
    def send_command(self):
        """Send command using backend"""
        if not self.backend.is_connected:
            QMessageBox.warning(self, "Warning", "Not connected to any port")
            return
        
        command = self.command_entry.text()
        if not command:
            return
        
        format_type = self.format_combo.currentText()
        line_ending = self.line_ending_combo.currentText()
        
        success = self.backend.send_command(command, format_type, line_ending)
        if success:
            self.command_entry.clear()
            # Reset history index
            self.history_index = len(self.backend.get_history())
    
    def log_message(self, message: str, msg_type: str = "INFO", add_timestamp: bool = True):
        """Add message to terminal output with color coding"""
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
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
    
    def clear_terminal(self):
        """Clear terminal output"""
        self.terminal_text.clear()
    
    def history_up(self):
        """Navigate up in command history"""
        history = self.backend.get_history()
        if history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.setText(history[self.history_index])
    
    def history_down(self):
        """Navigate down in command history"""
        history = self.backend.get_history()
        if history and self.history_index < len(history) - 1:
            self.history_index += 1
            self.command_entry.setText(history[self.history_index])
        elif self.history_index >= len(history) - 1:
            self.history_index = len(history)
            self.command_entry.clear()
    
    def load_quick_commands(self):
        """Load quick commands into the list widget"""
        self.quick_commands_list.clear()
        for cmd in self.quick_commands.get_commands():
            self.quick_commands_list.addItem(cmd)
    
    def add_quick_command(self):
        """Add current command to quick commands"""
        command = self.command_entry.text().strip()
        if command and self.quick_commands.add_command(command):
            self.quick_commands_list.addItem(command)
    
    def remove_quick_command(self):
        """Remove selected quick command"""
        current_row = self.quick_commands_list.currentRow()
        if current_row >= 0:
            item = self.quick_commands_list.takeItem(current_row)
            if item:
                self.quick_commands.remove_command(item.text())
    
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
            if self.quick_commands.save_to_file(filename):
                QMessageBox.information(self, "Success", f"Commands saved to {filename}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save commands")
    
    def load_commands(self):
        """Load quick commands from JSON file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Commands", "", "JSON files (*.json);;All files (*.*)"
        )
        if filename:
            if self.quick_commands.load_from_file(filename):
                self.load_quick_commands()
                QMessageBox.information(self, "Success", f"Commands loaded from {filename}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load commands")
    
    def refresh_plugins(self):
        """Refresh the plugin list"""
        self.plugin_combo.clear()
        self.plugin_combo.addItem("Select Plugin...")
        
        plugins = self.plugin_manager.get_all_plugins()
        for plugin_name, plugin in plugins.items():
            if plugin.enabled:
                self.plugin_combo.addItem(plugin.name, plugin_name)
    
    def on_plugin_selected(self, plugin_name: str):
        """Handle plugin selection change"""
        self.plugin_command_combo.clear()
        self.plugin_command_combo.addItem("Select Command...")
        
        # Clear previous parameter widgets
        self.clear_plugin_params()
        
        if plugin_name and plugin_name != "Select Plugin...":
            plugin = self.plugin_manager.get_plugin(self.plugin_combo.currentData())
            if plugin:
                commands = plugin.get_commands()
                for command_name in commands.keys():
                    self.plugin_command_combo.addItem(command_name, command_name)
    
    def on_plugin_command_selected(self, command_name: str):
        """Handle plugin command selection change"""
        # Clear previous parameter widgets
        self.clear_plugin_params()
        
        if command_name and command_name != "Select Command...":
            plugin_name = self.plugin_combo.currentData()
            if plugin_name:
                plugin = self.plugin_manager.get_plugin(plugin_name)
                if plugin:
                    commands = plugin.get_commands()
                    if command_name in commands:
                        self.setup_plugin_params(commands[command_name])
                        self.send_plugin_button.setEnabled(True)
                        return
        
        self.send_plugin_button.setEnabled(False)
    
    def clear_plugin_params(self):
        """Clear all parameter input widgets"""
        while self.plugin_params_layout.count():
            child = self.plugin_params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def setup_plugin_params(self, command_info):
        """Setup parameter input widgets for the selected command"""
        if 'parameters' not in command_info:
            return
            
        row = 0
        for param_name, param_info in command_info['parameters'].items():
            # Add label
            label = QLabel(f"{param_name.replace('_', ' ').title()}:")
            self.plugin_params_layout.addWidget(label, row, 0)
            
            # Add input widget based on parameter type
            if param_info['type'] == 'choice':
                widget = QComboBox()
                widget.addItems(param_info['choices'])
                if 'default' in param_info:
                    index = widget.findText(str(param_info['default']))
                    if index >= 0:
                        widget.setCurrentIndex(index)
            elif param_info['type'] == 'int':
                widget = QLineEdit()
                if 'default' in param_info:
                    widget.setText(str(param_info['default']))
                widget.setPlaceholderText(f"Range: {param_info.get('min', 'N/A')} - {param_info.get('max', 'N/A')}")
            elif param_info['type'] == 'str':
                widget = QLineEdit()
                if 'default' in param_info:
                    widget.setText(str(param_info['default']))
                if 'description' in param_info:
                    widget.setPlaceholderText(param_info['description'])
            else:
                widget = QLineEdit()
                if 'default' in param_info:
                    widget.setText(str(param_info['default']))
            
            widget.setObjectName(param_name)
            self.plugin_params_layout.addWidget(widget, row, 1)
            row += 1
    
    def send_plugin_command(self):
        """Send command from the selected plugin"""
        if not self.backend.is_connected:
            QMessageBox.warning(self, "Warning", "Please connect to a serial port first.")
            return
            
        plugin_name = self.plugin_combo.currentData()
        command_name = self.plugin_command_combo.currentData()
        
        if not plugin_name or not command_name:
            return
        
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            return
        
        # Collect parameters from the UI
        parameters = {}
        for i in range(self.plugin_params_layout.count()):
            widget = self.plugin_params_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'objectName') and widget.objectName():
                param_name = widget.objectName()
                if isinstance(widget, QComboBox):
                    parameters[param_name] = widget.currentText()
                elif isinstance(widget, QLineEdit):
                    text = widget.text()
                    # Try to convert to int if it looks like a number
                    if text.isdigit() or (text.startswith('-') and text[1:].isdigit()):
                        parameters[param_name] = int(text)
                    else:
                        parameters[param_name] = text
        
        try:
            # Execute plugin command
            command_bytes = self.plugin_manager.execute_plugin_command(plugin_name, command_name, parameters)
            if command_bytes:
                # Send the command
                self.backend.send_data(command_bytes)
                
                # Format bytes for display
                hex_display = ' '.join(f'{b:02X}' for b in command_bytes)
                self.log_message(f"PLUGIN SENT [{plugin.name}:{command_name}]: {hex_display}", "SENT")
                
                # Store last plugin response handler for parsing incoming data
                self.last_plugin = plugin
            else:
                self.log_message(f"ERROR: Failed to generate command for {plugin.name}:{command_name}", "ERROR")
                
        except Exception as e:
            self.log_message(f"ERROR: Plugin command failed: {str(e)}", "ERROR")
    
    def handle_data_received(self, message: SerialMessage):
        """Handle received data from serial port"""
        # Display the raw data
        formatted_data = self.format_received_data(message.data, message.timestamp)
        self.log_message(formatted_data, "RECEIVED")
        
        # Try to parse with the last used plugin
        if hasattr(self, 'last_plugin') and self.last_plugin:
            try:
                parsed_response = self.last_plugin.parse_response(message.data)
                if parsed_response:
                    # Display parsed response in the plugin response area
                    response_text = ""
                    for key, value in parsed_response.items():
                        response_text += f"{key}: {value}\n"
                    
                    current_text = self.plugin_response_text.toPlainText()
                    if current_text:
                        current_text += "\n"
                    current_text += f"[{message.timestamp.strftime('%H:%M:%S')}] {response_text.strip()}"
                    self.plugin_response_text.setPlainText(current_text)
                      # Scroll to bottom
                    cursor = self.plugin_response_text.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.plugin_response_text.setTextCursor(cursor)
                    
            except Exception as e:
                # Parsing failed, but that's OK - just continue with raw display
                pass
    
    def closeEvent(self, event):
        """Handle application closing"""
        if self.backend.is_connected:
            self.backend.disconnect()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("UART Command Sender")
    app.setApplicationVersion("2.1")
    app.setOrganizationName("CH341 Tools")
    
    # Load stylesheet
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass  # Continue without stylesheet if file not found
    
    # Create and show main window
    window = UARTCommandSenderGUI()
    window.show()
    
    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
