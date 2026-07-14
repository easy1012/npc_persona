# Database node Kubernetes resources

This storage topology is pinned to one physical database node and is not high availability. Label the node before applying manifests:

```bash
kubectl label node <database-node> hazel-role=database
```

Replace `secrets.example.yaml` values through the cluster secret-management process; do not commit real credentials. The CNI must enforce NetworkPolicy. Database persistent volumes must use a local StorageClass with `WaitForFirstConsumer`, and backups must leave the database node.

Copy `storage.example.yaml`, replace `replace-database-node`, create `/srv/hazel/postgres` and `/srv/hazel/neo4j` on the database node, then apply storage and database resources. After PostgreSQL is ready, run `migration-job.yaml` before starting the API.

The model repository owns API, Streamlit, and vLLM manifests. This repository does not request GPU resources.
