graph TD
    subgraph Frontend
        A[Next.js/React Dashboard]
    end

    subgraph Backend
        B[Flask Server]
    end

    subgraph External Services
        C[Fitbit API]
    end

    A -->|Fetches sleep data| B
    B -->|Authenticates & fetches data| C
    C -->|Returns user data| B
    B -->|Sends processed data| A