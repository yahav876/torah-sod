# Torah Search Web Application

🔍 **Torah Search (tzfanim)** - A production-ready web application for searching Hebrew text in the Torah using various letter mapping techniques.

## 🌟 Features

- **Multi-user Web Interface** - Beautiful Hebrew/RTL responsive design
- **8 Letter Mapping Methods** - Advanced ABGD (אבג״ד) techniques for text analysis
- **Production Ready** - Flask + Gunicorn + Docker containerization
- **High Performance** - Multi-threaded search with Aho-Corasick algorithm
- **RESTful API** - JSON endpoints for integration
- **Real-time Search** - Fast parallel processing across Torah text
- **Health Monitoring** - Built-in health checks and monitoring

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yahav876/tzfanim.git
cd tzfanim

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8080
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app_web.py

# Or use the startup script
chmod +x start_server.sh
./start_server.sh dev
```

## 📖 What is Torah Search?

This application searches Hebrew text in the Torah using traditional Jewish letter mapping techniques known as **ABGD** (אבג״ד). These methods reveal hidden connections and patterns in the text by mapping letters according to various systematic approaches:

### Letter Mapping Methods

1. **Map 1**: Basic pair swapping (א↔ב, ג↔ד, etc.)
2. **Map 2**: Reverse alphabet mapping (א↔ת, ב↔ש, etc.)  
3. **Map 3**: Positional mapping
4. **Map 4**: Advanced positional mapping
5. **Map 5**: Group-based mapping (numerical values)
6. **Map 6**: Alternative group mapping
7. **Map 7**: Extended group mapping
8. **Map 8**: YHVH letter group (א,ה,ו,י)

## 🌐 API Usage

### Search Endpoint

**POST** `/api/search`

```json
{
  "phrase": "אלהים"
}
```

**Response:**
```json
{
  "input_phrase": "אלהים",
  "results": [
    {
      "variant": "אלהים",
      "sources": ["Original"],
      "locations": [
        {
          "book": "בראשית",
          "chapter": "א",
          "verse": "א", 
          "text": "בראשית ברא [אלהים] את השמים ואת הארץ"
        }
      ]
    }
  ],
  "total_variants": 15,
  "search_time": 0.234,
  "success": true
}
```

### Health Check

```bash
curl http://localhost:8080/health
```

## 🏗️ Architecture

- **Flask** - Web framework
- **Gunicorn** - WSGI server for production
- **Docker** - Containerization
- **Nginx** - Reverse proxy (optional)
- **Aho-Corasick** - Efficient string matching algorithm
- **ThreadPoolExecutor** - Parallel processing

## 📁 Project Structure

```
tzfanim/
├── app_web.py              # Main Flask application
├── wsgi.py                 # WSGI entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Multi-service setup
├── gunicorn.conf.py       # Production server config
├── start_server.sh        # Startup script
├── .env.example           # Environment template
└── torah.txt              # Torah text data
```

## ⚙️ Configuration

Create a `.env` file:

```bash
SECRET_KEY=your-secret-key-here
MAX_RESULTS=1000
CACHE_TIMEOUT=3600
MAX_WORKERS=8
FLASK_ENV=production
```

## 🔧 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start development server
python app_web.py
```

## 📈 Performance

- **Multi-threaded**: 8+ parallel workers
- **Efficient Search**: Aho-Corasick algorithm
- **Caching**: Torah text loaded once
- **Rate Limiting**: Protection against abuse
- **Health Checks**: Monitoring and alerting

## 🚀 Deployment

### Production with Docker

```bash
# Build and start
docker-compose up -d

# Scale for high traffic
docker-compose up --scale torah-search=3 -d

# View logs
docker-compose logs -f torah-search
```

### Cloud Platforms

- **Heroku**: Ready with `Procfile`
- **AWS ECS**: Use included Dockerfile
- **Google Cloud Run**: Deploy with container
- **Azure**: Container instances support

## 🔐 Security

- Rate limiting on API endpoints
- Input validation and sanitization
- Security headers (XSS, CSRF protection)
- Non-root container user
- Environment-based configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is provided for educational and research purposes.

## 🙏 Acknowledgments

- Torah text processing and analysis
- Hebrew language pattern recognition
- Traditional Jewish text study methods
- Open source community

---

**Built with ❤️ for Torah study and research**

🔗 **Repository**: https://github.com/yahav876/tzfanim
