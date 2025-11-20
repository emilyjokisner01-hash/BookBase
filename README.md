# BookBase
BookBase is a full stack web-application designed to help users to organize and manage their personal library. Features we have worked on in this project are as follows: adding and editing book entries, searching and filtering books, CSV import and export, and ISBN duplicate checking.

# Table of Contents

- [Project Title](#project-title)
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)

# Installation

To install BookBase on your computer, you can clone the repository from github. 
As a contributor, you can copy the https code from the github website and pasting it alongside the following line of code in your computer or IDE terminal. 
"git clone [Repository Git HTTPS code]". This adds all of the necessary files to your computer or IDE. 
Then you can use flask commands to run the program in your web browser.
If not already done, you will need to download and install mysql on your computer. In doing this, you will set up a root password.
Once you ensure that both mysql and also Flask are installed on your computer, you can use the terminal on your IDE to enter the following commands. 
First, ensure that you are in the correct folder by typing the bash command "ls" and making sure the necessary files for the project from Github are listed.
The first command is "mysql -u root -p". This will ask you to enter your root password. The next command is "source database_setup.sql". 
Then exit mysql using "exit," and use "python app.py" and "flask run" to compile and run the project. Click on the hyperlink to open BookBase.

[(Back to top)](#table-of-contents)

# Usage
Once you have BookBase running locally, you will be able to use the following features: 

Add Books: 

Users can add any new book by entering: 
* Title 
* Author
* Genre
* Publication Year 
* Rating
* ISBN

Search Through Catalog:

Search by Keywords in:
* Title 
* Author 
* Genre 

Filter Through Catalog

Filter the books by:
* Author
* Genre
* Rating
* Year

CSV Import

Upload a .csv file to add multiple books at once.

CSV Export

Export search/filter results or the entire catalog into a csv that can be opened into Microsoft Excel.

[(Back to top)](#table-of-contents)

# Development

This project was developed using a Git Hub Repository housing python, HTML, and SQL files. Python served as the connecting langauge between the backend database (SQL) and the front end GUI design (HTML). Filtering and querying was completed using python FLASK connected to the database. 
This development was completed by Emily Kisner, Sheetal Bullapur Siddesh, and Samyuktha Gandi as part of ESS Development. We hope you enjoy our project!
[(Back to top)](#table-of-contents)
