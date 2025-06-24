# UART Command Sender for CH341 (PyQt6)

A modern, professional GUI application for sending commands over UART using CH341 USB-to-Serial converter chips. Built with PyQt6 for a superior user experience with enhanced performance and modern styling.

## Features

### Modern PyQt6 Interface
- **Professional dark theme** - Easy on the eyes with syntax highlighting
- **Responsive layout** - Resizable interface with proper widget scaling
- **Modern styling** - Custom stylesheet with rounded corners and hover effects
- **Threaded serial communication** - Non-blocking UI with dedicated reading thread

### Connection Management
- **Auto-detection of CH341/CH340 devices** - Automatically identifies and highlights CH341-based serial ports
- **Flexible serial configuration** - Support for various baud rates (9600 to 921600), data bits, parity, and stop bits
- **Real-time connection status** - Visual indicators with color-coded status messages
- **Quick connection toggle** - Single button to connect/disconnect with visual feedback

### Advanced Command Interface
- **Interactive command input** - Type commands with Enter key support and modern text styling
- **Smart command history** - Navigate through previously sent commands using Up/Down arrow keys
- **Multiple data formats** - Send commands in ASCII or HEX format with validation
- **Configurable line endings** - Support for different line ending formats (\r, \n, \r\n, or none)
- **Real-time validation** - Input validation for HEX format commands

### Enhanced Terminal Output
- **Color-coded messages** - Different colors for sent commands, received data, errors, and system messages
- **Dark terminal theme** - Professional dark background with colored text for better readability
- **Timestamped logging** - Automatic timestamps for all messages with millisecond precision
- **Auto-scroll option** - Automatically scroll to latest messages (can be toggled)
- **Rich text support** - HTML formatting for better message presentation

### Improved Quick Commands
- **Predefined command library** - Common AT commands and test commands pre-loaded
- **Custom command management** - Add, remove, and manage frequently used commands
- **Import/Export functionality** - Save and load command sets as JSON files
- **Double-click execution** - Quick execution of saved commands
- **Persistent storage** - Commands are preserved between sessions

## Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- CH341/CH340 USB-to-Serial adapter
- USB drivers for CH341 (usually auto-installed on modern systems)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd UART_Command_Sender
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

   Or use the provided batch file on Windows:
   ```bash
   run.bat
   ```

## PyQt6 Advantages

This version uses PyQt6 instead of tkinter, providing:

- **Better Performance**: Native platform widgets with hardware acceleration
- **Modern Appearance**: Professional look that matches the operating system
- **Enhanced Threading**: Proper signal/slot mechanism for thread communication
- **Scalable UI**: Better support for high-DPI displays and different screen sizes
- **Rich Styling**: CSS-like stylesheets for complete visual customization
- **Better Responsiveness**: Non-blocking UI operations with proper event handling

## Usage

### Basic Setup

1. **Connect your CH341 device** to a USB port
2. **Launch the application** - CH341 ports will be highlighted in the port list
3. **Select your device** from the Port dropdown (CH341 devices are marked)
4. **Configure serial parameters** (baud rate defaults to 115200 for modern devices)
5. **Click Connect** to establish the connection (button turns red when connected)

### Sending Commands

1. **Type your command** in the command input field (supports monospace font for clarity)
2. **Choose format** - ASCII for text commands, HEX for binary data (with validation)
3. **Select line ending** - Choose appropriate line ending for your device
4. **Press Enter** or click Send to transmit the command

### Advanced Features

- **Command History**: Use Up/Down arrow keys to navigate through command history
- **Quick Commands**: Double-click any command in the list to execute it immediately
- **Log Management**: Save all terminal output to a text file for analysis
- **HEX Mode**: Send binary data by entering hex values (e.g., "48 65 6C 6C 6F" for "Hello")
- **Real-time Monitoring**: View incoming data in real-time with color coding
- **Resizable Interface**: Adjust terminal and quick commands panel sizes as needed

## Common Use Cases

### ESP32/ESP8266 Development
```
AT                    # Test connectivity
AT+GMR               # Get firmware version
AT+CWLAP             # List available WiFi networks
AT+CWJAP="SSID","PWD" # Connect to WiFi
```

### Microcontroller Communication
```
help                 # Get available commands
version              # Check firmware version
status               # Get system status
reset                # Reset the device
```

### Industrial Equipment Testing
- Interface with UART-based industrial devices
- Send control commands with precise timing
- Monitor status responses with timestamped logs

## Troubleshooting

### Port Not Detected
1. Ensure CH341 drivers are installed (Device Manager on Windows)
2. Check if device appears in system's device list
3. Try different USB ports or cables
4. Verify the device is not in use by another application

### Connection Issues
1. Verify baud rate matches your target device (try 115200 first)
2. Check data bits, parity, and stop bits configuration
3. Ensure proper cable connections (TX/RX not crossed unless needed)
4. Try different line ending settings (\\r\\n is most common)

### PyQt6 Issues
1. Ensure PyQt6 is properly installed: `pip install PyQt6`
2. Check Python version compatibility (3.8+)
3. On Linux, may need additional packages: `sudo apt-get install python3-pyqt6`

## CH341 Specific Features

The application provides optimized support for CH341 chips:
- **Automatic detection** - CH341 devices are clearly marked in the port list
- **Optimal defaults** - Pre-configured with settings that work best with CH341
- **Error handling** - Specific error messages for common CH341 issues
- **Performance tuning** - Optimized read/write operations for CH341 characteristics

## File Structure

```
UART_Command_Sender/
├── main.py           # Main application file (PyQt6)
├── requirements.txt  # Python dependencies
├── style.qss         # PyQt6 stylesheet
├── config.json       # Configuration file
├── run.bat          # Windows launcher
└── README.md        # This file
```

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool. The PyQt6 version provides a solid foundation for additional features.

## License

This project is licensed under the MIT License - see the LICENSE file for details.