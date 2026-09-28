# syntax=docker/dockerfile:1
FROM python:3.12.10-slim-bookworm AS test
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY teacher_service/ teacher_service/
COPY profiles/ profiles/
COPY prompts/ prompts/
COPY schemas/ schemas/
COPY tests/ tests/
RUN python -m unittest discover -s tests -v

FROM nvidia/cuda:12.8.1-devel-ubuntu24.04 AS build
ENV LLAMA_COMMIT=7fe450e19305b828c199d602c23a8337aaa1f03b
ARG CUDA_ARCHITECTURES=80;86;89;90
ARG BUILD_JOBS=2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git ca-certificates libssl-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /build/llama
RUN git init && git remote add origin https://github.com/ggml-org/llama.cpp.git \
    && git fetch --depth 1 origin "$LLAMA_COMMIT" && git checkout --detach FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "$LLAMA_COMMIT"
RUN ln -s libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON \
    -DGGML_NATIVE=OFF -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCHITECTURES" \
    -DCMAKE_EXE_LINKER_FLAGS="-L/usr/local/cuda/lib64/stubs -Wl,-rpath-link,/usr/local/cuda/lib64/stubs" \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_APP=OFF \
    -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF \
    && cmake --build build --target llama-server -j "$BUILD_JOBS" \
    && mkdir -p /out && cp -a build/bin/. /out/ \
    && find build -name '*.so*' -exec cp -P '{}' /out/ \;

FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04
ARG VCS_REF=unknown
LABEL org.opencontainers.image.source="https://github.com/serda-dev/linguai-teacher-model" \
      org.opencontainers.image.revision="$VCS_REF"
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv curl ca-certificates libgomp1 libssl3t64 tini \
    && rm -rf /var/lib/apt/lists/* && python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" LD_LIBRARY_PATH="/opt/llama:${LD_LIBRARY_PATH}" \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=build /out/ /opt/llama/
COPY --from=build /build/llama/LICENSE /opt/llama/LICENSE
COPY teacher_service/ teacher_service/
COPY profiles/ profiles/
COPY prompts/ prompts/
COPY schemas/ schemas/
COPY scripts/ scripts/
RUN mkdir -p /workspace/models
EXPOSE 8000
STOPSIGNAL SIGTERM
# Liveness only: a model download may take up to two hours. Use authenticated /ready separately.
HEALTHCHECK --interval=30s --timeout=5s --start-period=120m --retries=3 \
  CMD ["python", "scripts/health.py"]
ENTRYPOINT ["/usr/bin/tini", "--", "python", "-m", "teacher_service.launch"]
