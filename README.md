# vinyl-recommender

An AI-powered desktop agent that analyzes whole-album audio features to ensure vinyl purchases are "skip-free" and align with the user's personal taste.

See [concept.md](concept.md) for a detailed breakdown of the application's features, logic, and architecture.

## Getting Started

Follow these steps to get your development environment set up and running.

### Prerequisites

Based on the **Python 3.12 / Vue.js 3** stack, you will need the following tools installed on your system:

- **Git:** For version control.
- **Python 3.12+:** The backend runtime.
- **Node.js v18+:** For the Vite/Vue frontend development.
- **FFmpeg:** Required by Librosa for audio processing and spectral analysis.
- **uv:** (Recommended) The high-performance Python package installer used by the `go.bat` script.

### Clone and Initialize the Repository

First, get the code. Then, it's highly recommended to initialize it as your own Git repository.

```bash
git init
git add .
git commit -m "Initial commit from boilerplate"
```

### Install Dependencies & Run

This project uses a `go.bat` script to streamline common tasks.

1. **Frontend Setup:**
   Navigate to the frontend directory (usually `frontend/`) and install Node dependencies:
   ```bash
   npm install
   ```

2. **Backend & App Run:**
   To create the virtual environment, install Python dependencies, and run the application, execute:

```bash
go.bat
```

**What this does:**
- It automatically creates a virtual environment (`.venv`) using `uv`.
- It installs all dependencies from `requirements.txt`.
- It launches the `pywebview` window pointing to your application entry point.

Once running:
- The Python bridge will be active for communication between Vue and Librosa.
- The UI will be rendered in a native desktop window.

See the `go.bat` script for other available commands like `build`, `f` (freeze), or `r` (release).