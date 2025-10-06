# MA-MPD (Multi-Agent Malicious Package Detection) (WIP: Work In Progress)

A multi-agent system for detecting and classifying malicious Python packages using AI-powered analysis.

## 🔍 Overview

MA-MPD leverages multiple AI agents to analyze Python packages and classify them as malicious or benign. The system examines package metadata, file contents, and suspicious patterns to provide comprehensive security assessments.

## ✨ Features

- **Multi-Agent Architecture**: Coordinated AI agents for package analysis
- **Automated Classification**: Intelligent detection of malicious patterns
- **Metadata Extraction**: Comprehensive package information gathering
- **RESTful API**: Easy integration via FastAPI endpoints
- **Database Storage**: PostgreSQL-backed result persistence
- **Docker Support**: Containerized deployment ready

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- OpenAI API key (or compatible LLM endpoint)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MA-MPD
```

2. Install dependencies using `uv`:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

4. Run database migrations:
```bash
python src/databaseSetup/run_migrations.py
python src/databaseSetup/insert_initial_prompts.py
```

### Running the API

**Local Development:**
```bash
uvicorn api.classify:app --reload
```

**Docker:**
```bash
docker-compose up
```

## 📡 API Usage

### Classify a Package

**Upload a file:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -F "upload_file=@package.tar.gz" \
  -F "dataset_id=your-dataset-id"
```

**Analyze a folder:**
```bash
curl -X POST "http://localhost:8000/classify" \
  -F "folder_path=/path/to/package" \
  -F "dataset_id=your-dataset-id"
```

### Get Classification Result

```bash
curl "http://localhost:8000/classification/{classification_id}/result"
```

### List All Results

```bash
curl "http://localhost:8000/classification-results"
```

## 🏗️ Architecture

- **RootAgent**: Orchestrates the analysis workflow
- **MetaDataAgent**: Extracts package metadata
- **ClassificationAgent**: Performs malicious pattern detection
- **ClassifyPackagesAgents**: Coordinates package-level analysis

## 📝 Configuration

Edit `config.ini` to customize:
- Model selection (GPT-4, custom endpoints)
- Database table names
- Service names
- Fallback models

## 🧪 Development

Run tests:
```bash
pytest
```

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.
