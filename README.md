# Project: PlanPilotpp

## Project Description
This project aims to provide an interactive web-based interface for visualizing planning problems using data from the [PlanPilot repository](https://github.com/abcorrea/planpilot). The goal is to enhance user interaction and understanding of planning spaces by offering graphical representations and interactivity with facets of the plans.

## Core Functions
- **Data Processing & Visualization**: The application will extract and process data from the PlanPilot repository and present it in a user-friendly format.
- **User Input & Interaction**: Users will be able to input their own planning problems, similar to how the existing Python script in PlanPilot processes input.
- **Graphical Representation**: The interface will feature visual elements to illustrate different facets of planning problems, allowing users to manipulate and explore plan spaces.
- **Faceted Navigation**: The frontend will support the essential `fasb` commands, enabling users to activate/deactivate facets and query plan space properties.

## Technological Specification
### Frontend
- **Framework**: Vue.js
- **Purpose**: Provides a responsive and interactive user interface to visualize and interact with planning data.

### Backend
- **Framework**: Flask (Python)
- **Purpose**: Acts as a bridge between the frontend and the PlanPilot repository, handling data processing and logic.

## Functional Features
- **Plan Input Support**: Users will be able to upload PDDL problem files and specify parameters.
- **Graphical Interaction**: Users will interact with plans and facets through a visual selection process instead of command-line inputs.
- **Dynamic Facet Activation**: Users can activate and deactivate facets via UI components to filter and explore plan options.
- **Graphical Representation**: The application will visually present the sequence of actions in the planning problem and showing how a solution is reached.

## Backend Setup
- The backend will run a Flask server that interacts with the PlanPilot repository.
- It will handle API requests from the frontend to execute planning operations.
- Data will be processed and returned in a format suitable for visualization.
