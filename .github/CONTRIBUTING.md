# Contributing to MCP PostgreSQL Operations

🎉 Thank you for your interest in contributing to MCP PostgreSQL Operations! Whether you're fixing a bug, adding a new monitoring tool, or improving documentation, your contributions make this project better for everyone.

## Getting Started

### Prerequisites

- PostgreSQL 12+ (for testing)
- Python 3.12
- UV package manager
- Git

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/MCP-PostgreSQL-Ops.git
   cd MCP-PostgreSQL-Ops
   ```

2. **Set up the development environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL connection details
   ```

3. **Start the test environment:**
   ```bash
   docker-compose up -d
   ```

4. **Test the setup:**
   ```bash
   ./scripts/run-mcp-inspector-local.sh
   ```

## Ways to Contribute

### � Using Issue Templates

When you click "New Issue" on GitHub, you'll see a template selection page with these options:
- **🐛 Bug Report** - Report bugs with detailed PostgreSQL environment information
- **💡 Feature Request** - Suggest new monitoring tools or improvements with PostgreSQL-specific requirements
- **📚 Documentation** - Report documentation issues or suggest improvements
- **❓ Question** - Ask general questions about setup, usage, or PostgreSQL compatibility

You'll also find quick links to:
- **🔒 Security Issues** - Report security vulnerabilities privately
- **💬 GitHub Discussions** - Community discussions and advanced usage strategies
- **📖 Documentation** - README with setup guides and examples
- **🧪 MCP Inspector** - Local testing and debugging information
- **🗂️ Tool Compatibility Matrix** - PostgreSQL version compatibility reference

> **💡 Tip**: For security vulnerabilities related to database access or potential SQL injection, always use the Security Advisories feature instead of public issues.

### �🐛 Bug Reports

**Use the [Bug Report template](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=bug_report.md)** to report issues.

The template will guide you to include:
- PostgreSQL version and environment details
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages or logs
- MCP server configuration used

### 💡 Feature Requests

**Use the [Feature Request template](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=feature_request.md)** to suggest improvements.

We welcome suggestions for:
- New PostgreSQL monitoring tools
- Additional database analysis features
- Performance improvements
- Documentation enhancements

The template will help you provide:
- The use case or problem you're trying to solve
- Your proposed solution
- PostgreSQL-specific requirements
- Expected output format and usage examples

### 🔧 Code Contributions

#### Adding New MCP Tools

The codebase is designed to be developer-friendly. To add a new monitoring tool:

1. **Add your function to `src/mcp_postgresql_ops/mcp_main.py`:**
   ```python
   @mcp.tool()
   def get_your_new_tool(
       parameter1: str = "default_value",
       parameter2: int = 10
   ) -> list[dict]:
       """
       Brief description of what this tool does.
       
       Args:
           parameter1: Description of parameter1
           parameter2: Description of parameter2
           
       Returns:
           List of dictionaries with monitoring data
       """
       # Your implementation here
       pass
   ```

2. **Follow these patterns:**
   - Use descriptive function names starting with `get_`
   - Include comprehensive docstrings
   - Handle PostgreSQL version compatibility
   - Return structured data (list of dictionaries)
   - Use read-only queries only

3. **Test across PostgreSQL versions:**
   - Test with PostgreSQL 12, 15, 16, 17 if possible
   - Ensure graceful degradation for version-specific features
   - Update the Tool Compatibility Matrix in README

#### Code Style Guidelines

- **Python**: Follow PEP 8 standards
- **SQL**: Use uppercase for SQL keywords, lowercase for identifiers
- **Comments**: Explain complex logic and PostgreSQL-specific behavior
- **Error handling**: Provide meaningful error messages
- **Version compatibility**: Always consider PostgreSQL version differences

#### Testing Your Changes

1. **Manual testing:**
   ```bash
   # Test with local development
   python -m src.mcp_postgresql_ops.mcp_main --log-level DEBUG
   
   # Test with MCP Inspector
   ./scripts/run-mcp-inspector-local.sh
   ```

2. **Version compatibility testing:**
   - Test against different PostgreSQL versions
   - Verify tool behavior with and without extensions
   - Check error handling for unsupported features

### 📚 Documentation

**Use the [Documentation Issue template](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=documentation.md)** to report documentation problems.

Help improve our documentation by:
- Fixing typos or unclear explanations
- Adding usage examples
- Improving tool descriptions
- Updating compatibility information

## PostgreSQL-Specific Guidelines

### Version Compatibility

- **Support PostgreSQL 12-17**
- Use version detection: `get_postgresql_version()`
- Handle version-specific features gracefully
- Update compatibility matrix when adding features

### Query Guidelines

- **Read-only operations only** - no data modification
- Use system catalogs and statistics views
- Handle missing extensions gracefully
- Optimize for performance on production systems
- Mask sensitive information in outputs

### Extension Handling

- Most tools should work without extensions
- For `pg_stat_statements` dependent features, check availability first
- Provide fallback behavior when extensions are missing
- Document extension requirements clearly

## Submitting Changes

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the coding guidelines
   - Add or update tests if applicable
   - Update documentation as needed

3. **Test thoroughly:**
   - Test with multiple PostgreSQL versions
   - Verify backward compatibility
   - Check error handling

4. **Commit with clear messages:**
   ```bash
   git commit -m "Add tool for monitoring connection pooling
   
   - New get_connection_pool_stats function
   - Compatible with PostgreSQL 12-17
   - Handles missing pg_stat_statements gracefully"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then create a Pull Request using our [PR template](https://github.com/call518/MCP-PostgreSQL-Ops/compare) which will guide you through the submission process.

### Pull Request Guidelines

Our **Pull Request template** will help you provide:
- **Clear title and description**
- **PostgreSQL compatibility information**
- **Testing details and environment info**
- **Documentation updates checklist**
- **Security considerations**

The template ensures all necessary information is included for efficient review.

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and questions
- Focus on constructive feedback
- Help others learn PostgreSQL monitoring concepts

### Getting Help

- **🐛 [Bug Reports](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=bug_report.md)**: For bugs and technical issues
- **💡 [Feature Requests](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=feature_request.md)**: For new features and enhancements  
- **📚 [Documentation Issues](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=documentation.md)**: For documentation problems
- **❓ [Questions](https://github.com/call518/MCP-PostgreSQL-Ops/issues/new?template=question.md)**: For general questions and support
- **💬 [Discussions](https://github.com/call518/MCP-PostgreSQL-Ops/discussions)**: For broader discussions and community interaction

## Recognition

Contributors are recognized in:
- Project documentation
- Release notes
- Special thanks for significant contributions

## PostgreSQL Expertise Levels

Don't worry if you're not a PostgreSQL expert! Contributions are welcome at all levels:
- **Beginners**: Documentation, testing, simple bug fixes
- **Intermediate**: New monitoring tools, compatibility improvements
- **Advanced**: Complex performance analysis features, version-specific optimizations

## Development Tips

### Understanding the Codebase

- **`mcp_main.py`**: Main MCP server implementation
- **`functions.py`**: Database utility functions
- **`version_compat.py`**: PostgreSQL version compatibility helpers
- **`scripts/`**: Development and testing utilities

### PostgreSQL Testing Resources

- Use the included test data (`scripts/create-test-data.sql`)
- Test with different user permissions (superuser vs regular user)
- Verify behavior on RDS/Aurora environments when possible

---

Thank you for contributing to MCP PostgreSQL Operations! Your efforts help make PostgreSQL monitoring more accessible to everyone. 🚀
