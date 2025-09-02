# PTZOptics Code Examples

A collection of code examples for controlling PTZOptics cameras programmatically using different protocols.

## 🚀 Quick Start

- **HTTP-CGI**: Web-based CGI commands over HTTP
- **VISCA over IP**: Sony VISCA protocol via TCP/IP
- **Motion Detection**: RTSP feed motion detector in Python

## 📚 Available Examples

### HTTP API [Python](./HTTP%20API/python/example-http.py) [Node.js](./HTTP%20API/node/example-http.js)
Control PTZOptics cameras using HTTP-CGI commands
- HTTP-CGI interface with URL-based commands
- HTTP Digest Authentication support
- Automatic command cycling demo (5-second intervals)


### VISCA API [Python](./VISCA%20API/python/example-visca.py) [Node.js](./VISCA%20API/node/example-visca.js)
Control PTZOptics cameras using VISCA protocol over IP
- Direct VISCA protocol implementation
- TCP socket communication (default port 5678)
- Byte-level command control with response interpretation
- Automatic command cycling demo (5-second intervals)


### Motion Detection [main.py](./Motion%20Detection/main.py)
View when motion is detected in an RTSP feed with OpenCV

## 📚 Resources

- **[PTZOptics Developer Portal](https://ptzoptics.com/developer-portal)** - Complete API documentation, command references, and developer resources
- **[PTZOptics Support](https://ptzoptics.com/contact/)** - Technical support and FAQs


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
