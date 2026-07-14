# Model Server

This folder is the deployment root for the GPU/application server. The API and Streamlit containers are stateless and connect to the database server through its private address.

```bash
cp .env.example .env
docker compose --env-file .env config
docker compose --env-file .env up -d api streamlit proxy
```

The command above does not start vLLM. Start the GPU profile only after confirming the GPU is available:

```bash
docker compose --env-file .env --profile gpu up -d vllm
```

Apply PostgreSQL migrations from the independently deployed `database-server` repository before starting the API.

Documentation maps: `docs/README.md` and `docs/.study/README.md`.
