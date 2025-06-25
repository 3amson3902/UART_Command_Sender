#!/usr/bin/env python3
"""
Emm42 V5.0 Plugin Standalone Tester
Comprehensive testing utility for the Emm42 V5.0 stepper motor plugin
"""

import sys
import os
import time
import serial
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Add the current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plugin_system import UARTPlugin, ChecksumCalculator, PluginManager


class MockSerial:
    """Mock serial interface for testing without hardware"""
    
    def __init__(self, port: str, baudrate: int = 9600, **kwargs):
        self.port = port
        self.baudrate = baudrate
        self.is_open = False
        self.sent_data = []
        self.response_queue = []
        print(f"[MockSerial] Created mock connection to {port} at {baudrate} baud")
    
    def open(self):
        """Open the mock connection"""
        self.is_open = True
        print(f"[MockSerial] Opened connection to {self.port}")
    
    def close(self):
        """Close the mock connection"""
        self.is_open = False
        print(f"[MockSerial] Closed connection to {self.port}")
    
    def write(self, data: bytes) -> int:
        """Write data to mock serial"""
        if not self.is_open:
            raise Exception("Port not open")
        
        self.sent_data.append(data)
        hex_str = ' '.join([f'{b:02X}' for b in data])
        print(f"[MockSerial] SENT: {hex_str}")
        
        # Generate mock response based on command
        if len(data) >= 2:
            addr = data[0]
            func = data[1]
            mock_response = self._generate_mock_response(addr, func, data)
            if mock_response:
                self.response_queue.append(mock_response)
        
        return len(data)
    
    def read(self, size: int = 1) -> bytes:
        """Read data from mock serial"""
        if not self.is_open:
            raise Exception("Port not open")
        
        if self.response_queue:
            response = self.response_queue.pop(0)
            hex_str = ' '.join([f'{b:02X}' for b in response])
            print(f"[MockSerial] RECV: {hex_str}")
            return response
        
        return b''
    
    def in_waiting(self) -> int:
        """Return number of bytes waiting"""
        return len(self.response_queue) > 0
    
    def _generate_mock_response(self, addr: int, func: int, command: bytes) -> bytes:
        """Generate mock responses for testing"""
        # Standard success response
        if func in [0xF3, 0xF6, 0xFD, 0xFE, 0xFF, 0x93, 0x9A, 0x9C, 
                   0x06, 0x0A, 0x0E, 0x0F, 0x84, 0xAE, 0x46, 0x44, 
                   0x4C, 0xF7, 0x4F]:
            return bytes([addr, func, 0x02, 0x6B])  # Success response
        
        # Read commands with data
        elif func == 0x31:  # Read encoder value
            return bytes([addr, func, 0x1A, 0x2B, 0x6B])  # Mock encoder: 6699
        
        elif func == 0x32:  # Read input pulses  
            return bytes([addr, func, 0x00, 0x00, 0x03, 0x20, 0x00, 0x6B])  # Mock: +800 pulses
        
        elif func == 0x33:  # Read target position
            return bytes([addr, func, 0x00, 0x00, 0x0C, 0x80, 0x00, 0x6B])  # Mock: +3200 position
        
        elif func == 0x34:  # Read realtime target
            return bytes([addr, func, 0x00, 0x00, 0x0C, 0x80, 0x00, 0x6B])  # Mock: +3200 target
        
        elif func == 0x35:  # Read realtime speed
            return bytes([addr, func, 0x00, 0x00, 0x64, 0x6B])  # Mock: +100 RPM
        
        elif func == 0x36:  # Read realtime position
            return bytes([addr, func, 0x00, 0x00, 0x0C, 0x80, 0x00, 0x6B])  # Mock: +3200 position
        
        elif func == 0x37:  # Read position error
            return bytes([addr, func, 0x00, 0x00, 0x00, 0x05, 0x00, 0x6B])  # Mock: +5 error
        
        elif func == 0x3A:  # Read motor status
            return bytes([addr, func, 0x03, 0x6B])  # Mock: Enabled + In Position
        
        elif func == 0x3B:  # Read homing status
            return bytes([addr, func, 0x03, 0x6B])  # Mock: Encoder Ready + Table Ready
        
        elif func == 0x1F:  # Read firmware version
            return bytes([addr, func, 0x20, 0x15, 0x6B])  # Mock: FW 0x20, HW 0x15
        
        elif func == 0x20:  # Read motor parameters
            return bytes([addr, func, 0x01, 0x2C, 0x00, 0x64, 0x6B])  # Mock: 300mΩ, 100uH
        
        elif func == 0x21:  # Read PID parameters
            pid_data = [0x00, 0x00, 0x00, 0x64,  # Kp: 100
                       0x00, 0x00, 0x00, 0x32,  # Ki: 50
                       0x00, 0x00, 0x00, 0x0A]  # Kd: 10
            return bytes([addr, func] + pid_data + [0x6B])
        
        elif func == 0x24:  # Read bus voltage
            return bytes([addr, func, 0x2E, 0xE0, 0x6B])  # Mock: 12V (12000mV)
        
        elif func == 0x27:  # Read phase current
            return bytes([addr, func, 0x03, 0xE8, 0x6B])  # Mock: 1000mA
        
        elif func == 0x42:  # Read drive config
            return bytes([addr, func, 0x10, 0x02, 0x01, 0x6B])  # Mock config
        
        elif func == 0x43:  # Read system status
            return bytes([addr, func, 0x00, 0x01, 0x6B])  # Mock system status
        
        else:
            # Unknown command error
            return bytes([addr, 0x00, 0xEE, 0x6B])


