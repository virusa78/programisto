# Programisto

Your coding companion for web development. Programisto is a Python-based assistant that helps developers build and maintain web projects with context-aware assistance.

## Features

- **Project Scanning**: Automatically scans your project directory to understand structure and context
- **LLM Integration**: Connects to OpenAI-compatible APIs for intelligent responses
- **CLI Interface**: Interactive command-line assistant
- **Foil Generation**: Generates code patterns and templates for common web development tasks
- **Engineering Harness**: Creates development tools and best practices
- **Log Analyzer**: Scans and interprets log files
- **Skill Catalog**: Index of coding skills with LLM-based recommendations
- **Multi-Agent Support**: Configures multiple AI coding CLI tools
- **Admin Commands**: Manage skills, tools, and projects

## Installation

```bash
# Clone or copy the programisto directory
cd programisto

# Make the main script executable
chmod +x programisto.py

# Install dependencies
pip install pyyaml
```

## Quick Start

```bash
# Show help
./programisto.py help

# Scan your project
./programisto.py scan

# Start interactive chat
./programisto.py chat

# Answer a single question
./programisto.py chat --query "How do I add a new React component?"

# Generate code foils
./programisto.py foil

# Generate engineering harness
./programisto.py harness

# Analyze log files
./programisto.py log
```

## Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `help` | Show help message |
| `scan` | Scan the project directory |
| `chat` | Start interactive assistant mode |
| `foil` | Generate code foils/patterns |
| `harness` | Generate engineering harness tools |
| `log` | Analyze log files |
| `skills` | Manage skills |
| `tools` | Manage CLI tool configurations |
| `validate` | Validate project setup |

### Admin Commands

| Command | Description |
|---------|-------------|
| `admin add-skill-repo <url>` | Add a skill repository |
| `admin add-cli <name>` | Register a CLI tool |
| `admin new-project <name>` | Create a new project |
| `admin list-skills` | List available skills |
| `admin list-tools` | List configured tools |
| `admin validate` | Validate project setup |

## Configuration

### Environment Variables

```bash
export OPENAI_API_KEY=your-api-key
```

### Configuration File

Edit `programisto-config.yaml` to customize settings:

```yaml
# Project directory
project_dir: "./my-project"

# LLM settings
llm:
  enabled: true
  api_key: "your-key"
  base_url: "https://api.openai.com/v1"
  model: "claude-3-sonnet-20240229"
  timeout: 120

# CLI tool settings
tools:
  claude-code:
    enabled: true
    skills_dir: "~/.claude/skills"
```

## Usage Examples

### Interactive Mode

```bash
./programisto.py chat

> help
> scan
> How do I set up TypeScript?
> Generate a React component
> Show me the log analysis
> exit
```

### Generate Foils

```bash
# Generate all foils
./programisto.py foil

# Save to specific directory
./programisto.py foil --output ./src/foils

# View generated foils
cat ./src/foils/foil_base-component.tsx
```

### Generate Engineering Harness

```bash
# Generate basic harness
./programisto.py harness

# Save to specific directory
./programisto.py harness --output ./scripts
```

### Analyze Logs

```bash
# Analyze all log files in project
./programisto.py log

# See summary of errors and warnings
```

### Admin: Create New Project

```bash
# Create a new project with Programisto
./programisto.py admin new-project my-new-project

# The project will be initialized with:
# - programisto-config.yaml
# - skills_catalog/
# - PROJECT_CONTEXT.md
```

### Admin: Add CLI Tool

```bash
# Register a new CLI tool
./programisto.py admin add-cli aider

# Enable a tool
./programisto.py tools enable claude-code

# Disable a tool
./programisto.py tools disable codex

# Validate configuration
./programisto.py tools validate
```

## Project Structure

```
programisto/
├── programisto.py          # Main CLI entry point
├── config.py               # Configuration management
├── programisto-config.yaml # Default configuration
├── scanner/
│   └── project_scanner.py  # Project directory scanning
├── llm/
│   └── client.py           # LLM API client
├── assistant/
│   └── main.py             # Main assistant
├── foils/
│   └── generator.py        # Foil generator
├── harness/
│   └── generator.py        # Engineering harness generator
├── analyzer/
│   └── log_analyzer.py     # Log file analyzer
├── context/
│   └── prompts.py          # Context-aware prompt builder
├── skills/
│   ├── catalog.py          # Skill catalog management
│   └── selector.py         # Skill selection
├── tools/
│   └── cli_support.py      # Multi-agent CLI support
├── admin/
│   └── commands.py         # Admin commands
├── utils/
│   └── testing.py          # Testing utilities
└── skills_catalog/
    └── skills.json         # Skill definitions
```

## Requirements

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- OpenAI-compatible API access (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License
# programisto
