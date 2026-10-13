# MyHomeStead.io: Open-Source Database Connectivity Guide

> **Universal open-source database integration architecture for MyHomeStead.io and Home Assistant.**  
> Enables local-first telemetry storage, hypertable time-series analytics, relational records, and zero-cloud data ownership.

---

## 🏛️ Supported Open-Source Databases

The **MyHomeStead.io** suite provides built-in sink connectors and schema exporters for the industry's premier open-source database engines:

```
                                  +---------------------------------------+
                                  |             MyHomeStead.io            |
                                  |     (26 Distributed Subsystems)       |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |              DataHub-io               |
                                  |   (Universal Multi-Database Driver)   |
                                  +-------------------+-------------------+
                                                      |
                 +-----------------+------------------+-----------------+-----------------+
                 |                 |                  |                 |                 |
                 v                 v                  v                 v                 v
          [ PostgreSQL ]     [ InfluxDB ]       [ SQLite / ]      [ MariaDB / ]     [ Redis / ]
          [ TimescaleDB]     [ (v1 & v2)]       [  DuckDB  ]      [   MySQL   ]     [ Valkey  ]
          - Hypertables      - Fast line proto  - Embedded file   - HA standard     - In-memory
          - SQL Analytics    - Flux / InfluxQL  - Zero-cloud disk - Relational      - Fast cache
```

---

## 🔌 1. Database Driver Specifications & Connection URIs

Every add-on in the ecosystem supports a unified `database` block in its options configuration or routes through **DataHub-io**:

### 1.1 PostgreSQL & TimescaleDB (Recommended for Advanced Analytics)
* **Driver:** `asyncpg` / `SQLAlchemy`
* **Connection URI:**
  ```text
  postgresql://homestead_user:secret_password@192.168.1.50:5432/myhomestead
  ```
* **Best Used For:** Automated hypertables, continuous aggregations (daily power consumption, weekly crop water loss, long-term soil health trends).
* **Sample Automated DDL:**
  ```sql
  CREATE TABLE IF NOT EXISTS homestead_telemetry (
      time TIMESTAMPTZ NOT NULL,
      subsystem VARCHAR(32) NOT NULL,
      entity_id VARCHAR(64) NOT NULL,
      value DOUBLE PRECISION NOT NULL,
      unit VARCHAR(16),
      attributes JSONB
  );
  SELECT create_hypertable('homestead_telemetry', 'time', if_not_exists => TRUE);
  ```

---

### 1.2 InfluxDB (v2 & v1) (Fast IoT Time-Series)
* **Driver:** `influxdb-client` / HTTP Line Protocol
* **Connection Config (v2):**
  ```yaml
  database:
    type: "influxdb_v2"
    url: "http://192.168.1.50:8086"
    token: "!secret influx_token"
    org: "homestead"
    bucket: "myhomestead"
  ```
* **Connection Config (v1 Legacy):**
  ```yaml
  database:
    type: "influxdb_v1"
    host: "192.168.1.50"
    port: 8086
    database: "myhomestead"
    username: "homestead"
    password: "!secret influx_password"
  ```
* **Best Used For:** Native integration with Grafana dashboards, sub-second telemetry ingestion from solar inverters and 25kHz fan tachometers.

---

### 1.3 SQLite & DuckDB (Zero-Configuration, Local-First Embedded)
* **Driver:** `sqlite3` / `duckdb`
* **Connection URI:**
  ```text
  sqlite:////config/myhomestead/homestead_telemetry.db
  duckdb:////share/myhomestead/analytics.duckdb
  ```
* **Best Used For:** 100% out-of-the-box local storage running directly on the Home Assistant node's internal NVMe or SSD storage with **zero external servers to maintain**.

---

### 1.4 MariaDB & MySQL (Home Assistant Native Standard)
* **Driver:** `aiomysql` / `pymysql`
* **Connection URI:**
  ```text
  mysql+pymysql://homeassistant:password@core-mariadb:3306/homeassistant?charset=utf8mb4
  ```
* **Best Used For:** Co-locating telemetry with the standard Home Assistant Core MariaDB official add-on.

---

### 1.5 QuestDB & VictoriaMetrics (High-Throughput Ingestion)
* **Driver:** Influx Line Protocol (ILP) TCP / HTTP
* **Connection Endpoint:**
  ```text
  tcp://192.168.1.50:9009 (QuestDB ILP)
  http://192.168.1.50:8428/api/v1/write (VictoriaMetrics)
  ```
* **Best Used For:** High-frequency electrical logging (CT clamp waveforms, grid ripple, vibration analysis on well pumps).

---

### 1.6 Redis & Valkey (Real-time Cache & Pub/Sub Interlocks)
* **Driver:** `redis-py`
* **Connection URI:**
  ```text
  redis://:password@192.168.1.50:6379/0
  ```
* **Best Used For:** Microsecond inter-process synchronization between **Control-io** and distributed ESP32 nodes (e.g., instant kill switch broadcast on dry-run trip).

---

## 🛠️ 2. Universal Add-on Database Configuration Schema

Add this block into any add-on's configuration tab (or `options.json`) to stream directly to your database:

```yaml
database:
  enabled: true
  provider: "postgresql" # options: postgresql, influxdb_v2, sqlite, mariadb, questdb, redis
  uri: "postgresql://user:pass@192.168.1.50:5432/myhomestead"
  batch_size: 50
  flush_interval_seconds: 10
  export_retries: 3
  local_buffer_path: "/data/db_buffer.wal"
```

### Edge Write-Ahead Log (WAL) Buffering
If your external database server reboots, network switches fail, or maintenance is underway:
1. Every add-on buffers writes locally into an embedded SQLite Write-Ahead Log (`/data/db_buffer.wal`).
2. When the remote database reconnects, the backlog drains automatically without losing a single data point.
