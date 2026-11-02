# InfraGuardian AI

InfraGuardian AI is an AI-assisted platform engineering workspace.

The initial capability is AI-powered automated regression testing.

The system is designed to allow an AI Test Agent to:

- Understand application behaviour
- Identify important user journeys
- Generate test scenarios
- Execute browser-based tests
- Validate expected vs actual behaviour
- Investigate failures
- Distinguish application defects from environment issues
- Produce a test report

---

# Architecture

```text
                    InfraGuardian AI
                           |
                           v
                    +-------------+
                    |  Frontend   |
                    |   Flask     |
                    +------+------+
                           |
                           | HTTP
                           v
                    +-------------+
                    |   IG API    |
                    |   Flask     |
                    +------+------+
                           |
                           | Test request
                           v
                    +-------------+
                    | Test Agent  |
                    |   Foundry   |
                    +------+------+
                           |
                    +------+------+
                    |             |
                    v             v
              AI Model     Browser Tool
                                |
                                v
                       Playwright Workspace
                                |
                                v
                           CustomerApp