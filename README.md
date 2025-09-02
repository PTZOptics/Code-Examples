# PTZOptics Code Examples

A collection of code examples for controlling PTZOptics cameras programmatically using different protocols.

## 🚀 Quick Start

- **HTTP-CGI**: Web-based CGI commands over HTTP
- **VISCA over IP**: Sony VISCA protocol via TCP/IP
- **Motion Detection**: RTSP feed motion detector in Python

## 📚 Available Examples

### HTTP API [[Python](./HTTP API/python/example-http.py)] [[Node.js](./HTTP API/node/example-http.js)]
Control PTZOptics cameras using HTTP-CGI commands
- HTTP-CGI interface with URL-based commands
- HTTP Digest Authentication support
- Automatic command cycling demo (5-second intervals)


### VISCA API [[Python](./VISCA API/python/example-visca.py)] [[Node.js](./VISCA API/node/example-visca.js)]
Control PTZOptics cameras using VISCA protocol over IP
- Direct VISCA protocol implementation
- TCP socket communication (default port 5678)
- Byte-level command control with response interpretation
- Automatic command cycling demo (5-second intervals)


### Motion Detection [[](./VISCA API/python/example-visca.py)]
Control PTZOptics cameras using VISCA protocol over IP
- Direct VISCA protocol implementation
- TCP socket communication (default port 5678)
- Byte-level command control with response interpretation
- Automatic command cycling demo (5-second intervals)


## 📚 Resources

- **[PTZOptics Developer Portal](https://ptzoptics.com/developer-portal)** - Complete API documentation, command references, and developer resources
- **[PTZOptics Support](https://ptzoptics.com/contact/)** - Technical support and FAQs


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
