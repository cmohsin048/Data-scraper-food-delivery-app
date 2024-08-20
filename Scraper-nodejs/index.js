const express = require("express");
const { exec } = require("child_process");
const fs = require("fs");
const path = require("path");
const app = express();
const port = 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// Route to handle scraping requests
app.post("/scrape", (req, res) => {
  const { url } = req.body;

  if (!url) {
    return res.status(400).json({ error: "URL is required" });
  }

  // Define the path for the JSON file
  const outputFilePath = path.join(__dirname, "scraped_data.json");

  // Execute the Python script with the URL as an argument
  exec(`python scraper.py "${url}"`, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error executing script: ${error.message}`);
      return res.status(500).json({ error: "Failed to execute script" });
    }

    if (stderr) {
      console.error(`stderr: ${stderr}`);
      return res.status(500).json({ error: "Script encountered an error" });
    }

    // Read the JSON file and send it as a response
    fs.readFile(outputFilePath, "utf-8", (readError, data) => {
      if (readError) {
        console.error(`Error reading file: ${readError.message}`);
        return res.status(500).json({ error: "Failed to read JSON file" });
      }

      // Send the JSON data as the response
      res.setHeader("Content-Type", "application/json");
      res.send(data);
    });
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
