# flask_blog

## a flask crud project

- this project started as an attempt to experiment with redis and evolved into me working my way through the entire flask mega tutorial by Miguel Grinberg, a well-respected authority in the flask community. If you've any interest in learning some flask best practices by someone who wrote the o'reilly flask book and a couple of the popular packages in the flask ecosystem (flask-migrate, flask-moment, etc), I would give this a HUGE recommendation! amazing quality. <a href='https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world'>Flask Mega Tutorial by Miguel Grinberg</a>

- this is a full-stack flask application that essentially mimics twitter. users can follow users. users can make posts of 140 characters or less and also have a profile page.

    - few highlights that i've picked up from this project:
        - built bilingual language support (en, es) for entire site using flask-babel. it has framework to build in many additional languages.
        - worked with azure's cognitive language translation api for identifying language dialects and follow-up conversion to the native browser language of the user. it allows for comments in foreign languages of other users to be translated in real-time with ajax
        - mimic the asynchronous nature of javascript by using python's threading. in the project, this enabled background proccesses to handle sending emails for password recovery (computationally expensive) without blocking the main execution of the application.
        - more robust error handling (logging and custom error handling) plus automated email notifications on ERROR level logging events
        - project config using docker-compose and integration with vscode's debugger has been life changing! i'm beginning to understand the popularity of vscode. this has not yet been covered in the tutorial, but i used this project to sort it out, and it was WELL worth it.

    - other topics we've covered/built thus far:
        - both basic config & more advanced application factory pattern of configuring a flask app
        - wtforms and form validation
        - secure password recovery using flask-mail and json web tokens (pyjwt package)
        - basics of testing with python built-in unittest (i used pytest instead)
        - session management with flask-login
        - real-time time deltas on user posts with flask-moment (port of moment.js)
        - sqlalchemy orm, models, migrations, and sqlite
        - styles provided by flask-bootstrap's integration with wtforms
        - more to come!

- also took some time to go through this: https://www.sqlitetutorial.net/sqlite-python -- sqlite is awesome!
