#!/usr/bin/env python3
"""
UART Backend Module for CH341 Chip
Handles all serial communication logic independently from GUI
"""

import serial
import serial.tools.list_ports
import threading
import time
import json
from datetime import datetime
from typing import List, Callable, Optional, Dict, Any


class SerialPortInfo:
    """Container for serial port information"""
    def __init__(self, device: str, description: str, is_ch341: bool = False):
        self.device = device
        self.description = description
        self.is_ch341 = is_ch341
    
    def __str__(self):
        suffix = " [CH341]" if self.is_ch341 else ""
        return f"{self.device} - {self.description}{suffix}"


class SerialMessage:
    """Container for serial messages with metadata"""
    def __init__(self, data: bytes, msg_type: str = "RECEIVED", timestamp: Optional[datetime] = None):
        self.data = data
        self.msg_type = msg_type
        self.timestamp = timestamp or datetime.now()
        
    def decode_text(self, encoding: str = 'utf-8') -> str:
        """Decode data as text, with fallback to hex representation"""
        try:
            return self.data.decode(encoding, errors='replace')
        except:
            return ' '.join([f'{b:02X}' for b in self.data])
    
    def to_hex_string(self) -> str:
        """Convert data to hex string representation"""
        return ' '.join([f'{b:02X}' for b in self.data])


