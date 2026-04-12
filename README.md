# Finbank API

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery" />
  <img src="https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" alt="RabbitMQ" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>

A robust, asynchronous RESTful API for a digital banking platform, built with modern Python technologies. 
Finbank API provides core banking functionalities including user management, bank account operations, transaction processing, and background task processing for reports like PDF account statements.

## 🚀 Key Features

*   **User & Authentication Management:** Secure user registration, authentication (JWT), and profile management with Argon2 password hashing.
*   **Bank Accounts:** Creation and management of bank accounts.
*   **Transactions:** Comprehensive transaction processing (deposits, withdrawals, internal transfers) with ACID compliance. Real-time balance calculations and currency conversion handling.
*   **Next of Kin Management:** Securely store and manage next of kin details for users.
*   **Asynchronous Processing:** Background tasks driven by Celery, RabbitMQ, and Redis to handle non-blocking operations like automated PDF statement generation and email notifications.
*   **Local Development with Docker:** Fully containerized multi-service architecture including the API, Postgres database, Celery workers/beat, Redis cache, RabbitMQ broker, Mailpit (for local email testing), and Traefik (reverse proxy).

## 🛠 Tech Stack

**Backend Framework:**
*   [FastAPI](https://fastapi.tiangolo.com/) (Async API framework)
*   [SQLModel](https://sqlmodel.tiangolo.com/) & [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
*   [Alembic](https://alembic.sqlalchemy.org/) (Database migrations)
*   [Pydantic](https://docs.pydantic.dev/) v2 (Data validation)

**Infrastructure & Databases:**
*   [PostgreSQL](https://www.postgresql.org/) (Primary Relational Database)
*   [Redis](https://redis.io/) (Cache and Celery backend)
*   [RabbitMQ](https://www.rabbitmq.com/) (Message Broker)

**Background Tasks:**
*   [Celery](https://docs.celeryq.dev/) (Distributed Task Queue)
*   [Flower](https://flower.readthedocs.io/) (Celery Monitoring)

**DevOps & Tooling:**
*   [Docker](https://www.docker.com/) & Docker Compose
*   [Traefik](https://traefik.io/) (Reverse Proxy)
*   [Mailpit](https://mailpit.axllent.org/) (Local Email Testing)

## ⚙️ Getting Started

### Prerequisites

*   [Docker Engine](https://docs.docker.com/engine/install/) & [Docker Compose](https://docs.docker.com/compose/install/)
*   Python 3.10+ (for local, non-containerized setup)
*   Make (optional, for convenience commands)

### Local Setup (Using Docker)

The easiest way to run the Finbank API locally is by using the provided `local.yml` Docker Compose configuration, which brings up all required services routing optimally through Traefik.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/Finbank_API.git
    cd Finbank_API/src
    ```

2.  **Environment Variables:**
    Ensure you have your environment variables set up in the `.envs/` directory. Typically, you'll need `.envs/.env.local`. 
    *(If there's an `.env.example`, copy it to `.env.local` and populate the required fields).*

3.  **Build and Start the Services:**
    ```bash
    docker compose -f local.yml up --build -d
    ```

4.  **Database Migrations:**
    Once the containers are running, apply the Alembic database migrations:
    ```bash
    docker compose -f local.yml run --rm api alembic upgrade head
    ```

This will start the following services (mapped via Traefik rules):
*   **API:** `http://api.localhost` or `http://localhost:8000`
*   **Postgres Database:** `localhost:5433`
*   **RabbitMQ Management:** `http://rabbitmq.localhost` or `http://localhost:15672`
*   **Flower (Celery Monitor):** `http://flower.localhost` or `http://localhost:5555`
*   **Mailpit UI:** `http://localhost:8025`

### Stopping the Services

To stop and remove networks/containers:
```bash
docker compose -f local.yml down
```

## 📚 API Documentation

FastAPI automatically generates interactive API documentation. Once the API is running locally via Docker, access the documentation at:

*   **Swagger UI:** `http://api.localhost/docs` or `http://localhost:8000/docs`
*   **ReDoc:** `http://api.localhost/redoc` or `http://localhost:8000/redoc`

## 🗄 Project Structure

```text
src/
├── alembic.ini             # Alembic configuration
├── local.yml               # Docker Compose file for local environment
├── Makefile                # Convenience helper commands
├── backend/
│   ├── app/                # Main application code
│   │   ├── api/            # API Routers and endpoints
│   │   ├── auth/           # Authentication logic
│   │   ├── bank_account/   # Bank Account domain
│   │   ├── core/           # Core configurations and background tasks
│   │   ├── next_of_kin/    # Next of Kin domain
│   │   ├── transaction/    # Transaction domain
│   │   └── user_profile/   # User Profile domain
│   ├── docker/             # Dockerfiles (Local)
│   └── requirements.txt    # Python dependencies
└── migrations/             # Alembic database migrate scripts
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
