# Model node Kubernetes resources

Label the GPU/application node with `hazel-role=model`. Replace secret placeholders with the database server's private address. Apply `namespace.yaml`, the managed secret, `services.yaml`, `model-server.yaml`, and `proxy.yaml` after the database repository migration job succeeds.

`hazel-vllm` remains at zero replicas. Do not scale it up until GPU execution is explicitly approved.
