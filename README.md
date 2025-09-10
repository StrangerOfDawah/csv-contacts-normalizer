# CSV Contacts Normalizer

Utility for normalizing contact data stored in CSV files.

## Features
- Input format: `id;phone;dob`
- Normalizes:
  - **Phone numbers** → E.164 standard (e.g., `+971501234567`)
  - **Dates of birth** → ISO 8601 (`YYYY-MM-DD`)
- Invalid rows are skipped with reasons reported
- Streaming (row-by-row) processing → handles large files with low memory usage
- Docker support for reproducible runs

## Usage

### Build
```bash
docker build -t csv-contacts-normalizer .
