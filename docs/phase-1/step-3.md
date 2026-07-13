You are a Senior Backend Engineer.

We are building an AI Data Engineering Copilot.

Current state:

* FastAPI application exists
* Configuration system exists
* Docker setup exists
* Health endpoint exists

Implement Phase 1 Step 3.

Requirements:

1. Add PostgreSQL support using SQLAlchemy.
2. Create database session management.
3. Create a database_connections table.
4. Implement:

   * POST /connections
   * GET /connections
   * DELETE /connections/{id}
   * POST /connections/test
5. Use repository pattern.
6. Use service layer.
7. Explain:

   * Why repository exists
   * Why service exists
   * Why we test connections
   * Why metadata is stored separately
8. Show complete folder structure.
9. Explain every file.
10. Include Alembic setup for migrations.

Do not implement:

* Schema extraction
* AI integration
* OpenAI
* Ollama
* RAG
