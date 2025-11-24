# Contributing to Orbis Ethica

Thank you for your interest in contributing to Orbis Ethica! We are building a moral operating system for AGI, and your help is vital.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct (standard Contributor Covenant). Please be respectful and constructive.

## How to Contribute

### 1. Reporting Bugs
- Check the [Issues](https://github.com/Yehielamor/orbis-ethica/issues) tab to see if the bug has already been reported.
- Open a new issue with a clear title and description.
- Include steps to reproduce, expected behavior, and actual behavior.

### 2. Suggesting Enhancements
- Open a new issue with the "enhancement" label.
- Describe the feature you'd like to see and why it's important.

### 3. Pull Requests
1. **Fork the repository** and create your branch from `main`.
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/orbis-ethica.git
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Make your changes**. Ensure you follow the coding style (PEP 8 for Python).
5. **Run tests**:
   ```bash
   python -m backend.cli.main test
   pytest
   ```
6. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "feat: Add amazing feature"
   ```
7. **Push to your fork**:
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request** targeting the `main` branch.

## Development Setup

1. Install Python 3.11+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Copy `.env.example` to `.env` (if available) or create one.
   - Add `GEMINI_API_KEY` for live LLM features.

## Project Structure

- `backend/`: Core Python logic (Entities, Deliberation Engine).
- `docs/`: Documentation.
- `tests/`: Test suite.

## License

By contributing, you agree that your contributions will be licensed under the project's [CC BY-SA 4.0 License](LICENSE).
