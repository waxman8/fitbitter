# Fitbitter Dashboard

This directory contains the source code for the Fitbitter dashboard, a [Next.js](https://nextjs.org/) application designed to visualize your Fitbit data. It uses the python app for its back-end, session and token handling etc. 

## Overview

The dashboard provides a user-friendly interface to view and analyze data retrieved from the Fitbit API via the main Python Flask application. It includes a visualization that mixes sleep stages with heart rate and showing most recent resting heart rate. You have to enter the date ranges.  
This reflects the metric I was most interested in: "heart rate below average resting heart rate during sleep".

## Getting Started

To run the dashboard locally, follow these steps:

0. **Ensure the python app is running**
   Follow the steps here [Main README](../README.md)

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
