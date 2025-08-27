# PTZOptics Code Examples

A collection of code examples for controlling PTZOptics cameras programmatically using different protocols.

## 🚀 Quick Start

- **HTTP-CGI**: Web-based CGI commands over HTTP
- **VISCA over IP**: Sony VISCA protocol via TCP/IP

## 📚 Available Examples

### using-HTTP [[Python](./python/using-HTTP.py)] [[Node.js](./node/using-HTTP.js)]
Control PTZOptics cameras using HTTP-CGI commands
- HTTP-CGI interface with URL-based commands
- HTTP Digest Authentication support
- Automatic command cycling demo (5-second intervals)


### using-VISCA [[Python](./python/using-VISCA.py)] [[Node.js](./node/using-VISCA.js)]
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
