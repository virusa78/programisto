# Programisto Implementation Plan

## Overview
Build a Python-based coding assistant for web developers with project scanning, LLM integration, CLI interface, and skill management.

## Project Structure

```
programisto/
├── programisto.py          # Main CLI entry point
├── config.py               # Configuration management
├── scanner/
│   ├── __init__.py
│   └── project_scanner.py  # Requirement 1: Project directory scanning
├── llm/
│   ├── __init__.py
│   └── client.py           # Requirement 2: External LLM integration
├── assistant/
│   ├── __init__.py
│   └── main.py             # Requirement 3: Main assistant functionality
├── foils/
│   ├── __init__.py
│   └── generator.py        # Requirement 4: Foil generation
├── harness/
│   ├── __init__.py
│   └── generator.py        # Requirement 5: Engineering harness generation
├── analyzer/
│   ├── __init__.py
│   └── log_analyzer.py     # Requirement 8: Log analyzer
├── context/
│   ├── __init__.py
│   └── prompts.py          # Requirement 9: Context-aware prompts
├── skills/
│   ├── __init__.py
│   ├── catalog.py          # Requirement 14: Skill catalog indexing
│   └── selector.py         # Requirement 13: LLM-based skill selection
├── tools/
│   ├── __init__.py
│   └── cli_support.py      # Requirement 15: Multi-agent CLI support
├── admin/
│   ├── __init__.py
│   └── commands.py         # Requirement 16: Admin commands
├── utils/
│   ├── __init__.py
│   └── testing.py          # Requirement 7: Testing/dry-run support
├── skills_catalog/         # Skill definitions
│   └── skills.json
├── programisto-config.yaml # Main configuration file
└── README.md
```

## Implementation Phases

### Phase 1: Core Infrastructure (Requirements 1, 3, 15)
- Main CLI entry point with argparse
- Configuration management (YAML)
- Project directory scanner
- Multi-agent CLI tool support

### Phase 2: LLM Integration (Requirements 2, 9)
- OpenAI-compatible API client
- Context-aware prompt construction
- Project context extraction

### Phase 3: Assistant Features (Requirements 3, 4, 5, 6, 8, 11)
- Main assistant CLI commands
- Foil generator for web development patterns
- Engineering harness generator
- Log analyzer
- User confirmation flow for parameters

### Phase 4: Skill Management (Requirements 10, 12, 13, 14)
- Skill catalog indexing
- LLM-based skill selection
- Full skill set generation

### Phase 5: Admin Commands (Requirement 16)
- `admin add-skill-repo`
- `admin add-cli`
- `admin new-project`

### Phase 6: Testing & Polish (Requirement 7)
- Dry-run execution support
- Testing utilities
- Documentation

## Key Design Decisions

1. **Configuration**: YAML-based config with validation
2. **LLM Integration**: OpenAI-compatible API (configurable endpoint)
3. **Skill System**: JSON-based catalog with LLM recommendations
4. **Project Scope**: All operations limited to project directory
5. **CLI Framework**: argparse with subcommands for modularity

## Next Steps
Awaiting your approval to begin implementation.
