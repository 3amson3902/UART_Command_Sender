#!/usr/bin/env python3
"""
Plugin System for UART Command Sender
Base classes and plugin manager for extending functionality
"""

import os
import sys
import importlib.util
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import json


class UARTPlugin(ABC):
    """Base class for UART plugins"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
    
    @abstractmethod
    def get_commands(self) -> Dict[str, Any]:
        """Return a dictionary of available commands for this plugin"""
        pass
    
    @abstractmethod
    def process_command(self, command: str, parameters: Dict[str, Any]) -> bytes:
        """Process a command and return the bytes to send"""
        pass
    
    @abstractmethod
    def parse_response(self, data: bytes) -> Dict[str, Any]:
        """Parse received data and return interpreted results"""
        pass
    
    def get_info(self) -> Dict[str, str]:
        """Get plugin information"""
        return {
            "name": self.name,
            "description": self.description,
            "enabled": str(self.enabled)
        }
    
    def validate_parameters(self, command: str, parameters: Dict[str, Any]) -> bool:
        """Validate command parameters (override in subclass if needed)"""
        return True


class PluginManager:
    """Manager for loading and handling plugins"""
    
    def __init__(self, plugin_directory: str = "plugins"):
        self.plugin_directory = plugin_directory
        self.plugins: Dict[str, UARTPlugin] = {}
        self.callbacks: Dict[str, Callable] = {}
        
        # Ensure plugin directory exists
        os.makedirs(plugin_directory, exist_ok=True)
        
    def set_callback(self, event: str, callback: Callable):
        """Set callback for plugin events"""
        self.callbacks[event] = callback
    
    def _notify(self, event: str, *args, **kwargs):
        """Notify callback of event"""
        if event in self.callbacks:
            self.callbacks[event](*args, **kwargs)
    
    def load_plugins(self):
        """Load all plugins from the plugin directory"""
        if not os.path.exists(self.plugin_directory):
            return
        
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                self.load_plugin(filename[:-3])  # Remove .py extension
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin"""
        try:
            plugin_path = os.path.join(self.plugin_directory, f"{plugin_name}.py")
            if not os.path.exists(plugin_path):
                return False
            
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec is None or spec.loader is None:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class (should be named Plugin)
            if hasattr(module, 'Plugin'):
                plugin_class = getattr(module, 'Plugin')
                plugin_instance = plugin_class()
                
                if isinstance(plugin_instance, UARTPlugin):
                    self.plugins[plugin_name] = plugin_instance
                    self._notify("plugin_loaded", plugin_name, plugin_instance)
                    return True
            
            return False
            
        except Exception as e:
            self._notify("plugin_error", f"Failed to load plugin {plugin_name}: {str(e)}")
            return False
    
    def unload_plugin(self, plugin_name: str):
        """Unload a plugin"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            self._notify("plugin_unloaded", plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[UARTPlugin]:
        """Get a specific plugin"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, UARTPlugin]:
        """Get all loaded plugins"""
        return self.plugins.copy()
    
    def get_enabled_plugins(self) -> Dict[str, UARTPlugin]:
        """Get all enabled plugins"""
        return {name: plugin for name, plugin in self.plugins.items() if plugin.enabled}
    
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
    
    def get_commands_for_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Get commands for a specific plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin and plugin.enabled:
            return plugin.get_commands()
        return {}
    
    def execute_plugin_command(self, plugin_name: str, command: str, parameters: Dict[str, Any]) -> Optional[bytes]:
        """Execute a command using a specific plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin and plugin.enabled:
            try:
                if plugin.validate_parameters(command, parameters):
                    return plugin.process_command(command, parameters)
            except Exception as e:
                self._notify("plugin_error", f"Error executing {plugin_name}.{command}: {str(e)}")
        return None
    
    def parse_response_with_plugin(self, plugin_name: str, data: bytes) -> Optional[Dict[str, Any]]:
        """Parse response using a specific plugin"""
        plugin = self.get_plugin(plugin_name)
        if plugin and plugin.enabled:
            try:
                return plugin.parse_response(data)
            except Exception as e:
                self._notify("plugin_error", f"Error parsing response with {plugin_name}: {str(e)}")
        return None


class ChecksumCalculator:
    """Utility class for calculating different types of checksums"""
    
    @staticmethod
    def xor_checksum(data: bytes) -> int:
        """Calculate XOR checksum"""
        result = 0
        for byte in data:
            result ^= byte
        return result
    
    @staticmethod
    def crc8_checksum(data: bytes, poly: int = 0x07) -> int:
        """Calculate CRC-8 checksum"""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ poly
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc
    
    @staticmethod
    def fixed_checksum(value: int = 0x6B) -> int:
        """Return fixed checksum value"""
        return value


def create_plugin_template(plugin_name: str, output_path: str):
    """Create a template plugin file"""
    template = f'''#!/usr/bin/env python3
"""
{plugin_name} Plugin for UART Command Sender
Auto-generated plugin template
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin_system import UARTPlugin, ChecksumCalculator
from typing import Dict, Any


class Plugin(UARTPlugin):
    """Plugin for {plugin_name}"""
    
    def __init__(self):
        super().__init__(
            name="{plugin_name}",
            description="Custom plugin for {plugin_name} device communication"
        )
    
    def get_commands(self) -> Dict[str, Any]:
        """Return available commands for this plugin"""
        return {{
            "example_command": {{
                "description": "Example command",
                "parameters": {{
                    "param1": {{"type": "int", "min": 0, "max": 255, "default": 1}},
                    "param2": {{"type": "str", "default": "test"}}
                }}
            }}
        }}
    
    def process_command(self, command: str, parameters: Dict[str, Any]) -> bytes:
        """Process command and return bytes to send"""
        if command == "example_command":
            # Example: create a simple command format
            addr = parameters.get("param1", 1)
            data = parameters.get("param2", "test").encode()
            
            # Build command: [addr] [data] [checksum]
            cmd_bytes = bytes([addr]) + data
            checksum = ChecksumCalculator.xor_checksum(cmd_bytes)
            
            return cmd_bytes + bytes([checksum])
        
        raise ValueError(f"Unknown command: {{command}}")
    
    def parse_response(self, data: bytes) -> Dict[str, Any]:
        """Parse received data"""
        if len(data) < 3:
            return {{"error": "Response too short"}}
        
        return {{
            "raw_data": data.hex(),
            "length": len(data),
            "parsed": True
        }}
    
    def validate_parameters(self, command: str, parameters: Dict[str, Any]) -> bool:
        """Validate command parameters"""
        if command == "example_command":
            param1 = parameters.get("param1", 1)
            if not isinstance(param1, int) or param1 < 0 or param1 > 255:
                return False
        
        return True
'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)
