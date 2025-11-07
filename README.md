# DBurst — AI Frontend Builder (Phase 1)

This project is an **AI-powered frontend builder** that generates Frontend UI components from natural language prompts.  
The stack uses **Django (REST API)** for backend + **React (Vite)** for the frontend.  

Phase 1 focuses on **project setup, authentication, base UI, and API foundations**.

---

## 🏗️ Tech Stack

| Layer | Technology |
|------|------------|
| Frontend | React (Vite) + TypeScript + TailwindCSS |
| Backend | Django + Django REST Framework |
| Auth (Phase 1) | OAuth (Google & GitHub), JWT |
| Database | PostgreSQL |
| Caching | Redis (planned for Phase 2) |
| Deployment | (TBD - Dev currently local Docker) |

---

## 📂 Project Structure

```
/project-root
│
├── backend/            # Django API
│   ├── manage.py
│   ├── core/           # main project config
│   └── apps/           # modular backend apps
│
├── frontend/           # React App
│   ├── src/
│   ├── public/
│   └── vite.config.ts
│
├── infra/ (optional)   # docker-compose, deployment scripts
│
└── README.md
```

API will run at:  
```
http://127.0.0.1:8000/
```

---

Frontend will run at:
```
http://localhost:5173/
```

---

## 🔐 Authentication (Phase 1 Target)

- Login via **Google or GitHub**
- Backend generates **JWT access + refresh tokens**
- Frontend stores tokens securely (HttpOnly or local secure storage)
- Protected routes require authentication

---

## 🎯 Phase 1 Deliverables

| Feature | Status |
|--------|--------|
| Monorepo Setup (frontend + backend) | ✅ In Progress |
| Basic UI Layout (header, dashboard skeleton) | ✅ In Progress |
| OAuth Login (Google & GitHub) | 🔄 Planned |
| JWT Security Layer | 🔄 Planned |
| DB Setup (Postgres Users table) | ✅ Done |
| API Base Routes & Project Model | ✅ In Progress |

---
