# AI Coding Agent Instructions

## Project Overview
This project is a GitHub management tool designed to:
- Batch invite users to join an organization or specific teams within the organization.
- Provide metrics and insights about the organization and its teams.

The project is implemented in Python 3.12 and all operations are executed within a `venv` environment.

## Key Components
1. **Batch Invitation System**
   - Automates the process of inviting users to join GitHub organizations or teams.
   - Handles bulk operations efficiently.

2. **Metrics and Insights**
   - Collects and displays data about organizational and team performance.
   - Provides actionable insights for administrators.

## Development Environment
- **Python Version**: 3.12
- **Virtual Environment**: All operations must be executed within a `venv` environment.
  - To create a `venv`:
    ```cmd
    python -m venv venv
    ```
  - To activate the `venv`:
    ```cmd
    venv\Scripts\activate
    ```

## Project Structure
- Ensure the project follows a modular structure with clear separation of concerns.
- Key directories and files:
  - `invitation/`: Contains logic for batch invitations.
  - `metrics/`: Handles data collection and analysis.
  - `tests/`: Unit tests for all components.

## Coding Conventions
- Follow PEP 8 for Python code style.
- Use type hints for all functions and methods.
- Write docstrings for all public functions and classes.

## Workflows
### Batch Invitation Workflow
1. Read user data from a CSV file.
2. Validate user data.
3. Send invitations using GitHub API.

### Metrics Collection Workflow
1. Authenticate with GitHub API.
2. Fetch data about organizations and teams.
3. Process and store data for analysis.

## External Dependencies
- **GitHub API**: Used for managing organizations, teams, and invitations.
- Install required dependencies using:
  ```cmd
  pip install -r requirements.txt
  ```

## Testing
- Use `pytest` for running tests.
- To execute tests:
  ```cmd
  pytest
  ```

## Examples
### Sending Invitations
Example script to send invitations:
```python
from invitation import send_invitations

send_invitations('users.csv')
```

### Fetching Metrics
Example script to fetch metrics:
```python
from metrics import fetch_metrics

fetch_metrics()
```

## Notes
- Ensure all API keys and sensitive data are stored securely (e.g., environment variables).
- Document any new patterns or workflows in this file.