# Chat Keyword Batch Processor

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![Python](https://img.shields.io/badge/python-asyncio-orange.svg)
![AI](https://img.shields.io/badge/AI-HCX%20API-purple.svg)

🚀 **AI-powered chat data keyword classification and batch processing system**

A scalable, production-ready system for processing large volumes of chat data using AI-based keyword classification. Built with Python, supports multiple organizations, and provides comprehensive reporting capabilities.

## ✨ Key Features

- **🤖 AI-Powered Classification**: Intelligent keyword extraction using HCX API
- **🔄 Batch Processing**: Efficient large-scale data processing with parallel execution
- **📊 Automated Reporting**: Excel-based detailed analysis reports
- **📧 Email Notifications**: Automated completion alerts
- **🐳 Docker Support**: Containerized deployment for stability
- **⚙️ Configurable**: Environment-based flexible configuration
- **🏢 Multi-Organization**: Supports any organization's database schema
- **🚀 High Performance**: Async processing with intelligent rate limiting
- **🛡️ Error Recovery**: Automatic retry with exponential backoff

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, asyncio, SQLAlchemy
- **AI/ML**: HCX API for intelligent classification
- **Database**: MySQL, PostgreSQL, SQLite support
- **Infrastructure**: Docker, Docker Compose
- **Monitoring**: Structured logging, health checks
- **Reporting**: Pandas, OpenPyXL
- **CLI**: argparse-based command line interface

## 📁 Project Structure

```
chat-keyword-batch-processor/
├── 🎯 Main Entry Points
│   ├── cli.py                 # Unified CLI interface (main)
│   └── run.py                 # CLI wrapper
│
├── 🏗️ Core Modules
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database connection management
│   │   ├── exceptions.py      # Exception handling
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── batch_service.py   # Batch processing service
│   │   ├── hcx_service.py     # HCX API service
│   │   ├── excel_service.py   # Excel reporting service
│   │   ├── email_service.py   # Email notification service
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── date_utils.py      # Date utilities
│   │   ├── validation_utils.py # Data validation
│   │   ├── logger.py          # Logging utilities
│   │   └── __init__.py
│   │
│   └── queries/
│       └── batch_queries.py   # SQL query collection
│
├── 📊 Generated Folders
│   ├── reports/               # Excel reports
│   ├── logs/                  # Log files
│   └── temp/                  # Temporary files
│
└── 📖 Configuration & Docs
    ├── requirements.txt       # Python dependencies
    ├── docker-compose.yml     # Docker configuration
    ├── Dockerfile             # Docker image
    └── README.md              # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- MySQL/PostgreSQL database (or SQLite for development)
- HCX API key (for AI classification)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/chat-keyword-batch-processor.git
cd chat-keyword-batch-processor

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 3. Configuration

Create a `.env` file with your settings:

```bash
# Database Configuration
ENGINE_FOR_SQLALCHEMY=mysql+pymysql://user:password@host:port/database

# Database Schema (customizable)
DB_TABLE_CHATTINGS=chattings
DB_TABLE_CHAT_KEYWORDS=admin_chat_keywords
DB_TABLE_CATEGORIES=admin_categories
DB_COLUMN_INPUT_TEXT=input_text
DB_COLUMN_CHATTING_PK=chatting_pk
DB_COLUMN_CREATED_AT=created_at
DB_COLUMN_QUERY_TEXT=query_text
DB_COLUMN_KEYWORD=keyword
DB_COLUMN_CATEGORY_ID=category_id
DB_COLUMN_QUERY_COUNT=query_count
DB_COLUMN_BATCH_CREATED_AT=batch_created_at
DB_COLUMN_CATEGORY_NAME=category_name

# Organization Settings
ORG_NAME=MyOrganization
ORG_CODE=MYORG
ORG_TIMEZONE=Asia/Seoul
ORG_LANGUAGE=ko

# HCX API Configuration
HCX_CHAT_API_KEY=nv-your-api-key-here
HCX_MODEL=HCX-005
HCX_APP_TYPE=serviceapp

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@email.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAILS=admin@company.com,team@company.com
```

### 4. Basic Usage

```bash
# Validate configuration
python cli.py config validate

# Process yesterday's data
python cli.py batch --email

# Process specific date
python cli.py batch -d 2024-03-15 --email

# Process date range with parallel processing
python cli.py batch -s 2024-03-01 -e 2024-03-31 --parallel --email

# Generate report
python cli.py report -d yesterday --email

# Check system status
python cli.py status
```

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Execute commands in container
docker-compose exec batch-keywords python cli.py batch --email
docker-compose exec batch-keywords python cli.py status
```

### Docker Configuration

The system includes comprehensive Docker support with:
- Automated cron scheduling
- Health checks
- Log management
- Volume mounting for persistence

## 📋 Use Cases

### Educational Institutions
- Process student inquiry chat data
- Analyze frequently asked questions
- Generate educational insights reports

### Customer Service
- Analyze customer support conversations
- Identify common issues and trends
- Improve response quality

### Research Organizations
- Classify research survey responses
- Process qualitative data at scale
- Generate research insights

### Government Agencies
- Process public inquiry data
- Analyze citizen feedback
- Generate policy insights

### Any Organization
- Customizable for any chat data analysis needs
- Scalable architecture for large datasets
- Multi-tenant support

## ⚙️ Advanced Configuration

### Performance Tuning

```bash
# Parallel processing settings
PARALLEL_MAX_WORKERS=4
PARALLEL_CHUNK_SIZE=100
PARALLEL_CONCURRENT_DATES=3

# HCX API rate limiting
HCX_MAX_REQUESTS_PER_MINUTE=30
HCX_MIN_REQUEST_INTERVAL=1.0
HCX_BASE_DELAY=2.0

# Batch processing
BATCH_SIZE=25
CLASSIFICATION_BATCH_SIZE=5
BATCH_MAX_RETRY=3
```

### Database Optimization

```bash
# Connection pooling
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## 📈 Performance Features

- **Parallel Processing**: Multi-date and multi-chunk parallel execution
- **Rate Limiting**: Intelligent API request management
- **Error Recovery**: Automatic retry with exponential backoff
- **Memory Efficient**: Streaming data processing for large datasets
- **Async Operations**: Non-blocking I/O operations
- **Connection Pooling**: Efficient database connection management

## 🔧 CLI Commands

### Batch Processing
```bash
# Basic batch processing
python cli.py batch                    # Process yesterday
python cli.py batch -d 2024-03-15     # Process specific date
python cli.py batch -s 2024-03-01 -e 2024-03-31  # Process date range

# Advanced options
python cli.py batch --parallel --workers 8       # Parallel processing
python cli.py batch --email                      # Send email notification
python cli.py batch --dry-run                    # Test run without processing
```

### Missing Data Processing
```bash
# Check for missing data
python cli.py missing check -s 2024-03-01 -e 2024-03-31

# Process missing data
python cli.py missing process -s 2024-03-01 -e 2024-03-31 --email

# Auto process (check + process)
python cli.py missing auto -s 2024-03-01 -e 2024-03-31 --email
```

### Reporting
```bash
# Generate reports
python cli.py report -d yesterday --email
python cli.py report -s 2024-03-01 -e 2024-03-31
python cli.py report -d yesterday -o /path/to/report.xlsx
```

### System Management
```bash
# System status
python cli.py status

# Configuration
python cli.py config validate
python cli.py config show
```

## 🛡️ Error Handling

The system includes comprehensive error handling:
- **Automatic Retry**: Failed operations are retried with exponential backoff
- **Graceful Degradation**: System continues operation even if some components fail
- **Detailed Logging**: Comprehensive logging for debugging and monitoring
- **Email Alerts**: Automatic notification of critical errors
- **Health Checks**: Regular system health monitoring

## 📊 Monitoring & Logging

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Log Rotation**: Automatic log file rotation and cleanup
- **Performance Metrics**: Processing time, success rates, error counts
- **Health Checks**: System status monitoring
- **Email Notifications**: Processing completion and error alerts

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/chat-keyword-batch-processor.git
cd chat-keyword-batch-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 .
black .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 **Documentation**: Check the [docs/](docs/) folder
- 🐛 **Bug Reports**: [Create an issue](https://github.com/yourusername/chat-keyword-batch-processor/issues)
- 💬 **Discussions**: [Join discussions](https://github.com/yourusername/chat-keyword-batch-processor/discussions)
- 📧 **Email**: your-email@example.com

## 🙏 Acknowledgments

- HCX API for AI-powered classification
- SQLAlchemy for database abstraction
- Docker for containerization
- Open source community for various dependencies

---

⭐ **Star this repository if you find it useful!**

Made with ❤️ for the open source community.