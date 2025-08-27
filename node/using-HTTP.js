#!/usr/bin/env node
/**
 * PTZOptics HTTP-CGI API Controller Example
 * 
 * This example demonstrates how to control PTZOptics cameras using HTTP-CGI commands.
 * Implements HTTP Digest Authentication (SHA-256) natively using Node.js built-in modules.
 * 
 * Usage:
 *    node using-HTTP.js
 */

const http = require('http');
const crypto = require('crypto');

// Configuration Constants
const CAMERA_HOST = "192.168.1.100";
const CAMERA_USERNAME = "admin";
const CAMERA_PASSWORD = "admin";

class PTZOpticsHTTPController {
    constructor(host = "ptzoptics.local", username = "admin", password = "admin") {
        this.host = host;
        this.username = username;
        this.password = password;
        this.running = false;
        this.commandIndex = 0;
        this.timerInterval = null;
        
        // HTTP-CGI Command List
        this.cgiCommands = [
            "/cgi-bin/ptzctrl.cgi?ptzcmd&left&12&10",
            "/cgi-bin/ptzctrl.cgi?ptzcmd&ptzstop&0&0", 
            "/cgi-bin/ptzctrl.cgi?ptzcmd&right&12&10",
        ];
        
        // Command descriptions
        this.commandDescriptions = [
            "Pan Left (Speed 12/10)",
            "Stop Pan/Tilt",
            "Pan Right (Speed 12/10)",
        ];
    }
    
