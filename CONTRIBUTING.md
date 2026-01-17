# Contributing to Fiscaliza

Thank you for your interest in contributing to Fiscaliza! This document provides guidelines and instructions for contributing to the Portuguese Parliament data analysis platform.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Data Import Guidelines](#data-import-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/parliament.git
   cd parliament
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/rfsbraz/parliament.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL (for production-like development) or SQLite (for quick local development)
- Git

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

4. Generate a secure SECRET_KEY:
   ```bash
   python -c 'import secrets; print(secrets.token_hex(32))'
   ```
   Add this to your `.env` file.

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the frontend:
   ```bash
   npm run build
   ```

4. For development with hot reload:
   ```bash
   npm run dev
   ```

### Running the Application

Start the Flask backend:
```bash
python main.py
```

The application will be available at `http://localhost:5000`.

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes** - Fix issues in existing code
- **New features** - Add new functionality
- **Documentation** - Improve or add documentation
- **Tests** - Add or improve test coverage
- **Data importers** - Create new data import pipelines
- **Translations** - Add Portuguese translations or improve English docs
- **Performance improvements** - Optimize existing code

### Before You Start

1. Check if an issue already exists for your contribution
2. If not, create an issue to discuss your proposed changes
3. Wait for feedback before starting major work
4. Keep pull requests focused on a single issue

## Coding Standards

### Python Code

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Add docstrings to all functions, classes, and modules

**Code Formatting:**
```bash
# Format code with black
black .

# Check linting
flake8 .
```

### JavaScript/React Code

- Use ES6+ syntax
- Follow React best practices
- Use functional components and hooks
- Use meaningful component and variable names
- Keep components small and focused

**Code Formatting:**
```bash
cd frontend
npm run lint
npm run format
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**Examples:**
```
feat(api): add endpoint for deputy voting records
fix(import): correct date parsing for legislature data
docs(readme): add environment variable documentation
test(mappers): add tests for boolean value conversion
```

## Data Import Guidelines

### Core Principles

When working on data import scripts, follow these critical principles from CLAUDE.md:

1. **Data Accuracy is Paramount**
   - Map XML to SQL directly unless instructed otherwise
   - Never generate artificial data or provide defaults
   - Use only data that matches the source exactly

2. **Explicit Field Mapping**

   **NEVER** use cascading `or` fallback patterns:
   ```python
   # WRONG - Anti-pattern
   dep_nome = (
       self._get_text_value(data_element, "DepNomeParlamentar")
       or self._get_text_value(data_element, "depNomeParlamentar")
       or self._get_text_value(data_element, "depNome")
   )
   ```

   **ALWAYS** use explicit field mapping:
   ```python
   # CORRECT - Clear data provenance
   dep_nome_parlamentar = self._get_text_value(data_element, "DepNomeParlamentar")
   dep_nome_completo = self._get_text_value(data_element, "DepNomeCompleto")
   ```

3. **Document Everything**
   - Document understanding of each field
   - Update documentation when gaining new knowledge
   - Add comments explaining data transformations

4. **Import Process**
   - Check for existing models before creating new ones
   - Create related models and relations as needed
   - Import, process, and store every property
   - Design unified data model across all legislative periods

## Testing

### Running Tests

Run all tests:
```bash
python run_tests.py
```

Run specific test file:
```bash
python -m pytest tests/test_date_parsing.py -v
```

### Writing Tests

- Write tests for all new functionality
- Aim for at least 80% code coverage
- Use descriptive test names
- Include both positive and negative test cases
- Test edge cases and error handling

**Example:**
```python
import unittest

class TestDataMapper(unittest.TestCase):
    def test_parse_valid_date(self):
        """Test parsing of valid date format"""
        result = parse_date("2024-01-15")
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_parse_invalid_date_raises_error(self):
        """Test that invalid date raises ValueError"""
        with self.assertRaises(ValueError):
            parse_date("invalid-date")
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, documented code
   - Add or update tests as needed
   - Update documentation if necessary

3. **Test your changes:**
   ```bash
   python run_tests.py
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**
   - Go to the GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template
   - Link related issues

### Pull Request Guidelines

- Provide a clear description of changes
- Include screenshots for UI changes
- Reference related issues (e.g., "Fixes #123")
- Ensure all tests pass
- Update documentation as needed
- Keep PRs focused and reasonably sized
- Respond to review feedback promptly

### PR Review Process

1. Automated checks must pass (tests, linting)
2. At least one maintainer review required
3. Address all review comments
4. Maintainer will merge when approved

## Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported
2. Verify the bug exists in the latest version
3. Collect relevant information

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Browser (if applicable): [e.g., Chrome 120]

**Additional context**
Add any other context, logs, or screenshots.
```

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature has already been requested
2. Clearly describe the feature and its benefits
3. Explain the use case
4. Be open to discussion and feedback

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context, screenshots, or examples.
```

## Questions?

If you have questions about contributing:

- Open a GitHub issue with the "question" label
- Check existing documentation in the `/docs` directory
- Review CLAUDE.md for technical architecture details

## License

By contributing to Fiscaliza, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions help make government data more accessible and transparent. Thank you for being part of this project!
