You are a Senior FastAPI Architect.

We have completed Phase 1 Step 1 of an AI Data Engineering Copilot project.

Current state:

* FastAPI application exists
* Service layer exists
* Schema layer exists
* GET /health endpoint exists

Implement Phase 1 Step 2.

Requirements:

1. Add configuration management.
2. Use Pydantic Settings.
3. Create:

   * app/core/config.py
   * .env
   * .env.example
4. Move application title into configuration.
5. Explain every file.
6. Explain why configuration should not be hardcoded.
7. Add Docker support.
8. Create:

   * Dockerfile
   * docker-compose.yml
9. Explain every Docker instruction.
10. Show commands for:

    * Local execution
    * Docker execution

Do not add:

* PostgreSQL
* AI models
* Ollama
* Authentication
* Repositories

Act as a mentor and explain every architectural decision before showing code.
