# Project Name

## Getting Started

Follow the steps below to set up and run the project.

### Prerequisites
Make sure you have the following installed:
- Node.js
- npm
- Any other dependencies required for your project

## Setup Instructions

### 1. Clone the Repository
Navigate to the root folder of the GIT repository.

### 2. Start the Backend Server
Run the following command to start the backend server:
```sh
./build/run_server.sh
```

### 3. Start the Frontend Server
Once the backend server is running, start the frontend server:
```sh
cd src/frontend
./scripts/get_env_file.sh
npm install
npm run dev
```

### 4. Run all Backend Tests
To execute all the backend test cases, run:
```sh
./build/run_backend_testcases.sh
```

### 5. Run only a particular Backend Testcase file
To execute only a particular test file like test_addcustomer.py, run:
```sh
./build/run_backend_testcases.sh -f test_addcustomer.py
```

## Additional Notes
- Ensure all dependencies are installed before running the servers.
- Modify configuration files if required before running the setup.

Happy Coding! 🚀

