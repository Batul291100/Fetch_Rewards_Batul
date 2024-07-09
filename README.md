# Fetch Rewards Data Engineering Take Home

## Overview
This project involves building a small application that reads JSON data from an AWS SQS Queue, transforms this data by masking personal identifiable information (PII), and then writes the transformed data to a Postgres database. The application runs in a local Docker environment, ensuring all dependencies are contained and no external AWS account is required.

## Prerequisites
- **Docker**: For creating and managing the application environment. [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: For defining and running multi-container Docker applications. [Install Docker Compose](https://docs.docker.com/compose/install/)
- **Python**: Required for running the ETL script. [Install Python](https://www.python.org/downloads/)
- **Psql**: For interacting with the Postgres database. [Install Psql](https://www.postgresql.org/download/)

Ensure these are installed on your machine before proceeding.

## Setup
1. **Clone the Repository**: Clone this repository to your local machine.
2. **Environment Setup**: Navigate to the project directory and run the following commands to set up the environment:

```
make pip-install # Install Python dependencies
make aws-configure # Configure AWS CLI (local version)
```

3. **Start Services**:

```
make start  # Starts the Docker containers
```

4. **Perform ETL Process**: Run the ETL process to read from the SQS queue, mask PII, and write to the Postgres database:

```
make perform-etl
```

5. **Stop the Application**: To stop and remove the Docker containers:

```
make stop
```

6. **Clean up Docker**: To clean up unused Docker data:

```
make clean
```

## Testing

** Reading Message from Queue: 

```
awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue
```

** Verify Database Records:

```
psql -d postgres -U postgres -p 5432 -h localhost -W
SELECT * FROM user_logins;
```

