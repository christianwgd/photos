# photos
Django photos app - Just another django photos app

### localsettings
To run create photos/localsettings.py:

mandatory:
  - DEBUG
  - SECRET_KEY
  - ALLOWED_HOSTS
  - DATABASE

optional: 
  - AUTH_PASSWORD_VALIDATORS
  - GEOPOSITION_GOOGLE_MAPS_API_KEY (if you want to use the maps)


### Theming

Bootstrap themes (css files) can be uploaded and selected by users. 

You can add themes  for user selection in the admin. Create your own 
themes (https://bootstrap.build/app) or load them from the web 
(examples below).

- https://bootstrap.build/themes
- https://bootswatch.com
- https://bootstrap.themes.guide/#themes