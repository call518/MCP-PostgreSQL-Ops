---
name: Bug Report
about: Report a bug to help us improve MCP PostgreSQL Operations
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce
1. 
2. 
3. 
4. 

## Expected Behavior
<!-- What you expected to happen -->

## Actual Behavior
<!-- What actually happened -->

## Environment Details
### PostgreSQL Environment
- **PostgreSQL Version**: 
- **Extensions Installed**: 
  - [ ] pg_stat_statements
  - [ ] pg_stat_monitor
  - [ ] Other: ___
- **Environment Type**: 
  - [ ] Self-managed PostgreSQL
  - [ ] Docker container
  - [ ] AWS RDS
  - [ ] AWS Aurora
  - [ ] Google Cloud SQL
  - [ ] Azure Database
  - [ ] Other: ___
- **User Permissions**: 
  - [ ] Superuser
  - [ ] Regular user with pg_read_all_stats
  - [ ] Regular user without special permissions
  - [ ] Other: ___

### MCP Server Environment
- **Installation Method**: 
  - [ ] PyPI (uvx)
  - [ ] Local source
  - [ ] Docker
- **Python Version**: 
- **MCP Server Version**: 
- **Client Used**: 
  - [ ] Claude Desktop
  - [ ] Open WebUI
  - [ ] MCP Inspector
  - [ ] Other: ___

## Error Messages
<!-- Include full error messages, stack traces, or logs -->
```
[Paste error messages here]
```

## Configuration
<!-- Share relevant configuration (remove sensitive information) -->
```json
{
  "env": {
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "your_db"
  }
}
```

## Additional Context
<!-- Add any other context about the problem here -->
- Does this affect all tools or specific ones?
- When did this start happening?
- Any recent changes to your environment?

## Screenshots
<!-- If applicable, add screenshots to help explain your problem -->
