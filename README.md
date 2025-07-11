# Bylaw Database - ADU Compliance Tool

A comprehensive tool for collecting, updating, storing, and managing bylaws related to Accessory Dwelling Units (ADUs) and building codes, with full source document preservation for liability protection.

## Overview

This tool consists of three main components:
1. **Resource Portal** - Front-end viewer for searching and viewing bylaws
2. **Configuration Manager** - Admin interface for managing data sources
3. **Scraping Engine** - Automated system for collecting and preserving bylaw data

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with TypeScript
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage for source documents
- **Scraping**: BeautifulSoup, Scrapy, Selenium

## Key Features

- Complete source document preservation for liability protection
- Full audit trail and version history
- Automated change detection and tracking
- Municipality-specific configuration
- ADU requirement extraction and standardization

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase account

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd bylaw-db
```

2. Set up backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up frontend
```bash
cd frontend
npm install
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

5. Run database migrations
```bash
cd database
# Apply migrations to Supabase
```

## Project Structure

```
bylaw-db/
├── backend/
│   ├── src/
│   │   ├── api/         # FastAPI endpoints
│   │   ├── scrapers/    # Web scraping modules
│   │   ├── models/      # Data models
│   │   ├── utils/       # Utility functions
│   │   └── storage/     # Document storage handlers
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   ├── utils/       # Utility functions
│   │   └── types/       # TypeScript types
│   └── public/
└── database/
    ├── migrations/      # SQL migrations
    └── schemas/         # Database schemas
```

## License

Proprietary - Borderless Inc.