# Gateway Performance Benchmark & Security Filter Analysis

A comprehensive performance benchmarking tool and gateway service designed to measure request latency, tail percentile behavior (p90, p99), and rate-limiting efficacy under heavy concurrency.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture & Routing](#-architecture--routing)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#-usage)
  - [Running the Gateway Service](#running-the-gateway-service)
  - [Running Benchmark Load Tests](#running-benchmark-load-tests)
- [Benchmark Results](#-benchmark-results)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📌 Overview

This project evaluates latency and filtering behavior across different request pathways (`PASS`, `MASK`, and `BLOCK`) for high-throughput API endpoints such as `/v1/chat/completions`. It uses Redis-backed rate limiting to measure service degradation and token-bucket performance during peak traffic spikes.

---

## ✨ Features

- **Multi-Route Security Filtering:** Dynamically tags and routes incoming payloads (`PASS`, `MASK`, `BLOCK`).
- **Tail Latency Tracking:** Measures exact median (p50), p90, and p99 percentile distribution under load.
- **Distributed Rate Limiting:** High-performance Redis integration enforcing sliding window and token bucket limits.
- **Automated Benchmarking:** Built-in headless load test suites powered by Locust.

---

## 🏗 Architecture & Routing
┌─────────────────────────┐
              │    Incoming Requests    │
              └────────────┬────────────┘
                           │
                   [ Redis Limiter ]
                  /        │        \
             (429)      (200 OK)    (403/400)
             Rate          │          Rule
            Limited        │        Blocked
                │          │           │
                ▼          ▼           ▼
              [PASS]     [MASK]     [BLOCK]

- **PASS:** Clean requests routed directly to downstream models.
- **MASK:** Payloads with sensitive content masked prior to downstream execution.
- **BLOCK:** Disallowed payloads halted at the rule evaluation layer.

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python 3.9+**
- **Redis Server** (local instance or Docker container)
- **Git**

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/guardllm-pilot.git](https://github.com/your-username/guardllm-pilot.git)
   cd guardllm-pilot

### Set up a virtual environment

*On Windows (PowerShell):*
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

*On Linux / macOS:*
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```
## 💻 Usage

### Running the Gateway Service

Start the Redis server and launch the gateway application:

```bash
# Ensure Redis is running
redis-server

# Launch the gateway application
python main.py
```

### Running Benchmark Load Tests

Execute the automated Locust load test suite in headless mode:

```bash
locust -f load_test.py --headless -u 50 -r 5 --run-time 2m --host http://localhost:8000
```
## 📊 Benchmark Results

Summary of a 3,000+ request execution run across all routes under peak concurrency:

| Endpoint / Tag | Total Requests | Median (p50) | p90 Latency | p99 Latency | Avg Latency | Failure Rate (429) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/v1/chat/completions [BLOCK]` | 135 | 13 ms | 170 ms | **1,800 ms** | 87 ms | 99.26% |
| `/v1/chat/completions [MASK]` | 457 | 12 ms | 160 ms | **1,900 ms** | 88 ms | 98.03% |
| `/v1/chat/completions [PASS]` | 986 | 12 ms | 150 ms | **1,700 ms** | 65 ms | 99.49% |
| **Aggregated Total** | **3,152** | **12 ms** | **150 ms** | **1,800 ms** | **74 ms** | **49.59%** |

## 📁 Project Structure

```
.
├── .gitignore          # Rules for files to ignore in Git
├── README.md           # Project documentation
├── LICENSE             # MIT License file
├── requirements.txt    # Python dependencies
├── main.py             # Main application & routing gateway
├── load_test.py        # Locust load testing setup
└── config.py           # Environment and rate limit parameters
```

---

## ⚙️ Configuration

Key environment variables can be set in a `.env` file or exported directly:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `REDIS_HOST` | `localhost` | Redis server address |
| `REDIS_PORT` | `6379` | Redis server port |
| `RATE_LIMIT_RPM` | `1000` | Allowed requests per minute before HTTP 429 |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/NewFeature`).
3. Commit your changes (`git commit -m "Add NewFeature"`).
4. Push to the branch (`git push origin feature/NewFeature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.