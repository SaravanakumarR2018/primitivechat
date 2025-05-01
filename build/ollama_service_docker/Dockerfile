FROM ollama/ollama:0.5.13

# Accept OLLAMA_MODEL as a build argument
ARG OLLAMA_MODEL
ENV OLLAMA_MODEL=${OLLAMA_MODEL}

# Print the value of OLLAMA_MODEL during the build
RUN echo "OLLAMA_MODEL is set to: ${OLLAMA_MODEL}"

# Pre-pull the model specified in the OLLAMA_MODEL environment variable
RUN /bin/bash -c "ollama serve & \
    until echo > /dev/tcp/localhost/11434 2>/dev/null; do sleep 1; done && \
    ollama pull ${OLLAMA_MODEL} && \
    pkill ollama"

# Default command and port exposure are inherited from base image