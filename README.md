# AI Question Testing System

A web-based system for data annotation and quality testing of professional domain questions using Hunyuan AI API.

## Features

- **Question Input Interface**: Web form for contributors to input questions with LaTeX support
- **AI Testing System**: Automated testing with 8 stateless API calls per question
- **Answer Verification**: AI-powered verification of correctness
- **Qualification System**: Questions with success rate < 50% are marked as qualified
- **Excel Export**: Export results in standardized 10-column format

## Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL/SQLite
- **Frontend**: Bootstrap 5, MathJax (LaTeX rendering)
- **AI Integration**: OpenAI Python SDK (Hunyuan API)
- **Export**: openpyxl

## Installation

1. Clone the repository:
```bash
cd question-testing-system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your Hunyuan API key
```

5. Initialize database:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Configuration

Edit `.env` file with your settings:

```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

DATABASE_URL=sqlite:///questions.db

HUNYUAN_API_KEY=your-api-key-here
HUNYUAN_BASE_URL=https://api.hunyuan.cloud.tencent.com/v1
HUNYUAN_MODEL=hunyuan-turbos-latest

TEST_ATTEMPTS=8
QUALIFICATION_THRESHOLD=50
MAX_ANSWER_LENGTH_MATH=40
MAX_ANSWER_LENGTH_OTHER=50
```

## Usage

1. Start the application:
```bash
python run.py
```

2. Open browser and navigate to `http://localhost:5000`

3. Add questions via the web interface

4. Run tests on questions (8 stateless API attempts per question)

5. View test results and export qualified questions to Excel

## Project Structure

```
question-testing-system/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration
│   ├── models.py                # Database models
│   ├── routes/
│   │   ├── question_routes.py  # Question CRUD
│   │   └── testing_routes.py   # Testing & export
│   ├── services/
│   │   ├── hunyuan_service.py  # API integration
│   │   ├── testing_service.py  # Testing logic
│   │   └── export_service.py   # Excel export
│   ├── templates/               # HTML templates
│   └── static/                  # CSS/JS files
├── exports/                     # Generated Excel files
├── requirements.txt
├── run.py                       # Application entry point
└── README.md
```

## Database Schema

### Questions Table
- Basic info: title, type, subject, difficulty
- Content: question_text (LaTeX), standard_answer, solution_approach
- Metadata: knowledge_points, timestamps

### Test Results Table
- Test metrics: correct_count, success_rate, qualified status
- Difficulty status: "X/8" format

### API Call Logs Table
- Individual attempt details
- AI answers and verification responses
- Error tracking

## API Integration

The system uses stateless API calls to ensure varied responses:
- Each call is independent (no conversation history)
- Temperature > 0 for response variation
- 0.5s delay between calls for rate limiting
- Automatic retry with exponential backoff

## Excel Export Format

10-column format:
1. 标题 (Title)
2. 题目类型 (Question Type)
3. 领域 (Subject)
4. 难度 (Difficulty)
5. 知识点 (Knowledge Points)
6. 问题 (Question Text)
7. 答案 (Standard Answer)
8. 解题思路 (Solution Approach)
9. (Empty Column)
10. 查难情况 (Difficulty Status: X/8)

## License

MIT License
