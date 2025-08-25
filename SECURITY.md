# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### 🔒 Preferred Method: GitHub Security Advisories

1. Go to the [Security Advisories page](https://github.com/call518/MCP-PostgreSQL-Ops/security/advisories)
2. Click "Report a vulnerability"
3. Fill out the security advisory form with details

### 📧 Alternative Contact

If you prefer email communication, you can reach out to the maintainer:
- **Email**: [Contact through GitHub profile](https://github.com/call518)
- **Response Time**: We aim to respond within 48 hours

## What to Include

When reporting a security vulnerability, please include:

### 🎯 Vulnerability Details
- **Type of vulnerability** (e.g., SQL injection, authentication bypass, data exposure)
- **Component affected** (specific MCP tool, database connection, etc.)
- **PostgreSQL version(s)** where the vulnerability exists
- **Environment details** (deployment method, permissions, extensions)

### 📋 Reproduction Information
- **Step-by-step reproduction guide**
- **Sample configuration** (with sensitive data removed)
- **Expected vs actual behavior**
- **Potential impact assessment**

### 🛡️ Suggested Mitigation
- **Immediate workarounds** (if any)
- **Proposed fixes** (if you have suggestions)
- **Affected user base** (estimation)

## Security Considerations

### 🔍 Common Security Areas

Our MCP server handles sensitive database operations. Key security areas include:

- **Database Connection Security**: Connection string handling, credential management
- **Query Safety**: SQL injection prevention, query validation
- **Data Exposure**: Sensitive information masking in outputs
- **Access Control**: Permission requirements, privilege escalation prevention
- **Network Security**: Connection encryption, host validation
- **Extension Security**: Safe handling of pg_stat_statements and pg_stat_monitor data
- **MCP Transport Security**: Secure client-server communication

### 🛡️ Built-in Security Features

- **Read-only Operations**: All tools perform read-only database operations
- **Input Validation**: Query parameters are validated and sanitized
- **Credential Masking**: Passwords and sensitive data are masked in logs/outputs
- **Least Privilege**: Operates with minimal required database permissions
- **Version Compatibility**: Secure handling across PostgreSQL 12-17

## Vulnerability Response Process

### ⏱️ Timeline

1. **Initial Response**: Within 48 hours of report
2. **Vulnerability Assessment**: Within 1 week
3. **Fix Development**: Timeline depends on severity
4. **Security Release**: Coordinated disclosure with reporter
5. **Public Disclosure**: After fix is available and users have time to update

### 📊 Severity Classification

We follow industry-standard CVSS scoring:

- **Critical (9.0-10.0)**: Immediate attention, emergency release
- **High (7.0-8.9)**: High priority, next planned release
- **Medium (4.0-6.9)**: Normal priority, regular release cycle
- **Low (0.1-3.9)**: Low priority, may be bundled with other updates

## Security Best Practices for Users

### 🔐 Deployment Security

- **Use dedicated database users** with minimal required permissions
- **Enable SSL/TLS** for database connections
- **Regularly rotate credentials** and connection strings
- **Monitor access logs** for unusual activity
- **Keep PostgreSQL updated** to latest supported version
- **Secure extension data**: Be aware that pg_stat_statements contains query text and execution statistics

### 🛡️ Configuration Security

- **Avoid superuser permissions** unless absolutely necessary
- **Use connection pooling** with appropriate limits
- **Configure proper network isolation** (VPC, firewalls)
- **Enable audit logging** in PostgreSQL for sensitive environments
- **Review MCP client access** regularly

### 🔗 MCP Client Security

- **Client authentication**: Ensure secure MCP server access and authorized clients only
- **Transport security**: Use HTTPS for streamable-http mode in production
- **Client validation**: Monitor and restrict MCP client connections
- **Environment variables**: Secure storage of database credentials in client configurations

### 🐳 Docker Deployment Security

- **Container isolation**: Use non-root users in containers
- **Secrets management**: Use Docker secrets or secure environment variable injection
- **Network security**: Proper container network configuration and port restrictions
- **Image security**: Use official PostgreSQL images and keep containers updated

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who report vulnerabilities responsibly:

- **Public acknowledgment** in release notes (if desired)
- **Security researchers page** recognition
- **Direct communication** throughout the process

## Contact

For security-related questions or concerns:

- **GitHub Security Advisories**: [Report a vulnerability](https://github.com/call518/MCP-PostgreSQL-Ops/security/advisories/new)
- **General Security Questions**: [GitHub Discussions - Security](https://github.com/call518/MCP-PostgreSQL-Ops/discussions)
- **Maintainer Contact**: Available through GitHub profile

---

**Thank you for helping keep MCP PostgreSQL Operations and the community safe!** 🛡️
