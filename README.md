CSV Contacts Normalizer

Python utility to normalize contact data from CSV files.

Features
	•	Input CSV format: id;phone;dob
	•	Normalization:
	•	Phone numbers → E.164 (+971501234567)
	•	Dates of birth → ISO 8601 (YYYY-MM-DD)
	•	Invalid rows are skipped, reasons printed in summary
	•	Row-by-row processing (low memory usage)
	•	Docker support for easy run

Usage

Build Docker image

docker build -t csv-contacts-normalizer .

Run

docker run --rm -v "$PWD":/data csv-contacts-normalizer /data/input.csv

Output will be saved as normalized_contacts.csv in the same folder.

Example

Input (input.csv):

id;phone;dob
U001;058_510_8603;Apr-05-2004
U002;0380 67 123 45 67;2001-09-09

Output (normalized_contacts.csv):

id;phone;dob
U001;+971585108603;2004-04-05
U002;+380671234567;2001-09-09

Notes
	•	Ambiguous dates like 01/02/1990 are parsed as day-first unless the month > 12.
	•	Two-digit years use pivot 25 → 00–25 → 2000–2025, otherwise → 1900–1999.
