# Security Policy & Architecture Documentation

## Overview

The Career Intelligence platform processes sensitive professional profiles, resume documents, and recruiter talent data. This document outlines the application's threat model, defensive security architecture, implemented mitigations, and known operational limitations.

---

## 1. Threats

The platform's threat model identifies several primary attack vectors and security risks:

### 1.1 Malicious File Uploads & Disguised Executables
- **Threat:** Attackers upload malicious binaries (e.g., Windows PE `.exe`, Linux ELF, Mach-O binaries, PHP/shell scripts) disguised with `.pdf` or `.docx` extensions to compromise the server or trigger parser exploits.
- **Impact:** Remote code execution (RCE), parser crashes, or server compromise.

### 1.2 Memory Exhaustion & Denial of Service (DoS)
- **Threat:** Attackers upload multi-gigabyte files or flood document parsing endpoints with concurrent requests to exhaust server RAM and CPU.
- **Impact:** Service outage, application crash, and denial of service for legitimate candidates and recruiters.

### 1.3 Path Traversal & Filename Injection
- **Threat:** Manipulated filenames containing directory traversal characters (e.g., `../../../../etc/passwd`, `..\..\windows\system32`) or null bytes (`\x00`) aimed at writing to or reading from unauthorized filesystem paths.
- **Impact:** Unauthorized file overwrite, data leakage, or arbitrary file access.

### 1.4 SQL Injection (SQLi)
- **Threat:** Malicious SQL syntax in candidate emails, names, or search parameters (e.g., `' OR '1'='1' --`) attempting to bypass authentication or extract database tables.
- **Impact:** Unauthorized access to user accounts, profile data, or database tampering.

### 1.5 Cross-Site Scripting (XSS) & Protocol Injection
- **Threat:** Malicious payload strings embedded in resume text, candidate names, or course links (e.g., `<script>`, `javascript:...`) executed in the recruiter's or candidate's browser.
- **Impact:** Session hijacking, credential theft, or unauthorized client actions.

### 1.6 CORS Misconfiguration
- **Threat:** Overly permissive Cross-Origin Resource Sharing (CORS) policies (such as wildcard `*` paired with `allow_credentials=True`), permitting unauthorized external domains to make authenticated requests.
- **Impact:** Cross-site request forgery and unauthorized data extraction.

### 1.7 Sensitive Data Exposure & PII Leakage
- **Threat:** Accidental storage, logging, or API reflection of raw personal identifiable information (PII) including credit card numbers, Indian Aadhaar numbers, PAN cards, US SSNs, passwords, and API keys.
- **Impact:** Privacy violation, regulatory non-compliance (DPDP Act, GDPR), and identity theft.

### 1.8 API Internal Error & Stack Trace Leakage
- **Threat:** Unhandled server exceptions returning raw Python stack traces, local filesystem paths, or internal library versions to API consumers.
- **Impact:** Reconnaissance aid for attackers to tailor exploits against specific library vulnerabilities.

---

## 2. Mitigations Implemented

