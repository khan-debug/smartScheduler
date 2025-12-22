# Smart Scheduler

## Purpose

Smart Scheduler is a web application designed to help educational institutions manage and schedule their classes, faculty, and rooms. It provides a simple interface for administrators to manage the school's resources and for teachers to view their schedules.

## How it works

The application is built with Flask, a Python web framework. The frontend is built with HTML, CSS, and JavaScript.

### Login

The application has two roles: `admin` and `teacher`.

*   **Admin:**
    *   Username: `admin`
    *   Password: `0880`
*   **Teacher:**
    *   Username: Any 5-digit number (e.g., `12345`)
    *   Password: `0770` (this is a temporary password until the teacher registration feature is implemented)

The login page is the main entry point of the application. After successful login, the user is redirected to their respective dashboard.

*   Admins are redirected to the Admin Panel, where they can manage faculty, courses, and rooms.
*   Teachers are redirected to the Teacher View, where they can view their schedule.
