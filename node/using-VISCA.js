#!/usr/bin/env node
/**
 * PTZOptics VISCA over IP Controller Example
 * 
 * This example demonstrates how to control PTZOptics cameras using VISCA commands
 * over IP. Commands are sent automatically every 5 seconds in a cycle.
 * 
 * Usage:
 *    node using-VISCA.js
 * 
 * Requirements:
 *    - Node.js 14+
 *    - PTZOptics camera on network
 *    - Camera IP address or hostname configured below
 */

const net = require('net');

// Configuration
const CAMERA_HOST = "192.168.1.100";  // Replace with your camera's IP address
const CAMERA_PORT = 5678;

class PTZOpticsVISCAController {
    constructor(host = "ptzoptics.local", port = 5678) {
        this.host = host;
        this.port = port;
        this.socket = null;
        this.running = false;
        this.commandIndex = 0;
        this.timerInterval = null;
        
        // VISCA Command List - Add or modify commands here
        this.viscaCommands = [
            // Pan Left (medium speed: pan=0x08, tilt=0x08)
            [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x01, 0x03, 0xFF],
            
            // Stop Pan/Tilt
            [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x03, 0xFF],
            
            // Pan Right (medium speed: pan=0x08, tilt=0x08)  
            [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x03, 0xFF],
            
            // Stop Pan/Tilt
            [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x03, 0xFF],
        ];
        
        // Command descriptions for logging
        this.commandDescriptions = [
            "Pan Left",
            "Stop Pan/Tilt",
            "Pan Right",
            "Stop Pan/Tilt"
        ];
    }
    
    connect() {
        /**Establish TCP connection to the PTZ camera*/
        return new Promise((resolve, reject) => {
            this.socket = new net.Socket();
            
            // Set timeout for connection
            this.socket.setTimeout(10000); // 10 second timeout
            
            // Handle successful connection
            this.socket.connect(this.port, this.host, () => {
                console.log(`✓ Connected to PTZ camera at ${this.host}:${this.port}`);
                this.socket.setTimeout(0); // Remove timeout after successful connection
                resolve(true);
            });
            
            // Handle connection errors
            this.socket.on('error', (error) => {
                console.log(`❌ Connection failed: ${error.message}`);
                reject(false);
            });
            
            // Handle timeout
            this.socket.on('timeout', () => {
                console.log(`❌ Connection timeout`);
                this.socket.destroy();
                reject(false);
            });
            
            // Handle unexpected close
            this.socket.on('close', () => {
                if (this.running) {
                    console.log("⚠️ Connection closed unexpectedly");
                    this.stop();
                }
            });
        });
    }
    
    disconnect() {
        /**Close the connection*/
        if (this.socket) {
            this.socket.destroy();
            this.socket = null;
            console.log("Connection closed");
        }
    }
    
    sendCommand(command) {
        /**Send a VISCA command and wait for response*/
        return new Promise((resolve) => {
            if (!this.socket || this.socket.destroyed) {
                console.log("❌ No connection available");
                resolve(false);
                return;
            }
            
            try {
                // Convert command to bytes and send
                const commandBuffer = Buffer.from(command);
                const hexString = Array.from(commandBuffer)
                    .map(b => b.toString(16).toUpperCase().padStart(2, '0'))
                    .join(' ');
                console.log(`   Hex: ${hexString}`);
                
                // Set up one-time response listener
                const responseHandler = (data) => {
                    const responseHex = Array.from(data)
                        .map(b => b.toString(16).toUpperCase().padStart(2, '0'))
                        .join(' ');
                    console.log(`   Response: ${responseHex}`);
                    this.interpretResponse(data);
                    resolve(true);
                };
                
                this.socket.once('data', responseHandler);
                
                // Send the command
                this.socket.write(commandBuffer);
                
                // Set timeout for response
                setTimeout(() => {
                    this.socket.removeListener('data', responseHandler);
                    resolve(true); // Consider it successful even without response
                }, 1000); // 1 second timeout for response
                
            } catch (error) {
                console.log(`❌ Send error: ${error.message}`);
                resolve(false);
            }
        });
    }
    
    interpretResponse(response) {
        /**Interpret VISCA response codes*/
        if (response.length < 3) {
            return;
        }
        
        if (response[0] === 0x90) {
            if (response[1] === 0x41) {  // ACK (camera address 1)
                console.log("   ✓ Command acknowledged");
            } else if (response[1] === 0x51) {  // Completion (camera address 1)
                console.log("   ✅ Command completed");
            } else if (response[1] === 0x60) {
                const errorCode = response[2];
                const errorMessages = {
                    0x02: "Syntax error",
                    0x03: "Command buffer full",
                    0x04: "Command cancelled",
                    0x05: "No socket",
                    0x41: "Command not executable"
                };
                const errorMsg = errorMessages[errorCode] || `Unknown error: ${errorCode.toString(16).toUpperCase().padStart(2, '0')}`;
                console.log(`   ❌ ${errorMsg}`);
            } else {
                console.log("   ⚠️ Unknown response type");
            }
        }
    }
    