class Emm42V5Tester:
    """Comprehensive tester for Emm42 V5.0 plugin"""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.serial_conn: Optional[serial.Serial] = None
        self.plugin: Optional[UARTPlugin] = None
        self.test_results: List[Dict[str, Any]] = []
        
        # Load the plugin
        self._load_plugin()
    
    def _load_plugin(self):
        """Load the Emm42 V5.0 plugin"""
        try:
            plugin_manager = PluginManager("plugins")
            plugin_manager.load_plugin("emm42_v5")
            self.plugin = plugin_manager.get_plugin("emm42_v5")
            
            if self.plugin:
                print(f"[Plugin] Loaded: {self.plugin.name}")
                print(f"[Plugin] Description: {self.plugin.description}")
            else:
                print("[ERROR] Failed to load emm42_v5 plugin")
                sys.exit(1)
                
        except Exception as e:
            print(f"[ERROR] Plugin loading failed: {e}")
            sys.exit(1)
    
    def connect_serial(self, port: str, baudrate: int = 9600) -> bool:
        """Connect to serial port or create mock connection"""
        try:
            if self.use_mock:
                self.serial_conn = MockSerial(port, baudrate, timeout=1)
            else:
                self.serial_conn = serial.Serial(port, baudrate, timeout=1)
            
            self.serial_conn.open()
            print(f"[Serial] Connected to {port} at {baudrate} baud")
            return True
            
        except Exception as e:
            print(f"[ERROR] Serial connection failed: {e}")
            return False
    
    def disconnect_serial(self):
        """Disconnect from serial port"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[Serial] Disconnected")
    
    def send_command(self, command: str, parameters: Dict[str, Any]) -> Tuple[bool, bytes, Optional[bytes]]:
        """Send a command and get response"""
        try:
            # Process command with plugin
            cmd_bytes = self.plugin.process_command(command, parameters)
            
            if not self.serial_conn or not self.serial_conn.is_open:
                print("[ERROR] Serial connection not available")
                return False, cmd_bytes, None
            
            # Send command
            self.serial_conn.write(cmd_bytes)
            
            # Wait for response
            time.sleep(0.1)
            response = b''
            
            # Read response (timeout after 1 second)
            start_time = time.time()
            while time.time() - start_time < 1.0:
                if self.serial_conn.in_waiting() > 0:
                    response = self.serial_conn.read(self.serial_conn.in_waiting())
                    break
                time.sleep(0.01)
            
            return True, cmd_bytes, response if response else None
            
        except Exception as e:
            print(f"[ERROR] Command execution failed: {e}")
            return False, b'', None
    
    def test_command(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test a single command and return results"""
        if parameters is None:
            parameters = {}
        
        print(f"\n[TEST] Testing command: {command}")
        print(f"[TEST] Parameters: {parameters}")
        
        test_result = {
            "command": command,
            "parameters": parameters.copy(),
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "sent_bytes": "",
            "received_bytes": "",
            "parsed_response": {},
            "human_readable": "",
            "error": None
        }
        
        try:
            # Send command
            success, sent_bytes, received_bytes = self.send_command(command, parameters)
            
            test_result["sent_bytes"] = ' '.join([f'{b:02X}' for b in sent_bytes])
            
            if received_bytes:
                test_result["received_bytes"] = ' '.join([f'{b:02X}' for b in received_bytes])
                
                # Parse response with plugin
                parsed = self.plugin.parse_response(received_bytes)
                test_result["parsed_response"] = parsed
                
                # Get human-readable response if plugin supports it
                if hasattr(self.plugin, 'response_to_human_readable'):
                    test_result["human_readable"] = self.plugin.response_to_human_readable(received_bytes)
                
                test_result["success"] = success
                
                print(f"[TEST] Sent: {test_result['sent_bytes']}")
                print(f"[TEST] Received: {test_result['received_bytes']}")
                if test_result["human_readable"]:
                    print(f"[TEST] Human readable: {test_result['human_readable']}")
            
            else:
                test_result["error"] = "No response received"
                print(f"[TEST] No response received")
        
        except Exception as e:
            test_result["error"] = str(e)
            print(f"[TEST] Error: {e}")
        
        self.test_results.append(test_result)
        return test_result
    
    def run_basic_tests(self):
        """Run basic functionality tests"""
        print("\n" + "="*60)
        print("RUNNING BASIC FUNCTIONALITY TESTS")
        print("="*60)
        
        # Test motor enable/disable
        self.test_command("motor_enable", {"address": 1, "enable": "Enable", "sync": "No"})
        self.test_command("motor_enable", {"address": 1, "enable": "Disable", "sync": "No"})
        
        # Test speed mode
        self.test_command("speed_mode", {
            "address": 1, "direction": "CW", "speed": 100, 
            "acceleration": 10, "sync": "No"
        })
        
        # Test position mode
        self.test_command("position_mode", {
            "address": 1, "direction": "CW", "speed": 100, 
            "acceleration": 10, "pulses": 3200, "mode": "Relative", "sync": "No"
        })
        
        # Test immediate stop
        self.test_command("immediate_stop", {"address": 1, "sync": "No"})
        
        # Test homing
        self.test_command("trigger_homing", {"address": 1, "mode": "Nearest", "sync": "No"})
        self.test_command("stop_homing", {"address": 1})
        
        # Test calibration and reset commands
        self.test_command("calibrate_encoder", {"address": 1})
        self.test_command("clear_position", {"address": 1})
        self.test_command("set_zero_position", {"address": 1, "save": "Yes"})
    
    def run_read_tests(self):
        """Run read command tests"""
        print("\n" + "="*60)
        print("RUNNING READ COMMAND TESTS")
        print("="*60)
        
        read_commands = [
            "read_firmware_version",
            "read_motor_params", 
            "read_pid_params",
            "read_bus_voltage",
            "read_phase_current",
            "read_encoder_value",
            "read_input_pulses",
            "read_target_position",
            "read_realtime_target",
            "read_realtime_speed", 
            "read_realtime_position",
            "read_position_error",
            "read_motor_status",
            "read_homing_status",
            "read_drive_config",
            "read_system_status"
        ]
        
        for cmd in read_commands:
            self.test_command(cmd, {"address": 1})
    
    def run_modify_tests(self):
        """Run modify parameter tests"""
        print("\n" + "="*60)
        print("RUNNING MODIFY PARAMETER TESTS")
        print("="*60)
        
        # Test subdivision modification
        self.test_command("modify_subdivision", {
            "address": 1, "save": "Yes", "subdivision": 32
        })
        
        # Test ID address modification
        self.test_command("modify_id_address", {
            "address": 1, "save": "No", "new_id": 2
        })
        
        # Test open/closed loop switching
        self.test_command("switch_open_closed_loop", {
            "address": 1, "save": "Yes", "mode": "Closed Loop"
        })
        
        # Test current modification
        self.test_command("modify_open_loop_current", {
            "address": 1, "save": "No", "current": 1500
        })
        
        # Test speed scale modification
        self.test_command("modify_speed_scale", {
            "address": 1, "save": "Yes", "scale_enable": "Enable"
        })
    
    def run_checksum_tests(self):
        """Run tests with different checksum types"""
        print("\n" + "="*60)
        print("RUNNING CHECKSUM TYPE TESTS")
        print("="*60)
        
        checksum_types = ["fixed_0x6B", "xor", "crc8"]
        
        for checksum_type in checksum_types:
            print(f"\n[CHECKSUM] Testing with {checksum_type}")
            self.test_command("motor_enable", {
                "address": 1, "enable": "Enable", "sync": "No",
                "checksum_type": checksum_type
            })
    
    def run_stress_tests(self):
        """Run stress tests with rapid commands"""
        print("\n" + "="*60)
        print("RUNNING STRESS TESTS")
        print("="*60)
        
        # Rapid enable/disable cycles
        for i in range(5):
            self.test_command("motor_enable", {"address": 1, "enable": "Enable"})
            time.sleep(0.05)
            self.test_command("motor_enable", {"address": 1, "enable": "Disable"})
            time.sleep(0.05)
        
        # Multiple address tests
        for addr in range(1, 4):
            self.test_command("read_motor_status", {"address": addr})
    
    def run_custom_command_tests(self):
        """Run custom command tests"""
        print("\n" + "="*60)
        print("RUNNING CUSTOM COMMAND TESTS")
        print("="*60)
        
        # Test custom command with manual hex data
        self.test_command("custom_command", {
            "address": 1,
            "func_code": 0x06,
            "data": "45",
            "checksum_type": "fixed_0x6B"
        })
        
        # Test custom command with multiple bytes
        self.test_command("custom_command", {
            "address": 1,
            "func_code": 0x84,
            "data": "8A 01 20",
            "checksum_type": "xor"
        })
    
    def run_all_tests(self):
        """Run all test suites"""
        print("Emm42 V5.0 Plugin Comprehensive Tester")
        print("="*60)
        print(f"Mode: {'Mock Hardware' if self.use_mock else 'Real Hardware'}")
        print(f"Plugin: {self.plugin.name if self.plugin else 'Not loaded'}")
        
        start_time = time.time()
        
        self.run_basic_tests()
        self.run_read_tests()
        self.run_modify_tests()
        self.run_checksum_tests()
        self.run_stress_tests()
        self.run_custom_command_tests()
        
        end_time = time.time()
        
        self.print_test_summary(end_time - start_time)
    
    def print_test_summary(self, duration: float):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests run: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['command']}: {result.get('error', 'Unknown error')}")
        
        print(f"\nDETAILED RESULTS:")
        for i, result in enumerate(self.test_results, 1):
            status = "PASS" if result["success"] else "FAIL"
            print(f"  {i:2d}. [{status}] {result['command']}")
            if result.get("human_readable"):
                print(f"      Response: {result['human_readable']}")
    
    def save_test_report(self, filename: str = None):
        """Save detailed test report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"emm42_v5_test_report_{timestamp}.json"
        
        import json
        
        report_data = {
            "test_info": {
                "plugin_name": self.plugin.name if self.plugin else "Unknown",
                "test_mode": "Mock Hardware" if self.use_mock else "Real Hardware",
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r["success"]),
                "failed_tests": sum(1 for r in self.test_results if not r["success"])
            },
            "test_results": self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"[REPORT] Detailed test report saved to: {filename}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Emm42 V5.0 Plugin Tester")
    parser.add_argument("--port", default="COM3", help="Serial port (default: COM3)")
    parser.add_argument("--baudrate", type=int, default=9600, help="Baud rate (default: 9600)")
    parser.add_argument("--real-hardware", action="store_true", help="Use real hardware instead of mock")
    parser.add_argument("--save-report", action="store_true", help="Save detailed test report")
    parser.add_argument("--test-single", help="Test single command only")
    parser.add_argument("--address", type=int, default=1, help="Device address (default: 1)")
    
    args = parser.parse_args()
    
    # Create tester
    tester = Emm42V5Tester(use_mock=not args.real_hardware)
    
    # Connect to serial
    if not tester.connect_serial(args.port, args.baudrate):
        print("Failed to connect to serial port")
        sys.exit(1)
    
    try:
        if args.test_single:
            # Test single command
            print(f"Testing single command: {args.test_single}")
            tester.test_command(args.test_single, {"address": args.address})
        else:
            # Run all tests
            tester.run_all_tests()
        
        if args.save_report:
            tester.save_test_report()
        
    finally:
        tester.disconnect_serial()


if __name__ == "__main__":
    main()
