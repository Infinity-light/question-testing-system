# Quick Start Guide

## Installation

### Windows
```bash
cd question-testing-system
setup.bat
```

### Linux/Mac
```bash
cd question-testing-system
chmod +x setup.sh
./setup.sh
```

### Manual Setup
```bash
cd question-testing-system
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Edit `.env` file and add your Hunyuan API credentials:

```
HUNYUAN_API_KEY=your-actual-api-key-here
```

## Running the Application

```bash
python run.py
```

Then open your browser to: `http://localhost:5000`

## Usage Workflow

### 1. Add Questions
- Navigate to "添加问题" (Add Question)
- Fill in all required fields:
  - Title, question type, subject (math/physics/chemistry/etc.)
  - Difficulty level (高中/大学)
  - Knowledge points (comma-separated)
  - Question text (supports LaTeX: `$x^2 + y^2 = r^2$`)
  - Standard answer (≤40 chars for math, ≤50 for others)
  - Solution approach
- Click "创建问题" (Create Question)

### 2. Run Tests
- Go to "问题列表" (Question List)
- Click "测试" (Test) button for any question
- System will:
  - Call Hunyuan AI 8 times (stateless, independent calls)
  - Verify each answer using AI
  - Calculate success rate
  - Mark as qualified if success rate < 50%

### 3. View Results
- Navigate to "测试结果" (Test Results)
- View all test results with success rates
- Filter to show only qualified questions
- Click "详情" (Details) to see individual API call logs

### 4. Export to Excel
- In "测试结果" page:
  - Select specific results using checkboxes
  - Click "导出选中的结果" (Export Selected)
  - OR click "导出合格问题" (Export Qualified) for all qualified questions
- Excel file will be saved to `exports/` folder with 10-column format

## Features

### LaTeX Support
Use LaTeX syntax in question text:
- Inline math: `$E = mc^2$`
- Display math: `$$\int_0^1 x^2 dx$$`
- Fractions: `$\frac{a}{b}$`
- Greek letters: `$\alpha, \beta, \gamma$`

### Answer Length Validation
- Math questions: Maximum 40 characters
- Other subjects: Maximum 50 characters
- Real-time validation in the form

### Stateless Testing
Each of the 8 API calls is completely independent:
- No conversation history
- No session memory
- Temperature > 0 for varied responses
- Ensures diverse testing scenarios

### Qualification Criteria
A question is marked as "qualified" (合格) if:
- Success rate < 50% (less than 4 correct out of 8)
- This indicates the question is sufficiently difficult

## Excel Export Format

The exported Excel file contains 10 columns:

1. **标题** - Question title
2. **题目类型** - Question type
3. **领域** - Subject (math, physics, etc.)
4. **难度** - Difficulty level
5. **知识点** - Knowledge points
6. **问题** - Question text (with LaTeX)
7. **答案** - Standard answer
8. **解题思路** - Solution approach
9. **(Empty)** - Reserved column
10. **查难情况** - Difficulty status (e.g., "3/8")

## Troubleshooting

### API Connection Issues
- Verify `HUNYUAN_API_KEY` is set correctly in `.env`
- Check `HUNYUAN_BASE_URL` matches your API endpoint
- Ensure internet connection is stable

### Database Issues
- Delete `questions.db` and restart to reset database
- Check file permissions in project directory

### Port Already in Use
Edit `run.py` and change port:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 to 5001
```

## System Requirements

- Python 3.8 or higher
- Internet connection (for Hunyuan API)
- Modern web browser (Chrome, Firefox, Edge)
- Minimum 2GB RAM
- 500MB free disk space

## Support

For issues or questions:
1. Check the README.md file
2. Review error messages in terminal
3. Check Flask logs for detailed error information
