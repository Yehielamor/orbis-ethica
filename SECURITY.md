# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are
currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, please follow these steps:

1.  **Do NOT open a public issue.** Publicly disclosing a vulnerability can put the entire network at risk before a fix is available.
2.  Send an email to **orbisethica@gmail.com**.
3.  Include a detailed description of the vulnerability, steps to reproduce, and any relevant logs or code snippets.
4.  Our security team (The Guardians) will acknowledge your report within 48 hours.
5.  We will provide regular updates on our progress until the issue is resolved.

### Bounty Program

We currently do not offer a monetary bug bounty, but we will happily acknowledge your contribution in our "Hall of Fame" (with your permission).

## Critical Areas

The following areas are considered critical security boundaries:
- **Consensus Mechanism:** Any exploit that allows a node to bypass the ULFR verification.
- **Identity & Auth:** Any bypass of the Ed25519 signature verification.
- **P2P Layer:** Vulnerabilities allowing DoS or remote code execution via gossip messages.