| Security Dimension | Threat | Mitigation Implemented |
|---|---|---|
| **File Storage** | Resume Retention & Leaks | **Zero Permanent Storage**: All resumes are parsed strictly in-memory using stream bytes (`io.BytesIO`). No temporary or permanent files are written to disk. |
| **File Size Limits** | Memory Exhaustion DoS | **Streaming Chunk Cutoff**: File uploads are read in 64 KB chunks up to a strict **10 MB limit** (`MAX_FILE_SIZE_BYTES`). Uploads exceeding 10 MB are aborted immediately, returning HTTP 413 without loading the rest of the stream into RAM. |
| **File Types & Magic Bytes** | Disguised Binaries | **Multi-Layer Validation**: Only `.pdf`, `.docx`, and `.txt` are permitted. Magic bytes (file signatures) are inspected: PDF must start with `%PDF-`, DOCX must start with `PK\x03\x04`, and known binary headers (`MZ`, `\x7fELF`, Mach-O) are strictly rejected. |
| **Filename Sanitization** | Path Traversal | **`sanitize_filename`**: Normalizes path separators (`\` to `/`), extracts pure basenames (`os.path.basename`), strips `..`, null bytes, control characters, and hidden file prefixes, enforcing a 100-character maximum length. |
| **Database Access** | SQL Injection | **SQLAlchemy ORM**: All database interactions in `UserRepository`, `AnalysisRepository`, etc., use parameterized ORM queries (`select(Model).where(...)`), completely eliminating raw SQL string concatenation. |
| **CORS Policy** | Unauthorized Cross-Origin Access | **Strict Origin Whitelist**: Origins are restricted to explicit origins (`http://localhost:3000`, `http://127.0.0.1:3000`). If a wildcard `*` is configured, `allow_credentials` is automatically disabled per CORS security standards. |
| **HTTP Headers** | Clickjacking & MIME Sniffing | **Security Middleware**: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Permissions-Policy`. |
| **Rate Limiting** | Endpoint Flooding & Brute Force | **Sliding Window Rate Limiter**: Thread-safe in-memory sliding window limiter protecting `/api/v1/documents/parse` (25 req/min) and general endpoints. Triggers HTTP 429 with `Retry-After` header. |
| **PII & Credential Masking** | PII & Secret Exposure | **`sanitize_sensitive_information`**: Automatically scrubs 16-digit credit cards, 12-digit Indian Aadhaar numbers, Indian PAN cards, US SSNs, passwords, and API keys before returning extracted text. |
| **Logging Security** | Secret & Resume Dumps in Logs | **`SecurityRedactionFilter`**: Intercepts all log records to redact passwords, tokens, API keys, and sensitive PII. Large raw resume text dumps (>1000 characters) are truncated to prevent log storage of private profiles. |
| **Error Handling** | Information Disclosure | **Sanitized API Errors**: Unhandled internal exceptions return generic, user-friendly error messages without leaking tracebacks or server paths. |
| **Frontend Links** | Client-Side XSS | **Safe URL Protocol Validation**: External learning resources and course links are validated to ensure only `http://` and `https://` protocols are rendered as clickable links, neutralizing `javascript:` injection. |

---

## 3. Known Limitations & Operational Guidance

1. **In-Memory Rate Limiting Scope**
   - *Limitation:* The built-in sliding-window rate limiter stores state in process memory.
   - *Operational Guidance:* When scaling horizontally across multiple container replicas or serverless workers, configure a centralized rate-limiting store (such as Redis or an API gateway like Kong / AWS API Gateway) to maintain shared global quotas.

2. **OCR for Scanned Document Images**
   - *Limitation:* Scanned image-only PDFs (containing no selectable text stream) are rejected with a corrupted/empty document notice rather than being passed to external OCR tools.
   - *Operational Guidance:* This intentional design choice prevents unbounded CPU and GPU utilization associated with OCR engines (e.g. Tesseract) during standard web request lifecycles. Candidates are advised to upload text-based PDF or DOCX resumes.

3. **Transport Layer Security (TLS)**
   - *Limitation:* The FastAPI application runs an HTTP server directly.
   - *Operational Guidance:* In production deployments, TLS/HTTPS termination must be managed by an edge reverse proxy (such as Nginx, Caddy, Cloudflare, or an AWS Application Load Balancer) with HTTP-to-HTTPS redirection and HSTS headers.

4. **Database Encryption at Rest**
   - *Limitation:* SQLite is used for local development and self-contained deployments.
   - *Operational Guidance:* Production environments should utilize managed PostgreSQL with volume-level encryption at rest (e.g. AWS RDS AES-256 or GCP Cloud SQL) and SSL connections (`sslmode=require`).

5. **Human-in-the-Loop Decision Support**
   - *Limitation:* Career match scores and skill extraction are decision-support indicators, not automated legal or employment determinations.
   - *Operational Guidance:* Recruiters must review candidate evidence snippets directly and conduct human interviews. All platform views display the mandated system disclaimer:
     > *"Career Intelligence provides decision support based on the available profile and dataset. It does not guarantee employment, hiring outcomes or career success."*
