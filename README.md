# A Web page to facilitate the finding of recycling public spaces in Chile.
#### Video Demo:  <URL HERE>
#### Description: 

This project goal is to make available to the general public from the country of Chile a web page to allow them to search up all the recycling facilities (a place set up by the local government where people can go and leave recyclable materials) near to where they live. The way this is accomplished is by implementing a database with general information about a recycling facility hosted in a server that the users can search on through a web page. The information available about recycling facilities includes:

- Facility location
- Location current owner and administrator
- What specific recyclable materials the location accepts
- A google maps generated map showing the place location by its coordinates

Other feature implemented for this project is that we are giving the chance for the users themselves to sign in on the site so they can become the ones that are in charge of updating, editing, adding or deleting recycling facilities from the database in order to keep the information up to date.

With respect to this last point is __important to make clear that not all user can be welcome to interact directly with the database__ and if an user wants to be chosen to do it they have to go first through a personal interview by contacting the team via an email found in the web page.

#### Program contents:
1. __project folder:__
    - The main folder of the program, inside it you can find the next folders each one to be further explained later:

        - __files folder__

        - __static folder__

        - __templates folder__

    - Other files that can be found inside the project folder:

        - __app.py:__ Here lies the source code of the server side part of the program. Written in python using the flask module with the jinja template engine to render html files, the code it's responsible for handling all the synchronous request, asynchronous request and forms submitted from the web page to the server and also responsible for writing and reading data to the sqlite3 database used by this program to process forms and delivering the contents asked by the user.

        - __tools.py:__ Python file with functions used by app.py to help give back the requested contents by the user.

        - __requirements.txt:__ A text file with the required modules that need to be installed for the app.py file to run properly.

2. __files folder:__

    - __borradas.txt:__ This text file serves as a backup for deleted information about recycling facilities in the server database. This file is only accesible to the site administrators and is expected to be used as a way to recover information that might have been deleted intentionally or unintentionally by a signed in user.

    - __imagenes_materiales.txt:__ This file stores html code as text that can be requested from the site and returned as valid html code that is used to display images.

    - __informacion_materiales.txt:__ This file stores html code as text that can be requested from the site and returned as valid html code used to display information about a subject.

    - __puntos_de_reciclaje.db:__ The database that is used by the server to handle all the information request and modifications to the database. Inside the database there a 3 tables:

        - __historial:__ Holds all the information about modifications made to the other 2 tables in this database so all changes can be connected to a specific user, thus making it easier to have user accountability.

        - __reciclaje:__ Holds all the info about the recycling facilities inside Chile, this is where all the info a user asking for recycling facilities nearby comes from.

        - __usuarios_registrados:__ Holds all the current users that are signed in to the site, making a distinction between users that are only editors (can alter the database) and users that are administrators (can alter the database, see deleted data from the database and add or delete user).

    - __Puntos_verdes_y_limpios_Chile.xlsx:__
    This is an excel spreadsheet that contains up to date database information about all the recycling facilities in Chile. This file exist so anyone can download it from the site
    to explore its contents.

3. __static folder:__

    - In this folder you can find first __3 other folders with the names fondos, materiales and puntos__, all 3 folders are used to host a bunch of different jpg and png images that are used throughout tha page as either backgrounds or visual supports.

    - Next you can find the file titled __scripts.js__ containing a collection of javascript functions used either to make async request to the server or to give more functionality to the web page.

    - Finally you can find the file __styles.css__ used to give the site its final design.

4. __templates folder:__
    
    - This folder contains all the __html files__ that are rendered by the flask module in the app.py file. Some of the html files in this folder are the returned contents to an async request.