class UARTBackend:
    """Backend class for UART communication with CH341 devices"""
    
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.read_thread: Optional[threading.Thread] = None
        self.stop_reading = False
        
        # Callbacks for events
        self.on_data_received: Optional[Callable[[SerialMessage], None]] = None
        self.on_connection_changed: Optional[Callable[[bool, str], None]] = None
        self.on_error_occurred: Optional[Callable[[str], None]] = None
        
        # Configuration
        self.config = {
            'port': '',
            'baudrate': 115200,
            'bytesize': 8,
            'parity': 'None',
            'stopbits': '1',
            'timeout': 1
        }
        
        # Command history
        self.command_history: List[str] = []
        self.max_history = 100
    
    def set_data_received_callback(self, callback: Callable[[SerialMessage], None]):
        """Set callback for when data is received"""
        self.on_data_received = callback
    
    def set_connection_changed_callback(self, callback: Callable[[bool, str], None]):
        """Set callback for connection status changes"""
        self.on_connection_changed = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Set callback for error events"""
        self.on_error_occurred = callback
    
    def get_available_ports(self) -> List[SerialPortInfo]:
        """Get list of available serial ports, highlighting CH341 devices"""
        ports = []
        for port in serial.tools.list_ports.comports():
            is_ch341 = "CH340" in port.description or "CH341" in port.description
            ports.append(SerialPortInfo(port.device, port.description, is_ch341))
        return ports
    
    def get_ch341_ports(self) -> List[SerialPortInfo]:
        """Get list of CH341 devices only"""
        return [port for port in self.get_available_ports() if port.is_ch341]
    
    def update_config(self, **kwargs):
        """Update connection configuration"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
    
    def get_parity_constant(self, parity_str: str) -> int:
        """Convert parity string to pyserial constant"""
        parity_map = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD,
            "Mark": serial.PARITY_MARK,
            "Space": serial.PARITY_SPACE
        }
        return parity_map.get(parity_str, serial.PARITY_NONE)
    
    def get_stopbits_constant(self, stopbits_str: str) -> float:
        """Convert stopbits string to pyserial constant"""
        stopbits_map = {
            "1": serial.STOPBITS_ONE,
            "1.5": serial.STOPBITS_ONE_POINT_FIVE,
            "2": serial.STOPBITS_TWO
        }
        return stopbits_map.get(stopbits_str, serial.STOPBITS_ONE)
    
    def connect(self, port: str = None) -> bool:
        """Connect to serial port"""
        if self.is_connected:
            return True
        
        try:
            # Use provided port or configured port
            target_port = port or self.config['port']
            if not target_port:
                if self.on_error_occurred:
                    self.on_error_occurred("No port specified")
                return False
            
            # Create serial connection
            self.serial_connection = serial.Serial(
                port=target_port,
                baudrate=self.config['baudrate'],
                bytesize=self.config['bytesize'],
                parity=self.get_parity_constant(self.config['parity']),
                stopbits=self.get_stopbits_constant(self.config['stopbits']),
                timeout=self.config['timeout']
            )
            
            self.is_connected = True
            self.config['port'] = target_port
            
            # Start reading thread
            self.stop_reading = False
            self.read_thread = threading.Thread(target=self._read_serial_data, daemon=True)
            self.read_thread.start()
            
            # Notify connection status change
            if self.on_connection_changed:
                self.on_connection_changed(True, f"Connected to {target_port}")
            
            return True
            
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            if self.on_error_occurred:
                self.on_error_occurred(error_msg)
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from serial port"""
        if not self.is_connected:
            return True
        
        try:
            # Stop reading thread
            self.stop_reading = True
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=1)
            
            # Close serial connection
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.is_connected = False
            
            # Notify connection status change
            if self.on_connection_changed:
                self.on_connection_changed(False, "Disconnected")
            
            return True
            
        except Exception as e:
            error_msg = f"Disconnect error: {str(e)}"
            if self.on_error_occurred:
                self.on_error_occurred(error_msg)
            return False
    
    def _read_serial_data(self):
        """Read data from serial port in background thread"""
        while not self.stop_reading and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.is_open:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.read(self.serial_connection.in_waiting)
                        if data and self.on_data_received:
                            message = SerialMessage(data, "RECEIVED")
                            self.on_data_received(message)
                time.sleep(0.01)  # Small delay to prevent high CPU usage
            except Exception as e:
                if self.is_connected and self.on_error_occurred:
                    self.on_error_occurred(f"Read error: {str(e)}")
                break
    
    def send_data(self, data: bytes) -> bool:
        """Send raw bytes over serial"""
        if not self.is_connected or not self.serial_connection:
            if self.on_error_occurred:
                self.on_error_occurred("Not connected to any port")
            return False
        
        try:
            self.serial_connection.write(data)
            return True
        except Exception as e:
            if self.on_error_occurred:
                self.on_error_occurred(f"Send error: {str(e)}")
            return False
    
    def send_command(self, command: str, format_type: str = "ASCII", line_ending: str = "\\r\\n") -> bool:
        """Send command with specified format and line ending"""
        if not command:
            return False
        
        try:
            # Add to command history
            self.add_to_history(command)
            
            # Process command based on format
            if format_type.upper() == "HEX":
                # Remove spaces and convert hex string to bytes
                hex_string = command.replace(" ", "")
                if len(hex_string) % 2 != 0:
                    if self.on_error_occurred:
                        self.on_error_occurred("Hex string must have even number of characters")
                    return False
                data = bytes.fromhex(hex_string)
            else:
                # ASCII format
                data = command.encode('utf-8')
                
                # Add line ending if specified
                if line_ending != "None":
                    line_ending_bytes = line_ending.replace("\\r", "\r").replace("\\n", "\n")
                    data += line_ending_bytes.encode('utf-8')
            
            # Send data
            success = self.send_data(data)
            
            # Create sent message for logging
            if success and self.on_data_received:
                display_command = f"HEX: {command}" if format_type.upper() == "HEX" else command
                sent_message = SerialMessage(display_command.encode('utf-8'), "SENT")
                self.on_data_received(sent_message)
            
            return success
            
        except Exception as e:
            if self.on_error_occurred:
                self.on_error_occurred(f"Command send error: {str(e)}")
            return False
    
    def add_to_history(self, command: str):
        """Add command to history, maintaining max size"""
        if command and command not in self.command_history:
            self.command_history.append(command)
            # Keep history within limits
            if len(self.command_history) > self.max_history:
                self.command_history = self.command_history[-self.max_history:]
    
    def get_history(self) -> List[str]:
        """Get command history"""
        return self.command_history.copy()
    
    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()
    
    def save_config(self, filename: str) -> bool:
        """Save current configuration to file"""
        try:
            config_data = {
                'connection': self.config.copy(),
                'history': self.command_history
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            if self.on_error_occurred:
                self.on_error_occurred(f"Failed to save config: {str(e)}")
            return False
    
    def load_config(self, filename: str) -> bool:
        """Load configuration from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if 'connection' in config_data:
                self.config.update(config_data['connection'])
            
            if 'history' in config_data:
                self.command_history = config_data['history']
            
            return True
        except Exception as e:
            if self.on_error_occurred:
                self.on_error_occurred(f"Failed to load config: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information"""
        return {
            'connected': self.is_connected,
            'port': self.config['port'] if self.is_connected else None,
            'baudrate': self.config['baudrate'],
            'config': self.config.copy()
        }
    
    def __del__(self):
        """Cleanup on object destruction"""
        if self.is_connected:
            self.disconnect()


class QuickCommandsManager:
    """Manager for quick commands functionality"""
    
    def __init__(self):
        self.commands: List[str] = []
        self.load_defaults()
    
    def load_defaults(self):
        """Load default quick commands"""
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
        self.commands = default_commands.copy()
    
    def add_command(self, command: str) -> bool:
        """Add command to quick commands"""
        command = command.strip()
        if command and command not in self.commands:
            self.commands.append(command)
            return True
        return False
    
    def remove_command(self, command: str) -> bool:
        """Remove command from quick commands"""
        if command in self.commands:
            self.commands.remove(command)
            return True
        return False
    
    def remove_command_at_index(self, index: int) -> bool:
        """Remove command at specific index"""
        if 0 <= index < len(self.commands):
            del self.commands[index]
            return True
        return False
    
    def get_commands(self) -> List[str]:
        """Get list of quick commands"""
        return self.commands.copy()
    
    def clear_commands(self):
        """Clear all commands"""
        self.commands.clear()
    
    def save_to_file(self, filename: str) -> bool:
        """Save commands to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.commands, f, indent=2)
            return True
        except Exception:
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """Load commands from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.commands = json.load(f)
            return True
        except Exception:
            return False
