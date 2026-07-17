# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainers directly with:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact
4. Any suggested fix (if applicable)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.
- **Assessment**: We will investigate and assess the severity within 7 days.
- **Resolution**: We aim to release a fix for confirmed vulnerabilities within 30 days.
- **Credit**: With your permission, we will credit you in the release notes.

## Security Considerations for This Project

This project is an AI search audit skill that runs deterministic scripts.

- **No network requests from scripts**: Core audit scripts do not make outbound HTTP requests. All web search functionality is delegated to the host agent's `web_search` tool.
- **No shell execution**: Scripts do not execute arbitrary shell commands.
- **No credential handling**: The skill does not read, store, or transmit API keys, tokens, or other secrets.
- **Filesystem isolation**: Scripts only read/write within the designated run directory and do not access paths outside the configured base directory.

If you believe any of these invariants have been violated, please report it immediately.

## Best Practices for Users

- Run the skill in an isolated environment (e.g., Docker container or virtual machine).
- Review the input JSON schema before providing brand data.
- Do not include sensitive personal information in audit inputs.
- Keep your Python runtime and dependencies up to date.