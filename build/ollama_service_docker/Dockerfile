FROM ollama/ollama:0.4.1

# Pre-pull llama3.2:3b model at build time

RUN /bin/bash -c "ollama serve & \
    until echo > /dev/tcp/localhost/11434 2>/dev/null; do sleep 1; done && \
    ollama pull llama3.2:3b && \
    pkill ollama"

# Default command and port exposure are inherited from base image