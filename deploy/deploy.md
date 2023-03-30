### Deployment
#### Heroku

##### Heroku-specific artefacts
The following are specific to a [Heroku](https://www.heroku.com/) deployment:
- [Procfile](../Procfile)

  https://devcenter.heroku.com/articles/procfile

- Environment variables as specified in [sample.env](../instance/sample.env) must be specified in [config vars](https://devcenter.heroku.com/articles/config-vars)

##### Push local release
```shell
git push heroku master
```

##### Display logs
```shell
heroku logs --app teampicker-fswd
```

##### Run a console
```shell
heroku run bash --app teampicker-fswd
```

##### View database
Use details from the `Database Credentials` in the Settings of the attached database, from the `Resources` section of the Heroku application.

> Please note that these credentials are not permanent.
> 
> Heroku rotates credentials periodically and updates applications where this database is attached.

> The PostgreSQL interactive terminal (psql) must be installed on your local machine. See [Set up Postgres on Windows](https://devcenter.heroku.com/articles/heroku-postgresql#set-up-postgres-on-windows)
> or [Set up Postgres on Linux](https://devcenter.heroku.com/articles/heroku-postgresql#set-up-postgres-on-linux).

```shell
Connect to server
$ heroku pg:psql <postgresql-datastore-name> --app teampicker-fswd

Connect to database
$ teampicker-fswd::DATABASE=> \c <database name>

List database tables
$ teampicker-fswd::DATABASE=> \dt

Run SQL file
$ teampicker-fswd::DATABASE=> \i \path\to\sample_data.sql
```

#### Render

##### Render-specific artefacts
The following are specific to a [Render](https://www.render.com/) deployment:
- [build.sh](../build.sh)
- Environment variables as specified in [sample.env](../instance/sample.env) must be specified in [Environment Variables](https://render.com/docs/configure-environment-variables#getting-started-with-environment-variables) or in a [Environment file](https://render.com/docs/configure-environment-variables#secret-and-environment-configuration-files) 
- Data from a Heroku PostgreSQL database may be ported to a Render PostgreSQL using https://render.com/docs/migrate-from-heroku#step-4-copy-data-from-postgresql