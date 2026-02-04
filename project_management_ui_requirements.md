# Project Management UI for ListProjects.vue

## 1. Overview

The goal is to adapt the existing `ListProjects.vue` component to support two different UI modes:

1.  **Case Management View (Existing):** This is the current implementation, which is tailored for clinical use cases and displays rich clinical information.
2.  **Project Management View (New):** This new view will be designed for research-oriented use cases. It will present projects in a more hierarchical, folder-like structure, abstracting away the clinical-specific details.

The user should be able to switch between these two views easily.

## 2. Conceptual Mapping

To implement the Project Management view, we will use the existing data models but present them differently. The mapping is as follows:

- **`Project`** will be conceptually treated as a **Folder**. It represents a main research project or a collection of related studies.
- **`Image Group`** will be conceptually treated as a **Sub-folder**. It represents a specific sub-project or experiment within a larger research folder.

## 3. Key Requirements

- **View-Specific UI:** The component should render a different layout and set of information depending on the selected view (Case Management vs. Project Management).
- **Component Reusability:** As much of the existing logic and sub-components as possible should be reused to implement the new view.
- **Data Model Consistency:** No changes should be made to the underlying data models (`Project`, `Image Group`, etc.). The changes should be purely presentational.
- **Future-Proofing:** The implementation should allow for easy switching between the two views, perhaps with a toggle button in the UI.

## 4. UI Layout and Design for Project Management View

The new view will be a two-column layout, similar to a desktop file explorer.

### 4.1. Left Column: File Tree

-   **Structure:** This column will display a hierarchical tree of projects and their associated image groups.
    -   **Level 1:** Folders (representing `Projects`).
    -   **Level 2:** Sub-folders (representing `Image Groups`).
-   **Hierarchy:** The tree will have a maximum depth of two levels.
-   **Context Menu (Right-click):**
    -   **On a Folder (`Project`):** A menu item to "Add Sub-folder" will be available. This action will create a new `Image Group` within the selected `Project`.
    -   **On a Sub-folder (`Image Group`):** Menu items for "Rename" and "Delete" will be available. The option to add another level of sub-folders will be disabled or hidden.

### 4.2. Right Column: Content Display

-   **Content:** This area will display the contents of the folder or sub-folder selected in the left-hand tree.
-   **Display Format:** The content will be displayed as a grid of cards. The visual style of these cards can be based on the existing `ProjectDetails` component for consistency.
-   **Content Representation:**
    -   When a Level 1 Folder (`Project`) is selected, the right-hand view will display cards for all its immediate children (both `Images` and `Image Groups`).
        -   Cards representing `Images` should display an image thumbnail.
        -   Cards representing `Image Groups` (sub-folders) should display a folder icon.
    -   When a Level 2 Sub-folder (`Image Group`) is selected, the right-hand view will display cards for all the images within that group, showing their thumbnails.
-   **Actions:** A set of action buttons will be displayed in the top-right corner of this content area. These actions will operate on the currently selected folder/sub-folder.
    -   Add Image
    -   Rename
    -   Share
    -   Create Folder (Image Group)

## 5. Next Steps

-   Proceed with the implementation of the new Project Management view based on these requirements.
-   Create a mechanism (e.g., a toggle switch) to alternate between the "Case Management" and "Project Management" views.

## 6. Progress

**2024-07-26:**

The initial implementation of the Project Management view is complete. The following provides a summary of the implementation details:

### Component Architecture

A modular component architecture was adopted to create the new view:

-   **`ProjectViewSwitcher.vue`**: The top-level component that renders a toggle to switch between the "Case Management" (`ListProjects.vue`) and "Project Management" (`ProjectManagement.vue`) views. It is registered in the main router (`routes.js`).
-   **`ProjectManagement.vue`**: The main component for the Project Management view. It implements the two-column layout and acts as a central controller for its child components. It manages all modals and the state of the selected item.
-   **`ProjectTree.vue`**: A component for the left column that displays the hierarchical folder tree of projects and image groups. It emits events to the parent (`ProjectManagement.vue`) when an item is selected or a context menu action is triggered.
-   **`ProjectContentDisplay.vue`**: A component for the right column that displays the content of the selected item. It receives the selected item as a prop and displays the corresponding images and image groups in a tiled layout. It emits events for actions like "Add Image", "Rename", and "Share".
-   **Modal Components**: Reusable modal components (`AddImageGroupModal.vue`, `RenameModal.vue`) were created for user input. Existing modals (`AddImageModal.vue`, `ShareProjectModal.vue`) were reused.

### Communication and Data Flow

-   **Event-Based Communication**: Child components communicate with the parent `ProjectManagement.vue` component using events. For example, `ProjectTree.vue` emits an `add-subfolder` event, and `ProjectContentDisplay.vue` emits an `add-image` event. This keeps the child components decoupled and reusable.
-   **Centralized State Management**: `ProjectManagement.vue` manages the application state for the Project Management view, including the currently selected item and the visibility of modals. This centralized approach simplifies state management and ensures a single source of truth.
-   **Prop-Based Data Passing**: Data is passed down from parent to child components using props. For example, `ProjectManagement.vue` passes the `selectedItem` and `selectedProject` to `ProjectContentDisplay.vue`.

### Reusability and Consistency

-   **Component Reuse**: Existing components like `ImagePreview.vue` (via a new `ImageCard.vue` wrapper) and `CytomineModal.vue` were reused to maintain consistency with the existing UI and reduce development time.
-   **Styling**: All new components were styled using the project's existing SASS variables and classes, ensuring they adhere to the Nord theme and the overall design system.

### Key Functionalities Implemented

-   **Hierarchical Tree View**: A collapsible tree view with folder icons.
-   **Context Menu**: A right-click context menu on tree items with "Add Sub-folder", "Rename", and "Delete" actions.
-   **Tiled Content Display**: A responsive tiled layout for displaying images and image groups.
-   **Functional Action Buttons**: All action buttons in the content display area are fully functional.
-   **Modal Integration**: All modals for user interaction are implemented and correctly integrated.

### Bug Fixes

-   Resolved issues with modal positioning and closing by correctly using the project's custom `CytomineModal.vue` component and ensuring proper event handling and prop management.