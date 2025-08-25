# Pull Request

## Description
<!-- Briefly describe what this PR does -->

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Code refactoring (no functional changes)
- [ ] 🎨 Style/formatting changes
- [ ] ⚡ Performance improvement
- [ ] 🧪 Adding or updating tests

## Related Issues
<!-- Link to related issues using # -->
Fixes #(issue number)
Relates to #(issue number)

## Changes Made
<!-- List the main changes in this PR -->
- 
- 
- 

## PostgreSQL Compatibility
<!-- Mark all that apply with an "x" -->
- [ ] Tested on PostgreSQL 12
- [ ] Tested on PostgreSQL 13
- [ ] Tested on PostgreSQL 14
- [ ] Tested on PostgreSQL 15
- [ ] Tested on PostgreSQL 16
- [ ] Tested on PostgreSQL 17
- [ ] Version-aware implementation (handles differences between versions)
- [ ] Extension-independent (works without pg_stat_statements/pg_stat_monitor)
- [ ] Extension-dependent (requires specific extensions)

## Testing
<!-- Describe how you tested your changes -->
### Manual Testing
- [ ] Tested with MCP Inspector (`./scripts/run-mcp-inspector-local.sh`)
- [ ] Tested with direct execution
- [ ] Tested with Docker environment
- [ ] Tested with custom PostgreSQL instance

### Test Environment
- PostgreSQL version(s): 
- Extensions installed: 
- Environment: [ ] Docker [ ] Local [ ] RDS/Aurora [ ] Other: ___

### Test Cases
<!-- List specific test cases or scenarios -->
- [ ] Basic functionality works
- [ ] Error handling works correctly
- [ ] Edge cases handled
- [ ] Performance acceptable
- [ ] Output format consistent

## Documentation
<!-- Mark all that apply with an "x" -->
- [ ] Updated README.md
- [ ] Updated Tool Compatibility Matrix
- [ ] Added usage examples
- [ ] Updated docstrings
- [ ] No documentation needed

## Security Considerations
<!-- Mark all that apply with an "x" -->
- [ ] Read-only operations only
- [ ] No sensitive data exposed
- [ ] Proper input validation
- [ ] No SQL injection risks
- [ ] Follows principle of least privilege

## Screenshots/Output Examples
<!-- If applicable, add screenshots or example outputs -->

## Checklist
<!-- Mark completed items with an "x" -->
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] My code is properly commented, particularly in complex areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have tested my code across multiple PostgreSQL versions where applicable
- [ ] Any dependent changes have been merged and published

## Additional Notes
<!-- Add any additional notes, concerns, or context -->
