FROM python:3.11-slim

WORKDIR /app

# Install only required build dependencies
RUN apt-get update && \
    apt-get install -y \
        cmake \
        g++ \
        make \
        bison \
        flex \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Build clingo
RUN cd lib/clingo && \
    cmake -S . -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCLINGO_BUILD_WITH_PYTHON=OFF \
        -DCLINGO_BUILD_SHARED=OFF && \
    cmake --build build -j

# Clean any old build artifacts
RUN rm -rf ./lib/downward/builds/release

# Run downward build script
RUN python3 ./lib/downward/build.py

# Let backend know where clingo lives (optional but recommended)
ENV CLINGO_BINARY=/app/lib/clingo/build/bin/clingo

# Expose Flask port
EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
