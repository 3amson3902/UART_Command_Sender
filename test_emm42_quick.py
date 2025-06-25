#!/usr/bin/env python3
"""
Quick Test Script for Emm42 V5.0 Plugin
Simple verification that the plugin works correctly
"""

import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_plugin():
    """Test the emm42_v5 plugin basic functionality"""
    
    try:
        # Import the plugin
        from plugins.emm42_v5 import Plugin as Emm42Plugin
        print("✓ Plugin imported successfully")
        
        # Create plugin instance
        plugin = Emm42Plugin()
        print(f"✓ Plugin created: {plugin.name}")
        
        # Test getting commands
        commands = plugin.get_commands()
        print(f"✓ Plugin has {len(commands)} commands")
        
        # Test a simple command
        params = {"address": 1, "enable": "Enable", "sync": "No"}
        cmd_bytes = plugin.process_command("motor_enable", params)
        hex_output = ' '.join([f'{b:02X}' for b in cmd_bytes])
        print(f"✓ Motor enable command: {hex_output}")
        
        # Test response parsing
        mock_response = bytes([0x01, 0xF3, 0x02, 0x6B])
        parsed = plugin.parse_response(mock_response)
        print(f"✓ Response parsed: {parsed.get('description', 'OK')}")
        
        # Test human readable response if available
        if hasattr(plugin, 'response_to_human_readable'):
            human = plugin.response_to_human_readable(mock_response)
            print(f"✓ Human readable: {human}")
        
        print("\n✓ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def show_available_commands():
    """Show all available commands in the plugin"""
    
    try:
        from plugins.emm42_v5 import Plugin as Emm42Plugin
        plugin = Emm42Plugin()
        commands = plugin.get_commands()
        
        print(f"\nEmm42 V5.0 Plugin - Available Commands ({len(commands)} total):")
        print("=" * 60)
        
        categories = {
            "Control": ["motor_enable", "speed_mode", "position_mode", "immediate_stop", "sync_motion"],
            "Homing": ["set_zero_position", "trigger_homing", "stop_homing"],
            "Read": [cmd for cmd in commands.keys() if cmd.startswith("read_")],
            "Modify": [cmd for cmd in commands.keys() if cmd.startswith("modify_") or cmd.startswith("switch_") or cmd.startswith("store_")],
            "Utility": ["calibrate_encoder", "clear_position", "clear_stall_protection", "factory_reset"],
            "Custom": ["custom_command"]
        }
        
        for category, cmd_list in categories.items():
            existing_commands = [cmd for cmd in cmd_list if cmd in commands]
            if existing_commands:
                print(f"\n{category} Commands ({len(existing_commands)}):")
                for cmd in existing_commands:
                    desc = commands[cmd].get('description', 'No description')
                    print(f"  {cmd:<25} - {desc}")
        
    except Exception as e:
        print(f"Error: {e}")


def test_specific_commands():
    """Test specific command examples"""
    
    try:
        from plugins.emm42_v5 import Plugin as Emm42Plugin
        plugin = Emm42Plugin()
        
        print("\nTesting Specific Commands:")
        print("=" * 40)
        
        test_cases = [
            ("motor_enable", {"address": 1, "enable": "Enable"}),
            ("speed_mode", {"address": 1, "speed": 100, "direction": "CW"}),
            ("read_motor_status", {"address": 1}),
            ("read_firmware_version", {"address": 1}),
            ("calibrate_encoder", {"address": 1}),
        ]
        
        for command, params in test_cases:
            try:
                cmd_bytes = plugin.process_command(command, params)
                hex_str = ' '.join([f'{b:02X}' for b in cmd_bytes])
                print(f"✓ {command:<20}: {hex_str}")
            except Exception as e:
                print(f"✗ {command:<20}: Error - {e}")
        
    except Exception as e:
        print(f"Error in specific tests: {e}")


def test_response_parsing():
    """Test response parsing with example responses"""
    
    try:
        from plugins.emm42_v5 import Plugin as Emm42Plugin
        plugin = Emm42Plugin()
        
        print("\nTesting Response Parsing:")
        print("=" * 40)
        
        test_responses = [
            (bytes([0x01, 0xF3, 0x02, 0x6B]), "Success response"),
            (bytes([0x01, 0x3A, 0x03, 0x6B]), "Motor status"),
            (bytes([0x01, 0x31, 0x1A, 0x2B, 0x6B]), "Encoder value"),
            (bytes([0x01, 0x1F, 0x20, 0x15, 0x6B]), "Firmware version"),
            (bytes([0x01]), "Short response (error)"),
        ]
        
        for response_bytes, description in test_responses:
            hex_str = ' '.join([f'{b:02X}' for b in response_bytes])
            print(f"\nResponse: {hex_str} ({description})")
            
            try:
                parsed = plugin.parse_response(response_bytes)
                print(f"  Parsed: {parsed.get('description', 'No description')}")
                
                if hasattr(plugin, 'response_to_human_readable'):
                    human = plugin.response_to_human_readable(response_bytes)
                    print(f"  Human:  {human}")
                    
            except Exception as e:
                print(f"  Error: {e}")
        
    except Exception as e:
        print(f"Error in response tests: {e}")


def main():
    """Main function"""
    print("Emm42 V5.0 Plugin Test Script")
    print("=" * 40)
    
    # Basic functionality test
    if not test_plugin():
        print("Basic tests failed. Exiting.")
        return
    
    # Show available commands
    show_available_commands()
    
    # Test specific commands
    test_specific_commands()
    
    # Test response parsing
    test_response_parsing()
    
    print("\n" + "=" * 40)
    print("Test script completed!")


if __name__ == "__main__":
    main()
