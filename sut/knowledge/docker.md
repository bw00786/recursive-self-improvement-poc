# Docker

A Docker image is a read-only template built in layers; each Dockerfile
instruction adds a layer, and layers are cached so unchanged steps do not
rebuild. A container is a running instance of an image with its own
filesystem, process namespace, and network namespace.

Docker Compose defines multi-container applications in a YAML file with
services, networks, and volumes. Resource limits use --cpus and --memory;
read-only mounts use :ro and prevent a container from modifying host files.

A bridge network gives containers private IPs; host.docker.internal lets a
container reach services on the host machine.
