#### Deployment

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

```shell
$ heroku pg:psql <postgresql-datastore-name> --app teampicker-fswd
$ teampicker-fswd::DATABASE=> \c <database name>
$ teampicker-fswd::DATABASE=> \dt
```

