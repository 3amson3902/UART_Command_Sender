#!/usr/bin/env python3
"""
Emm42 V5.0 Stepper Motor Plugin
Plugin for Emm42_V5.0 closed-loop stepper motor driver communication
Supports 485/CAN bus communication with various checksum methods
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin_system import UARTPlugin, ChecksumCalculator
from typing import Dict, Any, Union


class Plugin(UARTPlugin):
    """Plugin for Emm42 V5.0 stepper motor driver"""
    
    def __init__(self):
        super().__init__(
            name="Emm42_V5.0",
            description="Emm42 V5.0 closed-loop stepper motor driver communication plugin"
        )
        
        # Checksum types supported
        self.checksum_types = {
            "fixed_0x6B": 0x6B,
            "xor": "xor",
            "crc8": "crc8"        }
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands for Emm42 V5.0 based on official specification"""
        return {
            # 6.3.1 Control Action Commands
            "motor_enable": {
                "description": "Motor enable control (0xF3)",
                "func_code": 0xF3,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "enable": {"type": "choice", "choices": ["Disable", "Enable"], "default": "Enable"},
                    "sync": {"type": "choice", "choices": ["No", "Yes"], "default": "No"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "speed_mode": {
                "description": "Speed mode control (0xF6)",
                "func_code": 0xF6,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "direction": {"type": "choice", "choices": ["CW", "CCW"], "default": "CW"},
                    "speed": {"type": "int", "min": 0, "max": 65535, "default": 100, "description": "Speed in RPM"},
                    "acceleration": {"type": "int", "min": 0, "max": 255, "default": 10, "description": "Acceleration level (0=no curve)"},
                    "sync": {"type": "choice", "choices": ["No", "Yes"], "default": "No"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "position_mode": {
                "description": "Position mode control (0xFD)",
                "func_code": 0xFD,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "direction": {"type": "choice", "choices": ["CW", "CCW"], "default": "CW"},
                    "speed": {"type": "int", "min": 0, "max": 65535, "default": 100, "description": "Speed in RPM"},
                    "acceleration": {"type": "int", "min": 0, "max": 255, "default": 10, "description": "Acceleration level"},
                    "pulses": {"type": "int", "min": 0, "max": 4294967295, "default": 3200, "description": "Number of pulses"},
                    "mode": {"type": "choice", "choices": ["Relative", "Absolute"], "default": "Relative"},
                    "sync": {"type": "choice", "choices": ["No", "Yes"], "default": "No"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "immediate_stop": {
                "description": "Immediate stop (0xFE)",
                "func_code": 0xFE,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "sync": {"type": "choice", "choices": ["No", "Yes"], "default": "No"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "sync_motion": {
                "description": "Multi-motor sync motion (0xFF)",
                "func_code": 0xFF,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            
            # 6.3.2 Homing Commands
            "set_zero_position": {
                "description": "Set single-turn zero position (0x93)",
                "func_code": 0x93,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "Yes"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "trigger_homing": {
                "description": "Trigger homing (0x9A)",
                "func_code": 0x9A,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "mode": {"type": "choice", "choices": ["Nearest", "Direction", "Multi-collision", "Multi-limit"], "default": "Nearest"},
                    "sync": {"type": "choice", "choices": ["No", "Yes"], "default": "No"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "stop_homing": {
                "description": "Force stop homing (0x9C)",
                "func_code": 0x9C,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            
            # 6.3.3 Trigger Action Commands  
            "calibrate_encoder": {
                "description": "Trigger encoder calibration (0x06)",
                "func_code": 0x06,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "clear_position": {
                "description": "Clear current position to zero (0x0A)",
                "func_code": 0x0A,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "clear_stall_protection": {
                "description": "Clear stall protection (0x0E)",
                "func_code": 0x0E,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "factory_reset": {
                "description": "Factory reset (0x0F)",
                "func_code": 0x0F,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            
            # 6.3.4 Read Parameter Commands
            "read_firmware_version": {
                "description": "Read firmware and hardware version (0x1F)",
                "func_code": 0x1F,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_motor_params": {
                "description": "Read motor resistance and inductance (0x20)",
                "func_code": 0x20,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_pid_params": {
                "description": "Read position PID parameters (0x21)",
                "func_code": 0x21,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_homing_params": {
                "description": "Read homing parameters (0x22)",
                "func_code": 0x22,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_bus_voltage": {
                "description": "Read bus voltage (0x24)",
                "func_code": 0x24,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_phase_current": {
                "description": "Read phase current (0x27)",
                "func_code": 0x27,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_encoder_value": {
                "description": "Read calibrated encoder value (0x31)",
                "func_code": 0x31,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_input_pulses": {
                "description": "Read input pulses (0x32)",
                "func_code": 0x32,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_target_position": {
                "description": "Read motor target position (0x33)",
                "func_code": 0x33,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_realtime_target": {
                "description": "Read realtime target position (0x34)",
                "func_code": 0x34,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_realtime_speed": {
                "description": "Read realtime motor speed (0x35)",
                "func_code": 0x35,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_realtime_position": {
                "description": "Read realtime motor position (0x36)",
                "func_code": 0x36,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_position_error": {
                "description": "Read motor position error (0x37)",
                "func_code": 0x37,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_motor_status": {
                "description": "Read motor status flags (0x3A)",
                "func_code": 0x3A,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_homing_status": {
                "description": "Read homing status flags (0x3B)",
                "func_code": 0x3B,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_drive_config": {
                "description": "Read driver configuration (0x42)",
                "func_code": 0x42,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "read_system_status": {
                "description": "Read system status (0x43)",
                "func_code": 0x43,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            
            # 6.3.5 Modify Parameter Commands
            "modify_subdivision": {
                "description": "Modify subdivision (0x84)",
                "func_code": 0x84,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "Yes"},
                    "subdivision": {"type": "int", "min": 1, "max": 256, "default": 16, "description": "Subdivision (0=256)"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "modify_id_address": {
                "description": "Modify ID address (0xAE)",
                "func_code": 0xAE,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "Yes"},
                    "new_id": {"type": "int", "min": 1, "max": 255, "default": 2},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "switch_open_closed_loop": {
                "description": "Switch open/closed loop mode (0x46)",
                "func_code": 0x46,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "Yes"},
                    "mode": {"type": "choice", "choices": ["Open Loop", "Closed Loop"], "default": "Closed Loop"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },            "modify_open_loop_current": {
                "description": "Modify open loop current (0x44)",
                "func_code": 0x44,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "No"},
                    "current": {"type": "int", "min": 0, "max": 65535, "default": 1000, "description": "Current in mA"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "modify_homing_params": {
                "description": "Modify homing parameters (0x4C)",
                "func_code": 0x4C,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "Yes"},
                    "mode": {"type": "choice", "choices": ["Nearest", "Direction", "Multi-collision", "Multi-limit"], "default": "Nearest"},
                    "direction": {"type": "choice", "choices": ["CW", "CCW"], "default": "CW"},
                    "speed": {"type": "int", "min": 0, "max": 65535, "default": 30, "description": "Homing speed in RPM"},
                    "timeout": {"type": "int", "min": 0, "max": 4294967295, "default": 10000, "description": "Timeout in ms"},
                    "collision_speed": {"type": "int", "min": 0, "max": 65535, "default": 300, "description": "Speed for collision detection"},
                    "collision_current": {"type": "int", "min": 0, "max": 65535, "default": 800, "description": "Current for collision detection"},
                    "collision_time": {"type": "int", "min": 0, "max": 65535, "default": 60, "description": "Collision detection time"},
                    "auto_homing": {"type": "choice", "choices": ["Disable", "Enable"], "default": "Disable"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "store_speed_params": {
                "description": "Store speed mode parameters for auto-run (0xF7)",
                "func_code": 0xF7,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "operation": {"type": "choice", "choices": ["Clear", "Store"], "default": "Store"},
                    "direction": {"type": "choice", "choices": ["CW", "CCW"], "default": "CW"},
                    "speed": {"type": "int", "min": 0, "max": 65535, "default": 100, "description": "Speed in RPM"},
                    "acceleration": {"type": "int", "min": 0, "max": 255, "default": 10, "description": "Acceleration level"},
                    "en_control": {"type": "choice", "choices": ["Disable", "Enable"], "default": "Disable"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            "modify_speed_scale": {
                "description": "Modify communication speed input scale (0x4F)",
                "func_code": 0x4F,
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "save": {"type": "choice", "choices": ["No", "Yes"], "default": "Yes"},
                    "scale_enable": {"type": "choice", "choices": ["Disable", "Enable"], "default": "Disable"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            },
            
            # Custom command for any manual command
            "custom_command": {
                "description": "Send custom command with manual data",
                "parameters": {
                    "address": {"type": "int", "min": 0, "max": 255, "default": 1},
                    "func_code": {"type": "int", "min": 0, "max": 255, "default": 0x06, "description": "Function code in hex"},
                    "data": {"type": "str", "default": "", "description": "Hex data (e.g., '00 01 02')"},
                    "checksum_type": {"type": "choice", "choices": list(self.checksum_types.keys()), "default": "fixed_0x6B"}
                }
            }
        }
    
    def _int32_to_bytes(self, value: int) -> list:
        """Convert 32-bit signed integer to bytes (little-endian)"""
        if value < 0:
            value = (1 << 32) + value  # Convert to unsigned
        return [
            value & 0xFF,
            (value >> 8) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 24) & 0xFF
        ]
    
    def _int16_to_bytes(self, value: int) -> list:
        """Convert 16-bit integer to bytes (little-endian)"""
        return [
            value & 0xFF,
            (value >> 8) & 0xFF
        ]
    
    def _calculate_checksum(self, data: bytes, checksum_type: str) -> int:
        """Calculate checksum based on type"""
        if checksum_type == "fixed_0x6B":
            return 0x6B
        elif checksum_type == "xor":
            return ChecksumCalculator.xor_checksum(data)
        elif checksum_type == "crc8":
            return ChecksumCalculator.crc8_checksum(data)
        else:
            return 0x6B  # Default fallback
    
    def process_command(self, command: str, parameters: Dict[str, Any]) -> bytes:
        """Process command and return bytes to send according to official specification"""
        commands = self.get_commands()
        if command not in commands:
            raise ValueError(f"Unknown command: {command}")
        
        cmd_info = commands[command]
        address = parameters.get("address", 1)
        checksum_type = parameters.get("checksum_type", "fixed_0x6B")
        
        # Build command based on official specification
        if command == "custom_command":
            func_code = parameters.get("func_code", 0x06)
            data_str = parameters.get("data", "")
            
            # Parse hex data string
            data_bytes = []
            if data_str:
                hex_parts = data_str.replace(",", " ").split()
                for part in hex_parts:
                    try:
                        data_bytes.append(int(part, 16))
                    except ValueError:
                        raise ValueError(f"Invalid hex data: {part}")
            
            cmd_bytes = bytes([address, func_code] + data_bytes)
        
        elif command == "motor_enable":
            # Format: Address + 0xF3 + 0xAB + Enable_State + Sync_Flag + Checksum
            enable = 1 if parameters.get("enable", "Enable") == "Enable" else 0
            sync = 1 if parameters.get("sync", "No") == "Yes" else 0
            cmd_bytes = bytes([address, 0xF3, 0xAB, enable, sync])
        
        elif command == "speed_mode":
            # Format: Address + 0xF6 + Direction + Speed + Acceleration + Sync_Flag + Checksum
            direction = 1 if parameters.get("direction", "CW") == "CCW" else 0
            speed = parameters.get("speed", 100)
            acceleration = parameters.get("acceleration", 10)
            sync = 1 if parameters.get("sync", "No") == "Yes" else 0
            speed_bytes = self._int16_to_bytes(speed)
            cmd_bytes = bytes([address, 0xF6, direction] + speed_bytes + [acceleration, sync])
        
        elif command == "position_mode":
            # Format: Address + 0xFD + Direction + Speed + Acceleration + Pulses + Mode + Sync_Flag + Checksum
            direction = 1 if parameters.get("direction", "CW") == "CCW" else 0
            speed = parameters.get("speed", 100)
            acceleration = parameters.get("acceleration", 10)
            pulses = parameters.get("pulses", 3200)
            mode = 1 if parameters.get("mode", "Relative") == "Absolute" else 0
            sync = 1 if parameters.get("sync", "No") == "Yes" else 0
            speed_bytes = self._int16_to_bytes(speed)
            pulse_bytes = self._int32_to_bytes(pulses)
            cmd_bytes = bytes([address, 0xFD, direction] + speed_bytes + [acceleration] + pulse_bytes + [mode, sync])
        
        elif command == "immediate_stop":
            # Format: Address + 0xFE + 0x98 + Sync_Flag + Checksum
            sync = 1 if parameters.get("sync", "No") == "Yes" else 0
            cmd_bytes = bytes([address, 0xFE, 0x98, sync])
        
        elif command == "sync_motion":
            # Format: Address + 0xFF + 0x66 + Checksum
            cmd_bytes = bytes([address, 0xFF, 0x66])
        
        elif command == "set_zero_position":
            # Format: Address + 0x93 + 0x88 + Save_Flag + Checksum
            save = 1 if parameters.get("save", "Yes") == "Yes" else 0
            cmd_bytes = bytes([address, 0x93, 0x88, save])
        
        elif command == "trigger_homing":
            # Format: Address + 0x9A + Homing_Mode + Sync_Flag + Checksum
            mode_map = {"Nearest": 0, "Direction": 1, "Multi-collision": 2, "Multi-limit": 3}
            mode = mode_map.get(parameters.get("mode", "Nearest"), 0)
            sync = 1 if parameters.get("sync", "No") == "Yes" else 0
            cmd_bytes = bytes([address, 0x9A, mode, sync])
        
        elif command == "stop_homing":
            # Format: Address + 0x9C + 0x48 + Checksum
            cmd_bytes = bytes([address, 0x9C, 0x48])
        
        elif command == "calibrate_encoder":
            # Format: Address + 0x06 + 0x45 + Checksum
            cmd_bytes = bytes([address, 0x06, 0x45])
        
        elif command == "clear_position":
            # Format: Address + 0x0A + 0x6D + Checksum
            cmd_bytes = bytes([address, 0x0A, 0x6D])
        
        elif command == "clear_stall_protection":
            # Format: Address + 0x0E + 0x52 + Checksum
            cmd_bytes = bytes([address, 0x0E, 0x52])
        
        elif command == "factory_reset":
            # Format: Address + 0x0F + 0x5F + Checksum
            cmd_bytes = bytes([address, 0x0F, 0x5F])
        
        elif command == "modify_subdivision":
            # Format: Address + 0x84 + 0x8A + Save_Flag + Subdivision + Checksum
            save = 1 if parameters.get("save", "Yes") == "Yes" else 0
            subdivision = parameters.get("subdivision", 16)
            if subdivision == 256:
                subdivision = 0  # 256 subdivision is represented as 0
            cmd_bytes = bytes([address, 0x84, 0x8A, save, subdivision])
        
        elif command == "modify_id_address":
            # Format: Address + 0xAE + 0x4B + Save_Flag + New_ID + Checksum
            save = 1 if parameters.get("save", "Yes") == "Yes" else 0
            new_id = parameters.get("new_id", 2)
            cmd_bytes = bytes([address, 0xAE, 0x4B, save, new_id])
        
        elif command == "switch_open_closed_loop":
            # Format: Address + 0x46 + 0x69 + Save_Flag + Mode + Checksum
            save = 1 if parameters.get("save", "Yes") == "Yes" else 0
            mode = 1 if parameters.get("mode", "Closed Loop") == "Open Loop" else 2
            cmd_bytes = bytes([address, 0x46, 0x69, save, mode])
        
        elif command == "modify_open_loop_current":
            # Format: Address + 0x44 + 0x33 + Save_Flag + Current + Checksum
            save = 1 if parameters.get("save", "No") == "Yes" else 0
            current = parameters.get("current", 1000)
            current_bytes = self._int16_to_bytes(current)
            cmd_bytes = bytes([address, 0x44, 0x33, save] + current_bytes)
        
        elif command == "modify_homing_params":
            # Format: Address + 0x4C + 0xAE + Save_Flag + Params...
            save = 1 if parameters.get("save", "Yes") == "Yes" else 0
            mode_map = {"Nearest": 0, "Direction": 1, "Multi-collision": 2, "Multi-limit": 3}
            mode = mode_map.get(parameters.get("mode", "Nearest"), 0)
            direction = 1 if parameters.get("direction", "CW") == "CCW" else 0
            speed = parameters.get("speed", 30)
            timeout = parameters.get("timeout", 10000)
            collision_speed = parameters.get("collision_speed", 300)
            collision_current = parameters.get("collision_current", 800)
            collision_time = parameters.get("collision_time", 60)
            auto_homing = 1 if parameters.get("auto_homing", "Disable") == "Enable" else 0
            
            speed_bytes = self._int16_to_bytes(speed)
            timeout_bytes = self._int32_to_bytes(timeout)
            collision_speed_bytes = self._int16_to_bytes(collision_speed)
            collision_current_bytes = self._int16_to_bytes(collision_current)
            collision_time_bytes = self._int16_to_bytes(collision_time)
            
            cmd_bytes = bytes([address, 0x4C, 0xAE, save, mode, direction] + 
                            speed_bytes + timeout_bytes + collision_speed_bytes + 
                            collision_current_bytes + collision_time_bytes + [auto_homing])
        
        elif command == "store_speed_params":
            # Format: Address + 0xF7 + 0x1C + Operation + Direction + Speed + Acceleration + En_Control + Checksum
            operation = 1 if parameters.get("operation", "Store") == "Store" else 0
            direction = 1 if parameters.get("direction", "CW") == "CCW" else 0
            speed = parameters.get("speed", 100)
            acceleration = parameters.get("acceleration", 10)
            en_control = 1 if parameters.get("en_control", "Disable") == "Enable" else 0
            
            speed_bytes = self._int16_to_bytes(speed)
            cmd_bytes = bytes([address, 0xF7, 0x1C, operation, direction] + speed_bytes + [acceleration, en_control])
        
        elif command == "modify_speed_scale":
            # Format: Address + 0x4F + 0x71 + Save_Flag + Scale_Enable + Checksum
            save = 1 if parameters.get("save", "Yes") == "Yes" else 0
            scale_enable = 1 if parameters.get("scale_enable", "Disable") == "Enable" else 0
            cmd_bytes = bytes([address, 0x4F, 0x71, save, scale_enable])
        
        elif command.startswith("read_"):
            # Simple read commands: Address + Function_Code + Checksum
            func_code = cmd_info["func_code"]
            if command == "read_drive_config":
                cmd_bytes = bytes([address, func_code, 0x6C])
            elif command == "read_system_status":
                cmd_bytes = bytes([address, func_code, 0x7A])
            else:
                cmd_bytes = bytes([address, func_code])
        
        else:
            raise ValueError(f"Command processing not implemented for: {command}")
        
        # Add checksum
        checksum = self._calculate_checksum(cmd_bytes, checksum_type)
        cmd_bytes += bytes([checksum])
        
        return cmd_bytes
    
    def parse_response(self, data: bytes) -> Dict[str, Any]:
        """Parse received data from Emm42 V5.0"""
        if len(data) < 3:
            return {
                "error": "Response too short",
                "raw_data": data.hex().upper(),
                "length": len(data)
            }
        
        result = {
            "raw_data": ' '.join([f'{b:02X}' for b in data]),
            "length": len(data),
            "address": data[0],
            "func_code": data[1],
            "checksum": data[-1]
        }
        
        # Parse based on function code
        func_code = data[1]
        payload = data[2:-1]  # Data between func_code and checksum
        
        if func_code == 0x31:  # Read position response
            if len(payload) >= 4:
                position = int.from_bytes(payload[:4], byteorder='little', signed=True)
                result["position"] = position
                result["description"] = f"Current position: {position} steps"
        
        elif func_code == 0x32:  # Read speed response
            if len(payload) >= 3:
                direction = "CCW" if payload[0] == 1 else "CW"
                speed = int.from_bytes(payload[1:3], byteorder='little')
                result["direction"] = direction
                result["speed"] = speed
                result["description"] = f"Speed: {speed} rpm, Direction: {direction}"
        
        elif func_code == 0x33:  # Read status response
            if len(payload) >= 1:
                status = payload[0]
                status_bits = {
                    "motor_enabled": bool(status & 0x01),
                    "motor_running": bool(status & 0x02),
                    "motor_direction": "CCW" if (status & 0x04) else "CW",
                    "position_reached": bool(status & 0x08),
                    "error_occurred": bool(status & 0x10)
                }
                result["status"] = status
                result["status_bits"] = status_bits
                result["description"] = f"Status: 0x{status:02X}"
        
        elif func_code == 0x06:  # Stop motor response
            result["description"] = "Motor stop command acknowledged"
        
        elif func_code == 0x0A:  # Reset position response
            result["description"] = "Position reset command acknowledged"
        
        else:
            result["description"] = f"Response to function code 0x{func_code:02X}"
        
        # Verify checksum if possible
        if len(data) >= 3:
            data_without_checksum = data[:-1]
            
            # Try different checksum methods
            checksums = {
                "fixed_0x6B": 0x6B,
                "xor": ChecksumCalculator.xor_checksum(data_without_checksum),
                "crc8": ChecksumCalculator.crc8_checksum(data_without_checksum)
            }
            
            received_checksum = data[-1]
            valid_checksums = []
            
            for method, calculated in checksums.items():
                if calculated == received_checksum:
                    valid_checksums.append(method)
            
            result["checksum_valid"] = len(valid_checksums) > 0
            result["possible_checksum_methods"] = valid_checksums
        
        return result
    
    def response_to_human_readable(self, data: bytes) -> str:
        """Convert a raw response to a human-readable string according to the Emm42 V5.0 protocol."""
        if len(data) < 3:
            return f"[Error] Response too short: {data.hex().upper()}"
        addr = data[0]
        func = data[1]
        payload = data[2:-1]
        checksum = data[-1]
        # Error/acknowledge patterns
        if func == 0x00 and len(data) == 4 and data[2] == 0xEE:
            return f"[Error] Invalid command. Address: {addr}"
        if len(data) == 4 and data[2] == 0xE2:
            return f"[Error] Condition not met for command 0x{func:02X} (e.g. stall, not enabled). Address: {addr}"
        if len(data) == 4 and data[2] == 0x02:
            return f"[OK] Command 0x{func:02X} executed successfully. Address: {addr}"
        # Command-specific parsing
        if func == 0x31 and len(payload) == 2:
            value = int.from_bytes(payload, 'big')
            return f"[Encoder] Calibrated encoder value: {value} (0-65535, 1 turn)"
        if func == 0x32 and len(payload) == 5:
            sign = '-' if payload[0] == 1 else '+'
            pulses = int.from_bytes(payload[1:], 'big', signed=False)
            return f"[Input Pulses] {sign}{pulses} pulses"
        if func == 0x33 and len(payload) == 5:
            sign = '-' if payload[0] == 1 else '+'
            pos = int.from_bytes(payload[1:], 'big', signed=False)
            deg = (pos * 360) / 65536
            return f"[Target Position] {sign}{pos} ({deg:.2f}°)"
        if func == 0x34 and len(payload) == 5:
            sign = '-' if payload[0] == 1 else '+'
            pos = int.from_bytes(payload[1:], 'big', signed=False)
            deg = (pos * 360) / 65536
            return f"[Realtime Target] {sign}{pos} ({deg:.2f}°)"
        if func == 0x35 and len(payload) == 3:
            sign = '-' if payload[0] == 1 else '+'
            speed = int.from_bytes(payload[1:], 'big', signed=False)
            return f"[Realtime Speed] {sign}{speed} RPM"
        if func == 0x36 and len(payload) == 5:
            sign = '-' if payload[0] == 1 else '+'
            pos = int.from_bytes(payload[1:], 'big', signed=False)
            deg = (pos * 360) / 65536
            return f"[Realtime Position] {sign}{pos} ({deg:.2f}°)"
        if func == 0x37 and len(payload) == 5:
            sign = '-' if payload[0] == 1 else '+'
            err = int.from_bytes(payload[1:], 'big', signed=False)
            deg = (err * 360) / 65536
            return f"[Position Error] {sign}{err} ({deg:.5f}°)"
        if func == 0x3A and len(payload) == 1:
            status = payload[0]
            bits = [
                (status & 0x01, "Enabled"),
                (status & 0x02, "In Position"),
                (status & 0x04, "Stall"),
                (status & 0x08, "Stall Protection")
            ]
            flags = ', '.join([desc for bit, desc in bits if bit])
            return f"[Motor Status] Flags: {flags or 'None'} (0x{status:02X})"
        if func == 0x3B and len(payload) == 1:
            status = payload[0]
            bits = [
                (status & 0x01, "Encoder Ready"),
                (status & 0x02, "Table Ready"),
                (status & 0x04, "Homing"),
                (status & 0x08, "Homing Failed")
            ]
            flags = ', '.join([desc for bit, desc in bits if bit])
            return f"[Homing Status] Flags: {flags or 'None'} (0x{status:02X})"
        if func == 0x1F and len(payload) == 2:
            fw, hw = payload
            return f"[Version] Firmware: 0x{fw:02X}, Hardware: 0x{hw:02X}"
        if func == 0x20 and len(payload) == 4:
            res = int.from_bytes(payload[:2], 'big')
            ind = int.from_bytes(payload[2:], 'big')
            return f"[Motor Params] Resistance: {res} mΩ, Inductance: {ind} uH"
        if func == 0x21 and len(payload) == 12:
            kp = int.from_bytes(payload[0:4], 'big')
            ki = int.from_bytes(payload[4:8], 'big')
            kd = int.from_bytes(payload[8:12], 'big')
            return f"[PID] Kp: {kp}, Ki: {ki}, Kd: {kd}"
        if func == 0x24 and len(payload) == 2:
            voltage = int.from_bytes(payload, 'big')
            return f"[Bus Voltage] {voltage} mV"
        if func == 0x27 and len(payload) == 2:
            current = int.from_bytes(payload, 'big')
            return f"[Phase Current] {current} mA"
        if func == 0x42 and len(payload) > 0:
            return f"[Driver Config] Raw: {' '.join(f'{b:02X}' for b in payload)}"
        if func == 0x43 and len(payload) > 0:
            return f"[System Status] Raw: {' '.join(f'{b:02X}' for b in payload)}"
        # Default fallback
        return f"[Raw] Addr: {addr}, Func: 0x{func:02X}, Payload: {' '.join(f'{b:02X}' for b in payload)}, Checksum: 0x{checksum:02X}"
    
    def validate_parameters(self, command: str, parameters: Dict[str, Any]) -> bool:
        """Validate command parameters"""
        commands = self.get_commands()
        if command not in commands:
            return False
        
        cmd_params = commands[command].get("parameters", {})
        
        for param_name, param_config in cmd_params.items():
            if param_name in parameters:
                value = parameters[param_name]
                param_type = param_config.get("type", "str")
                
                if param_type == "int":
                    if not isinstance(value, int):
                        return False
                    if "min" in param_config and value < param_config["min"]:
                        return False
                    if "max" in param_config and value > param_config["max"]:
                        return False
                
                elif param_type == "choice":
                    if value not in param_config.get("choices", []):
                        return False
        
        return True
