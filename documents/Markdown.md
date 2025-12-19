**To the Backend & Database Engineers:** This is **Part 1 of 15** of the Technical Implementation & Domain Specification. This document provides the complete, production-ready SQL schema for the Supabase PostgreSQL database. This schema is the foundational data model for the entire AIaaS platform.

# Tech Spec 1: Complete Database Schema

**Version:** 1.0 (Implementation-Ready) **Audience:** Backend Engineers, Database Administrators

## 1\. Schema Philosophy

*   **Normalization:** The schema is designed to be in Third Normal Form (3NF) to minimize data redundancy and improve data integrity.
*   **Scalability:** Indexes are strategically placed on foreign keys and frequently queried columns to ensure performance at scale.
*   **Security:** Row-Level Security (RLS) is enabled on all tables to ensure users can only access data they are permitted to see.
*   **Extensibility:** The use of JSONB for metadata and schemas allows for future flexibility without requiring database migrations.

## 2\. Complete SQL Schema

\-- Enable Row-Level Security for all tables

ALTER DEFAULT PRIVILEGES IN SCHEMA public ENABLE ROW LEVEL SECURITY;

\-- Create custom types for roles and statuses

CREATE TYPE user\_role AS ENUM ('designer', 'engineer', 'lead', 'hod', 'admin');

CREATE TYPE task\_status AS ENUM ('pending', 'in\_progress', 'awaiting\_review', 'awaiting\_clarification', 'completed', 'rejected');

CREATE TYPE deliverable\_type AS ENUM ('civil', 'structural', 'architectural');

\-- Main Tables

CREATE TABLE users (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

email TEXT UNIQUE NOT NULL,

full\_name TEXT NOT NULL,

role user\_role NOT NULL,

created\_at TIMESTAMPTZ DEFAULT now()

);

CREATE TABLE projects (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

name TEXT NOT NULL,

client\_name TEXT,

project\_code TEXT UNIQUE NOT NULL,

created\_at TIMESTAMPTZ DEFAULT now(),

\-- Foreign key to the user who created the project

created\_by UUID REFERENCES users(id)

);

CREATE TABLE project\_members (

project\_id UUID REFERENCES projects(id) ON DELETE CASCADE,

user\_id UUID REFERENCES users(id) ON DELETE CASCADE,

PRIMARY KEY (project\_id, user\_id)

);

CREATE TABLE deliverables (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

project\_id UUID REFERENCES projects(id) ON DELETE CASCADE,

name TEXT NOT NULL,

type deliverable\_type NOT NULL,

schema\_id UUID REFERENCES deliverable\_schemas(id),

created\_at TIMESTAMPTZ DEFAULT now()

);

CREATE TABLE tasks (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

deliverable\_id UUID REFERENCES deliverables(id) ON DELETE CASCADE,

assignee\_id UUID REFERENCES users(id),

status task\_status NOT NULL DEFAULT 'pending',

due\_date DATE,

created\_at TIMESTAMPTZ DEFAULT now(),

updated\_at TIMESTAMPTZ DEFAULT now()

);

CREATE TABLE task\_versions (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

task\_id UUID REFERENCES tasks(id) ON DELETE CASCADE,

version\_number INT NOT NULL,

input\_data JSONB,

output\_data JSONB,

risk\_score FLOAT,

created\_by UUID REFERENCES users(id),

created\_at TIMESTAMPTZ DEFAULT now(),

UNIQUE(task\_id, version\_number)

);

CREATE TABLE reviews (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

task\_version\_id UUID REFERENCES task\_versions(id) ON DELETE CASCADE,

reviewer\_id UUID REFERENCES users(id),

is\_approved BOOLEAN NOT NULL,

comments TEXT,

created\_at TIMESTAMPTZ DEFAULT now()

);

\-- Configuration & Knowledge Base Tables

CREATE TABLE deliverable\_schemas (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

name TEXT UNIQUE NOT NULL,

schema\_json JSONB NOT NULL -- Contains input\_schema, workflow\_steps, output\_schema, risk\_rules

);

CREATE TABLE knowledge\_chunks (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

source\_document TEXT,

chunk\_text TEXT NOT NULL,

metadata JSONB, -- Includes project\_id, deliverable\_type, etc.

embedding VECTOR(1536) -- Example dimension, adjust based on model

);

CREATE TABLE fine\_tuning\_dataset (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

input\_prompt TEXT NOT NULL,

correct\_output TEXT NOT NULL,

created\_at TIMESTAMPTZ DEFAULT now()

);

\-- Audit & Logging

CREATE TABLE audit\_log (

id BIGSERIAL PRIMARY KEY,

user\_id UUID REFERENCES users(id),

action TEXT NOT NULL, -- e.g., 'CREATE\_PROJECT', 'APPROVE\_REVIEW'

details JSONB,

timestamp TIMESTAMPTZ DEFAULT now()

);

\-- Indexes for performance

CREATE INDEX ON projects (created\_by);

CREATE INDEX ON deliverables (project\_id);

CREATE INDEX ON tasks (deliverable\_id, assignee\_id);

CREATE INDEX ON task\_versions (task\_id);

CREATE INDEX ON reviews (task\_version\_id, reviewer\_id);

CREATE INDEX ON knowledge\_chunks USING hnsw (embedding vector\_cosine\_ops); -- HNSW index for fast vector search

## 3\. Row-Level Security (RLS) Policies

Below are example RLS policies. These must be implemented for every table to enforce data access rules.

\-- Example: Users can only see projects they are a member of.

CREATE POLICY select\_project\_members ON projects

FOR SELECT USING (

id IN (SELECT project\_id FROM project\_members WHERE user\_id = auth.uid())

);

\-- Example: Users can only see tasks assigned to them or tasks in their projects if they are a lead/hod.

CREATE POLICY select\_tasks ON tasks

FOR SELECT USING (

assignee\_id = auth.uid() OR

(SELECT role FROM users WHERE id = auth.uid()) IN ('lead', 'hod') AND

deliverable\_id IN (SELECT id FROM deliverables WHERE project\_id IN (SELECT project\_id FROM project\_members WHERE user\_id = auth.uid()))

);

This schema provides a robust, secure, and scalable foundation for the AIaaS platform. All other system components will be built upon this data model.