    async sendNextCommand() {
        /**Send the next command in the cycle*/
        if (!this.viscaCommands || this.viscaCommands.length === 0) {
            console.log("⚠️ No commands in command list");
            return;
        }
        
        const command = this.viscaCommands[this.commandIndex];
        const description = (this.commandDescriptions[this.commandIndex] 
                          || `Command ${this.commandIndex + 1}`);
        
        console.log(`\n📤 Sending: ${description}`);
        await this.sendCommand(command);
        
        // Move to next command (cycle through the list)
        this.commandIndex = (this.commandIndex + 1) % this.viscaCommands.length;
    }
    
    async start() {
        /**Start the controller*/
        try {
            await this.connect();
            this.running = true;
            
            // Send first command immediately
            await this.sendNextCommand();
            
            // Then set up interval for subsequent commands
            this.timerInterval = setInterval(() => {
                if (this.socket && this.running) {
                    this.sendNextCommand();
                }
            }, 5000); // 5 second interval
            
            console.log("🕒 Started command timer (5 second intervals)");
            return true;
        } catch (error) {
            return false;
        }
    }
    
    stop() {
        /**Stop the controller*/
        this.running = false;
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        this.disconnect();
        console.log("⏹️ Controller stopped");
    }
    
    async sendSingleCommand(index) {
        /**Send a single command by index*/
        if (index >= 0 && index < this.viscaCommands.length) {
            const command = this.viscaCommands[index];
            const description = (this.commandDescriptions[index] 
                              || `Command ${index + 1}`);
            
            console.log(`\n📤 Manual send: ${description}`);
            await this.sendCommand(command);
        } else {
            console.log(`❌ Invalid command index: ${index}`);
        }
    }
}

// Global controller instance for signal handler
let controller;

function signalHandler() {
    /**Handle Ctrl+C gracefully*/
    console.log("\n\n🛑 Stopping PTZ Controller...");
    if (controller) {
        controller.stop();
    }
    process.exit(0);
}

async function main() {
    // Create controller instance
    controller = new PTZOpticsVISCAController(CAMERA_HOST, CAMERA_PORT);
    
    // Set up signal handlers for graceful shutdown
    process.on('SIGINT', signalHandler);
    process.on('SIGTERM', signalHandler);
    
    console.log("PTZOptics VISCA Controller Example");
    console.log("=".repeat(40));
    console.log(`Connecting to camera at: ${controller.host}`);
    console.log("Commands will be sent every 5 seconds");
    console.log("Press Ctrl+C to stop\n");
    
    // Start the controller
    if (await controller.start()) {
        // Keep the program running
        // Node.js will keep running as long as the interval is active
    } else {
        console.log("Failed to start controller");
        process.exit(1);
    }
}

// Run the main function
main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});

/*
HOW TO ADD MORE COMMANDS:

1. Add command byte arrays to the 'viscaCommands' array
2. Add corresponding descriptions to 'commandDescriptions' array

Example commands from the PTZOptics VISCA documentation:

Pan/Tilt Commands:
- Pan Right:     [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x03, 0xFF]
- Tilt Up:       [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x01, 0xFF]
- Tilt Down:     [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x03, 0x02, 0xFF]
- Up-Left:       [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x01, 0x01, 0xFF]
- Up-Right:      [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x01, 0xFF]
- Down-Left:     [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x01, 0x02, 0xFF]
- Down-Right:    [0x81, 0x01, 0x06, 0x01, 0x08, 0x08, 0x02, 0x02, 0xFF]
- Home Position: [0x81, 0x01, 0x06, 0x04, 0xFF]
- Reset:         [0x81, 0x01, 0x06, 0x05, 0xFF]

Speed Parameters:
- Pan speed: 0x01 (slow) to 0x18 (fast)
- Tilt speed: 0x01 (slow) to 0x14 (fast)
- Medium speed: 0x08 (commonly used)

Preset Commands:
- Save Preset 1:   [0x81, 0x01, 0x04, 0x3F, 0x01, 0x01, 0xFF]
- Recall Preset 1: [0x81, 0x01, 0x04, 0x3F, 0x02, 0x01, 0xFF]

Configuration:
- Change camera IP in the configuration constants
- Modify the 5-second interval in start()
- Add error handling or logging as needed

Note: VISCA uses TCP port 5678 by default for IP control.
*/
