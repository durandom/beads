# Tasks: User Authentication

**Input**: Design documents from `/specs/001-user-auth/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

- [ ] T003 Setup database schema in src/db/schema.py
- [ ] T004 [P] Implement base models in src/models/base.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Login Flow (Priority: P1)

**Goal**: Users can authenticate with email and password

- [ ] T005 [US1] Create User model in src/models/user.py
- [ ] T006 [US1] Implement AuthService in src/services/auth.py (depends on T005)
- [x] T007 [P] [US1] Add login endpoint in src/api/auth.py (depends on T006)

**Checkpoint**: User Story 1 should be fully functional

---

## Phase 4: User Story 2 - Registration (Priority: P2)

**Goal**: New users can create accounts

- [ ] T008 [P] [US2] Add registration endpoint in src/api/auth.py
- [ ] T009 [US2] Implement email validation in src/services/email.py (depends on T003)
