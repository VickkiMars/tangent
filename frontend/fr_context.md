# Frontend Context (fr_context.md)

This document provides a summary of the frontend application for the `Tangent` project.

## Project Structure

The frontend is a standard React application built with Vite. The main source code is located in the `frontend/src` directory.

- **`main.jsx`**: The entry point of the application. It renders the `App` component.
- **`App.jsx`**: The root component that sets up the routing using `react-router-dom`.
- **`index.css`**: Global styles and Tailwind CSS imports.
- **`components/`**: Contains reusable components used throughout the application.
  - **`Layout.jsx`**: The main layout component that includes the `Navbar` and `Footer`.
  - **`Navbar.jsx`**: The navigation bar at the top of the page.
  - **`Footer.jsx`**: The footer at the bottom of the page.
  - **`TaskBoard.jsx`**: A complex component that displays a task board with threads and events.
- **`pages/`**: Contains the different pages of the application.
  - **`Landing.jsx`**: The landing page of the application.
  - **`Workspace.jsx`**: A page that displays the `TaskBoard` component, defaulting to a specific task.
  - **`TaskView.jsx`**: A page that displays the `TaskBoard` component.
  - **`History.jsx`**: A page for viewing history (not yet implemented).
  - **`Pricing.jsx`**: A page for pricing information (not yet implemented).
  - **`Features.jsx`**: A page for features information (not yet implemented).
  - **`Docs.jsx`**: A page for documentation (not yet implemented).

## Routing

The routing is handled by `react-router-dom` in `App.jsx`. The following routes are defined:

- `/`: `Landing`
- `/workspace`: `Workspace`
- `/tasks`: `TaskView`
- `/history`: `History`
- `/pricing`: `Pricing`
- `/features`: `Features`
- `/docs`: `Docs`

## State Management

There is no dedicated state management library like Redux or Zustand. State is managed locally within components using `useState`. The `TaskBoard` component has a significant amount of local state to manage the mock data and UI interactions.

## Styling

The project uses Tailwind CSS for styling. The configuration is in `tailwind.config.js`. Global styles and Tailwind imports are in `index.css`.

## Key Components

- **`TaskBoard.jsx`**: This is the most complex component in the application. It simulates a task board with a list of threads and a timeline of events for the selected thread. It uses mock data for now. It has a three-column layout: a list of threads, a timeline of events, and an inspector to view the details of a selected event.
- **`Layout.jsx`**: This component provides the basic structure of the application, including the header, footer, and background elements.
- **`Navbar.jsx`**: The navigation bar with links to different pages. It uses `framer-motion` for animations.

## Functionality

The application is currently a mock-up of a task management system for AI agents. The `TaskBoard` component is the core of the application, and it is where the user can see the status of different tasks and the events that occurred during their execution.

## Next Steps

Now that I have a good understanding of the existing frontend, I can proceed with implementing the chat UI. I will create a new `Chat.jsx` page and add a route for it in `App.jsx`. I will also add a link to the chat page in the `Navbar`.