    makeRequest(path) {
        return new Promise((resolve, reject) => {
            const options = {
                hostname: this.host,
                port: 80,
                path: path,
                method: 'GET',
                headers: {
                    'Accept': '*/*'
                }
            };
            
            const req = http.request(options, (res) => {
                let data = '';
                
                res.on('data', chunk => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    if (res.statusCode === 401 && res.headers['www-authenticate']) {
                        // Need to handle digest auth
                        const authHeader = res.headers['www-authenticate'];
                        const digestResponse = this.createDigestResponse(authHeader, path);
                        
                        // Make authenticated request
                        const authOptions = {
                            ...options,
                            headers: {
                                ...options.headers,
                                'Authorization': digestResponse
                            }
                        };
                        
                        const authReq = http.request(authOptions, (authRes) => {
                            let authData = '';
                            authRes.on('data', chunk => {
                                authData += chunk;
                            });
                            authRes.on('end', () => {
                                resolve({ 
                                    statusCode: authRes.statusCode, 
                                    data: authData,
                                    headers: authRes.headers 
                                });
                            });
                        });
                        
                        authReq.on('error', reject);
                        authReq.end();
                        
                    } else {
                        resolve({ 
                            statusCode: res.statusCode, 
                            data: data,
                            headers: res.headers 
                        });
                    }
                });
            });
            
            req.on('error', reject);
            req.end();
        });
    }
    
    createDigestResponse(authHeader, uri) {
        // Parse WWW-Authenticate header
        const params = {};
        authHeader.replace('Digest ', '').split(',').forEach(param => {
            const [key, value] = param.trim().split('=');
            params[key] = value ? value.replace(/"/g, '') : '';
        });
        
        const realm = params.realm || '';
        const nonce = params.nonce || '';
        const qop = params.qop || '';
        const algorithm = params.algorithm || 'MD5';
        
        // Generate client nonce
        const cnonce = crypto.randomBytes(8).toString('hex');
        const nc = '00000001';
        
        // Calculate digest
        let ha1, ha2, response;
        
        if (algorithm === 'SHA-256') {
            const hash = crypto.createHash('sha256');
            hash.update(`${this.username}:${realm}:${this.password}`);
            ha1 = hash.digest('hex');
            
            const hash2 = crypto.createHash('sha256');
            hash2.update(`GET:${uri}`);
            ha2 = hash2.digest('hex');
            
            const hash3 = crypto.createHash('sha256');
            if (qop === 'auth') {
                hash3.update(`${ha1}:${nonce}:${nc}:${cnonce}:${qop}:${ha2}`);
            } else {
                hash3.update(`${ha1}:${nonce}:${ha2}`);
            }
            response = hash3.digest('hex');
        } else {
            // MD5
            const hash = crypto.createHash('md5');
            hash.update(`${this.username}:${realm}:${this.password}`);
            ha1 = hash.digest('hex');
            
            const hash2 = crypto.createHash('md5');
            hash2.update(`GET:${uri}`);
            ha2 = hash2.digest('hex');
            
            const hash3 = crypto.createHash('md5');
            if (qop === 'auth') {
                hash3.update(`${ha1}:${nonce}:${nc}:${cnonce}:${qop}:${ha2}`);
            } else {
                hash3.update(`${ha1}:${nonce}:${ha2}`);
            }
            response = hash3.digest('hex');
        }
        
        // Build Authorization header
        let authStr = `Digest username="${this.username}", realm="${realm}", nonce="${nonce}", uri="${uri}"`;
        if (qop) {
            authStr += `, cnonce="${cnonce}", nc=${nc}, qop=${qop}`;
        }
        authStr += `, response="${response}", algorithm=${algorithm}`;
        
        return authStr;
    }
    
    async testConnection() {
        try {
            console.log(`Testing connection to: http://${this.host}/cgi-bin/ptzctrl.cgi?ptzcmd&ptzstop&0&0`);
            const result = await this.makeRequest('/cgi-bin/ptzctrl.cgi?ptzcmd&ptzstop&0&0');
            
            console.log(`Response status: ${result.statusCode}`);
            if (result.statusCode === 200) {
                console.log(`✓ Connected to PTZ camera at ${this.host}`);
                return true;
            } else {
                console.log(`❌ Connection failed - HTTP ${result.statusCode}`);
                console.log(`Response: ${result.data.substring(0, 200)}`);
                return false;
            }
        } catch (error) {
            console.log(`❌ Connection error: ${error.message}`);
            return false;
        }
    }
    
    async sendCommand(path) {
        try {
            console.log(`   URL: ${path}`);
            const result = await this.makeRequest(path);
            
            if (result.statusCode === 200) {
                console.log(`   ✅ Command successful (HTTP ${result.statusCode})`);
                if (result.data.trim()) {
                    const firstLine = result.data.trim().split('\n')[0].substring(0, 100);
                    console.log(`   Response: ${firstLine}`);
                }
                return true;
            } else {
                console.log(`   ❌ Command failed (HTTP ${result.statusCode})`);
                return false;
            }
        } catch (error) {
            console.log(`   ❌ Request error: ${error.message}`);
            return false;
        }
    }
    
    async sendNextCommand() {
        if (!this.cgiCommands || this.cgiCommands.length === 0) {
            console.log("⚠️ No commands in command list");
            return;
        }
        
        const command = this.cgiCommands[this.commandIndex];
        const description = this.commandDescriptions[this.commandIndex] || `Command ${this.commandIndex + 1}`;
        
        console.log(`\n📤 Sending: ${description}`);
        await this.sendCommand(command);
        
        this.commandIndex = (this.commandIndex + 1) % this.cgiCommands.length;
    }
    
    async start() {
        if (await this.testConnection()) {
            this.running = true;
            
            await this.sendNextCommand();
            
            this.timerInterval = setInterval(() => {
                if (this.running) {
                    this.sendNextCommand();
                }
            }, 5000);
            
            console.log("🕒 Started command timer (5 second intervals)");
            return true;
        }
        return false;
    }
    
    stop() {
        this.running = false;
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        console.log("⏹️ Controller stopped");
    }
}

let controller;

function signalHandler() {
    console.log("\n\n🛑 Stopping PTZ Controller...");
    if (controller) {
        controller.stop();
    }
    process.exit(0);
}

async function main() {
    controller = new PTZOpticsHTTPController(CAMERA_HOST, CAMERA_USERNAME, CAMERA_PASSWORD);
    
    process.on('SIGINT', signalHandler);
    process.on('SIGTERM', signalHandler);
    
    console.log("PTZOptics HTTP-CGI Controller Example");
    console.log("=".repeat(40));
    console.log(`Connecting to camera at: ${controller.host}`);
    console.log("Commands will be sent every 5 seconds");
    console.log("Press Ctrl+C to stop\n");
    
    if (await controller.start()) {
        // Keep running
    } else {
        console.log("Failed to start controller");
        process.exit(1);
    }
}

main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
});
