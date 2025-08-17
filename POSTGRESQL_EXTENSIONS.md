# PostgreSQL Extensions for Render Deployment

This file explains the purpose of the PostgreSQL-specific SQL files in this project.

## init-pgvector.sql

The `init-pgvector.sql` file contains PostgreSQL-specific syntax to enable the pgvector extension, which is required for vector embeddings in the affiliate website. This SQL file is used in:

1. The Docker Compose setup to initialize the local database
2. The Render deployment to ensure the pgvector extension is enabled

Note that the SQL syntax in this file is specific to PostgreSQL and will show errors if viewed with SQL Server (MSSQL) syntax highlighting or validation in VS Code.

## Why pgvector?

The pgvector extension allows PostgreSQL to store and search over vector embeddings, which are used in the Affiliate Website's search functionality:

- Semantic search for offers and campaigns
- RAG (Retrieval Augmented Generation) for the chat feature
- Coupon code search functionality

## Usage in Render

The Render deployment automatically sets up the pgvector extension through the `render.yaml` configuration:

```yaml
databases:
  - name: affiliate-db
    # ...
    extensions:
      - vector
```

This ensures that when Render creates the PostgreSQL database, it also enables the pgvector extension.
