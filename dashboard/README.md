# Fitbitter Dashboard

This directory contains the source code for the Fitbitter dashboard, a [Next.js](https://nextjs.org/) application designed to visualize your Fitbit data.

## Overview

The dashboard provides a user-friendly interface to view and analyze data retrieved from the Fitbit API via the main Python Flask application. It includes visualizations for various metrics such as sleep patterns, heart rate, and more.

## Getting Started

To run the dashboard locally, follow these steps:

1.  **Navigate to the dashboard directory:**
    ```bash
    cd dashboard
    ```

2.  **Install dependencies:**
    Make sure you have [Node.js](https://nodejs.org/) installed. Then, run the following command to install the necessary packages.
    ```bash
    npm install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    ```

4.  **View the dashboard:**
    Open [http://localhost:3000](http://localhost:3000) in your web browser to see the application.

## Project Structure

-   `src/app/`: Contains the main pages and layouts of the application.
-   `src/app/dashboard/`: The primary page for data visualization.
-   `src/components/`: Reusable React components used throughout the dashboard (e.g., charts, UI elements).
-   `public/`: Static assets like images and icons.
