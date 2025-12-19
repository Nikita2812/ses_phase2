**To the Backend & Frontend Engineers:** This is **Part 2 of 15** of the Technical Implementation & Domain Specification. This document provides the complete API specifications in OpenAPI 3.0 format. This defines the contract between the frontend and backend, ensuring seamless communication.

# Tech Spec 2: Complete API Specifications

**Version:** 1.0 (Implementation-Ready) **Audience:** Backend Engineers, Frontend Engineers

## 1\. API Philosophy

*   **RESTful Principles:** The API follows RESTful design principles, using standard HTTP methods (GET, POST, PUT, DELETE) and status codes.
*   **Stateless:** All requests are stateless; the server does not store client session information.
*   **Authentication:** All endpoints (except /auth/login) are protected and require a valid JWT in the Authorization header.
*   **Versioning:** The API is versioned via the URL (/api/v1/...) to allow for future iterations without breaking existing clients.

## 2\. OpenAPI 3.0 Specification

openapi: 3.0.0

info:

title: CSA AIaaS API

version: 1.0.0

servers:

\- url: /api/v1

paths:

/auth/login:

post:

summary: User login

requestBody:

required: true

content:

application/json:

schema:

type: object

properties:

email: { type: string }

password: { type: string }

responses:

200:

description: Login successful

content:

application/json:

schema:

type: object

properties:

token: { type: string }

/projects:

get:

summary: Get all projects for the current user

responses:

200:

description: A list of projects

content:

application/json:

schema:

type: array

items:

$ref: '#/components/schemas/Project'

post:

summary: Create a new project

requestBody:

required: true

content:

application/json:

schema:

$ref: '#/components/schemas/NewProject'

responses:

201:

description: Project created

content:

application/json:

schema:

$ref: '#/components/schemas/Project'

/projects/{projectId}:

get:

summary: Get a single project by ID

parameters:

\- name: projectId

in: path

required: true

schema:

type: string

format: uuid

responses:

200:

description: Project details

content:

application/json:

schema:

$ref: '#/components/schemas/Project'

/projects/{projectId}/tasks:

get:

summary: Get all tasks for a project

parameters:

\- name: projectId

in: path

required: true

schema:

type: string

format: uuid

responses:

200:

description: A list of tasks

content:

application/json:

schema:

type: array

items:

$ref: '#/components/schemas/Task'

/tasks/{taskId}/review:

post:

summary: Submit a review for a task version

parameters:

\- name: taskId

in: path

required: true

schema:

type: string

format: uuid

requestBody:

required: true

content:

application/json:

schema:

$ref: '#/components/schemas/NewReview'

responses:

201:

description: Review submitted

/chat:

post:

summary: Send a message to the conversational AI

requestBody:

required: true

content:

application/json:

schema:

type: object

properties:

message: { type: string }

project\_context\_id: { type: string, format: uuid }

responses:

200:

description: AI response

content:

application/json:

schema:

type: object

properties:

response: { type: string }

sources: { type: array, items: { type: string } }

components:

schemas:

Project:

type: object

properties:

id: { type: string, format: uuid }

name: { type: string }

client\_name: { type: string }

project\_code: { type: string }

created\_at: { type: string, format: date-time }

NewProject:

type: object

properties:

name: { type: string }

client\_name: { type: string }

project\_code: { type: string }

Task:

type: object

properties:

id: { type: string, format: uuid }

deliverable\_id: { type: string, format: uuid }

assignee\_id: { type: string, format: uuid }

status: { type: string, enum: \[pending, in\_progress, awaiting\_review, completed, rejected\] }

due\_date: { type: string, format: date }

NewReview:

type: object

properties:

task\_version\_id: { type: string, format: uuid }

is\_approved: { type: boolean }

comments: { type: string }

security:

\- bearerAuth: \[\]

components:

securitySchemes:

bearerAuth:

type: http

scheme: bearer

bearerFormat: JWT

This specification provides a clear and unambiguous contract for all frontend-backend communication. The backend team will implement these endpoints, and the frontend team will consume them.