# TeamPicker API

- [API Sections](#api-sections)
- [General Errors](#general-errors)
- [UI API](#ui-api)
  - [Home](#home)
  - [Dashboard](#dashboard)
  - [Login](#login)
  - [Callback](#callback)
  - [Logout](#logout)
  - [Setup user](#setup-user)
  - [Setup team](#setup-team)
  - [Set user's team](#set-users-team)
  - [Initialise match creation/search or list (UI)](#initialise-match-creationsearch-or-list-ui)
  - [Initialise match creation (UI)](#initialise-match-creation-ui)
  - [Initialise match search (UI)](#initialise-match-search-ui)
  - [List matches (UI)](#list-matches-ui)
  - [Create a match (UI)](#create-a-match-ui)
  - [Get/update a match (UI)](#getupdate-a-match-ui)
  - [Search match (UI)](#search-match-ui)
  - [Get match selections (UI)](#get-match-selections-ui)
  - [Update user match selection](#update-user-match-selection)
  - [Update user match confirmation](#update-user-match-confirmation)
  - [Delete match (UI)](#delete-match-ui)
- [Database API](#database-api)
  - [Basic Formats](#basic-formats)
    - [Success Response](#success-response)
    - [Error Response](#error-response)
  - [Get roles](#get-roles)
  - [Get role by id](#get-role-by-id)
    - [Role Entity](#role-entity)
  - [All users.](#all-users)
  - [Create user](#create-user)
  - [Get user](#get-user)
    - [User Entity](#user-entity)
  - [Update user.](#update-user)
  - [Delete user](#delete-user)
  - [All teams](#all-teams)
  - [Create team](#create-team)
  - [Get team](#get-team)
    - [Team Entity](#team-entity)
  - [Update team](#update-team)
  - [Delete team](#delete-team)
  - [All matches](#all-matches)
  - [Create match](#create-match)
  - [Get match](#get-match)
    - [Match Entity](#match-entity)
  - [Update match](#update-match)
  - [Delete match](#delete-match)
- [Test API](#test-api)
  - [Login (token)](#login-token)

### API Sections
The application API has been split into three sections; 
* the [UI API](#ui-api) 
* the [Database API](#database-api)  
* the [Test API](#test-api)  

### General Errors
General errors which may occur from any request follow the [Error Response](#error-response) format.
These include but are not limited to:

| Error | Reason |
| ----- | ------ |
| 503: Service Unavailable | Database related issue |

### UI API
This section deals with requests utilised by a UI application. 
#### Home
Home endpoint.


|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | - |

For example,

*Request*

GET `/`

*Response*

`Home` screen.

#### Dashboard
Dashboard endpoint.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/dashboard` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK <br> 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | - |

For example,

*Request*

GET `/dashboard`

*Response*

`Dashboard` screen.

#### Login
Endpoint to handle login requests.

In some scenarios, the [Auth0](https://auth0.com/) service will need to redirect to the application’s login page.
This URI is the route in the application that redirects to the the [Auth0](https://auth0.com/) service's `/authorize` endpoint.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/login` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | - |
| **Response Body** | html |
| **Errors**        | - |

For example,

*Request*

GET `/login`

*Response*

Redirects to the [Auth0](https://auth0.com/) service's `/authorize` endpoint.

#### Callback
Endpoint to handle Auth0 callback requests.

After the user authenticates, the [Auth0](https://auth0.com/) service will callback this URI with the result of the login.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/callback` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | - |

For example,

*Request*

GET `/callback?code=<authorisation code>`

*Response*

Completes login by exchanging an Authorization Code for a token, and redirects to the `Dashboard` screen.
See [Authorization Code Flow](https://auth0.com/docs/flows/authorization-code-flow) for more information.

#### Logout
Endpoint to handle logout requests.

Logs out the currently logged-in user and redirects to the `Home` screen.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/logout` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | - |

For example,

*Request*

GET `/logout`

*Response*

`Home` screen

#### Setup user
Endpoint to handle requests to set up a user.

Create a new user in the application database, following initial registration with the [Auth0](https://auth0.com/) service.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/users/setup` |
| **Method**        | `POST` |
| **Request Body**  | `csrf_token:` CSRF token <br> `name:` user's first name <br> `surname:` user's surname <br> `role_id:` id of user's role |
| **Data type**     | - |
| **Content-Type**  | application/x-www-form-urlencoded |
| **Response**      | 200: OK - form data error, resubmit <br> 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | 422: UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/users/setup`
```
csrf_token: abcdef123456ghijk
name: Manny
surname: Uno
role_id: 1
```

*Response*

Redirects to the `Dashboard` screen.

#### Setup team
Endpoint to handle requests to set up a team.

Create a new team in the application database, following initial registration with the [Auth0](https://auth0.com/) service.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/teams/setup` |
| **Method**        | `POST` |
| **Request Body**  | `csrf_token:` CSRF token <br> `name:` name of team |
| **Data type**     | - |
| **Content-Type**  | application/x-www-form-urlencoded |
| **Response**      | 200: OK - form data error, resubmit <br> 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | 401: UNAUTHORISED <br> 422: UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/teams/setup`
```
csrf_token: abcdef123456ghijk
name: Team 1
```

*Response*

Redirects to the `Dashboard` screen.

#### Set user's team
Endpoint to handle requests to set a user's team.

As part of the initial setup of a player, they are required to select a team.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/users/<int:user_id>/team` <br> where `<user_id>` is the id of the user |
| **Method**        | `POST` |
| **Request Body**  | `csrf_token:` CSRF token <br> `team_id:` id of team |
| **Data type**     | - |
| **Content-Type**  | application/x-www-form-urlencoded |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND <br> 422: UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/users/1/team`

```
csrf_token: abcdef123456ghijk
team_id: 1
```

*Response*

Redirects to the `Dashboard` screen.

#### Initialise match creation/search or list (UI)
Endpoint to handle requests to start match creation or search, or list matches.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches` |
| **Method**        | `GET` |
| **Query**         | `new`: initiate match creation; *y/n*, default *n* <br> `search`: initiate match search; *y/n*, default *n* <br> When none of the previous queries are specified, list matches, with <br> `order`: match list order; *date_desc/date_asc*, default *n* |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | application/x-www-form-urlencoded |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | 302: FOUND - redirect when not logged-in <br> 400: BAD REQUEST <br> 401: UNAUTHORISED |

For example,

#### Initialise match creation (UI)
*Request*

GET `/matches?new=y`

*Response*

`Create match` screen

#### Initialise match search (UI)
*Request*

GET `/matches?search=y`

*Response*

`Search match` screen

#### List matches (UI)
*Request*

GET `/matches?order=date_desc`

*Response*

`Match list` screen with matches listed in date descending order.

#### Create a match (UI)
Endpoint to handle requests to create/update a match.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches` |
| **Method**        | `POST` |
| **Request Body**  | `csrf_token:` CSRF token <br> `venue:` match venue; home *0* or away *1* <br> `opposition:` id of opposition team <br> `start_time:` match start time; YYYY-MM-DD HH:MM <br> `result:` final result flag; *y* or *n* <br> `team_score:` own team score <br> `opposition_score:` opposition team score |
| **Data type**     | - |
| **Content-Type**  | application/x-www-form-urlencoded |
| **Response**      | 200: OK - form data error, resubmit <br> 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | 401: UNAUTHORISED <br> 422: UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/matches`
```
csrf_token: abcdef123456ghijk
venue: 0
opposition: 2
start_time: 2021-07-07 11:00
result: n
team_score: 8 
opposition_score: 0
```

*Response*

Redirects to the `Dashboard` screen.

#### Get/update a match (UI)
Endpoint to handle requests to get/update a match.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches/<int:match_id>` <br> where `<match_id>` is the id of the match |
| **Method**        | `GET, PATCH, POST` |
| **Request Body**  | `PATCH`/`POST`: see [Create a match (UI)](#create-a-match-ui) |
| **Data type**     | - |
| **Content-Type**  | `PATCH`/`POST`: see [Create a match (UI)](#create-a-match-ui) |
| **Response**      | 200: OK <br> 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | 400: BAD REQUEST <br> 401: UNAUTHORISED <br> 404: NOT FOUND <br> 422: UNPROCESSABLE ENTITY |

For example,

*Request*

GET `/matches/1`

*Response*

`Match update` screen.

*Request*

POST `/matches/1`
```
csrf_token: abcdef123456ghijk
venue: 0
opposition: 2
start_time: 2021-07-07 12:00
result: y
team_score: 8 
opposition_score: 2
```

*Response*

`Dashboard` screen.

#### Search match (UI)
Endpoint to handle match search requests.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches/search` |
| **Method**        | `POST` |
| **Request Body**  | `csrf_token:` CSRF token <br> `opposition:` id of opposition team <br> `start_time:` match start time; YYYY-MM-DD <br> `date_range:` one of *DateRange.IGNORE_DATE*, *DateRange.BEFORE_DATE*, *DateRange.BEFORE_OR_EQUAL_DATE*, *DateRange.EQUAL_DATE*, *DateRange.AFTER_OR_EQUAL_DATE*, *DateRange.AFTER_DATE* |
| **Data type**     | - |
| **Content-Type**  | application/x-www-form-urlencoded |
| **Response**      | 200: OK - form data error, resubmit <br> 302: FOUND - redirect |
| **Response Body** | html |
| **Errors**        | 400: BAD REQUEST |

For example,

*Request*

POST `/matches/search`
```
csrf_token: abcdef123456ghijk
opposition: 2
start_time: 2021-07-07
date_range: DateRange.BEFORE_DATE
```

*Response*

`Match search result` screen.


#### Get match selections (UI)
Endpoint to handle requests to get match selections.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches/<int:match_id>/selections` <br> where `<match_id>` is the id of the match |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

GET `/matches/1/selections`

*Response*

`Match selections` screen.

#### Update user match selection
Endpoint to handle requests to update individual user's match selection status.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches/<int:match_id>/selections/<int:user_id>` <br> where `<match_id>` is the id of the match and `<user_id>` is the id of the user |
| **Method**        | `POST` |
| **Query**         | `select`: selection setting; *y* (yes), *n* (no) or *t* (toggle), default *t* |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

POST `/matches/1/selections/2?select=y`

*Response*

`Match selections` screen.

#### Update user match confirmation
Endpoint to handle requests to update individual user's match confirmation status.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches/<int:match_id>/confirm/<int:user_id>` <br> where `<match_id>` is the id of the match and `<user_id>` is the id of the user |
| **Method**        | `POST` |
| **Query**         | `select`: selection setting; *y* (yes), *n* (no) or *m* (maybe), default *m* |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

POST `/matches/1/confirm/2?select=y`

*Response*

`Match selections` screen.

#### Delete match (UI)
Endpoint to handle requests to DELETE match by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/matches/<int:match_id>` <br> where `<match_id>` is the id of the match |
| **Method**        | `DELETE` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | json |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

DELETE `/matches/1`

*Response*

See [Delete match](#delete-match)


### Database API
This section deals with requests utilised to interact with the database. 

#### Basic Formats
In general, the following basic formats are utilised:

##### Success Response
The standard success response has the following the format:

| Field            | Description |
|------------------|-------------|
| ``success``      | success flag, always *true* for an successful response |
| *payload*        | results, endpoint dependant and may be a list or json object |

##### Error Response
The standard error response has the following format:

| Field            | Description |
|------------------|-------------|
| ``success``          | success flag, always *false* for an error response |
| ``error``            | http status code |
| ``message``          | message corresponding to http status code |
| ``detailed_message`` | optional, detailed message |

For example, an invalid login would result in the following response:
```json
{
  "success": false,
  "error": 401,
  "message": "Unauthorized",
  "detailed_message": "Invalid username or password"
}
```

#### Get roles
Endpoint to handle requests for all roles.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/roles` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `roles`. |
| `roles`           | a list of [Role Entity](#role-entity) |
| **Errors**        | 401: UNAUTHORISED |

For example,

*Request*

GET `/api/roles`

*Response*

```json
{
  "roles": [
    {
      "id": 1,
      "role": "Manager"
    },
    {
      "id": 2,
      "role": "Player"
    }
  ],
  "success": true
}
```

#### Get role by id
Endpoint to handle requests for role by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/roles/<int:role_id>` <br> where `<role_id>` is the id of the role |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `role`. |
| `role`            | a [Role Entity](#role-entity) |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

##### Role Entity
A role entity contains the following attributes

`id`: role id <br>`role`: role title

For example,

*Request*

GET `/api/roles/1`

*Response*

```json
{
  "role": {
    "id": 1,
    "role": "Manager"
  },
  "success": true
}
```

#### All users.
Endpoint to handle requests for all users.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/users` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `users`. |
| `users`           | a list of [User Entity](#user-entity) |
| **Errors**        | 401: UNAUTHORISED |

For example,

*Request*

GET `/api/users`

*Response*

```json
{
  "success": true,
  "users": [
    {
      "auth0_id": "auth0|acbdefg123456",
      "id": 1,
      "name": "Manny",
      "role_id": 1,
      "surname": "Uno",
      "team_id": 2
    },
    ...
  ]
}
```

#### Create user
Endpoint to handle requests to create a user.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/users` |
| **Method**        | `POST` |
| **Request Body**  | `auth0_id`: id of user on the [Auth0](https://auth0.com/) service <br>`name`: user first name <br>`surname`: user surname <br>`role_id`: id of user's role <br>`team_id`: id of user's team |
| **Data type**     | json |
| **Content-Type**  | application/json |
| **Response**      | 201 - CREATED |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `created`, `id` and `user`. |
| `created`         | number of users created  |
| `id`              | id of user in database  |
| `user`            | a [User Entity](#user-entity)  |
| **Errors**        | 400 - BAD REQUEST <br> 422 - UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/api/users`
```json
{
  "auth0_id": "auth0|acbdefg123456",
  "name": "Manny",
  "role_id": 1,
  "surname": "Uno",
  "team_id": 2
}
```

*Response*
```json
{
  "success": true,
  "created": 1,
  "id": 1,
  "user": {
    "auth0_id": "auth0|acbdefg123456",
    "id": 1,
    "name": "Manny",
    "role_id": 1,
    "surname": "Uno",
    "team_id": 2
  }
}
```

#### Get user
Endpoint to handle requests for user by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/users/<int:user_id>` <br> where `<user_id>` is the id of the user |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `user`. |
| `user`            | a [User Entity](#user-entity)  |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

##### User Entity
A user entity contains the following attributes

`auth0_id`: id of user on the [Auth0](https://auth0.com/) service <br>`id`: user id in database <br>`name`: user first name <br>`surname`: user surname <br>`role_id`: id of user's role <br>`team_id`: id of user's team

For example,

*Request*

GET `/api/users/1`

*Response*

```json
{
  "success": true,
  "user": {
    "auth0_id": "auth0|acbdefg123456",
    "id": 1,
    "name": "Manny",
    "role_id": 1,
    "surname": "Uno",
    "team_id": 2
  }
}
```

#### Update user.
Endpoint to handle requests to update user by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/users/<int:user_id>` <br> where `<user_id>` is the id of the user |
| **Method**        | `PATCH` |
| **Request Body**  | See [Create user](#create-user) |
| **Data type**     | See [Create user](#create-user) |
| **Content-Type**  | See [Create user](#create-user) |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `updated` and `user`. |
| `updated`         | number of users updated |
| `user`            | a [User Entity](#user-entity)  |
| **Errors**        | 400 - BAD REQUEST <br> 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

PATCH `/api/users/1`
```json
{
  "auth0_id": "auth0|acbdefg123456",
  "name": "Manny",
  "role_id": 1,
  "surname": "Uno",
  "team_id": 2
}
```

*Response*
```json
{
  "success": true,
  "updated": 1,
  "user": {
    "auth0_id": "auth0|acbdefg123456",
    "id": 1,
    "name": "Manny",
    "role_id": 1,
    "surname": "Uno",
    "team_id": 2
  }
}
```

#### Delete user
Endpoint to handle requests to delete user by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/users/<int:user_id>` <br> where `<user_id>` is the id of the user |
| **Method**        | `DELETE` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `deleted`. |
| `deleted`         | number of users deleted |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

DELETE `/api/users/1`

*Response*

```json
{
  "success": true,
  "deleted": 1
}
```

#### All teams
Endpoint to handle requests for all teams.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/teams` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `teams`. |
| `teams`           | a list of [Team Entity](#team-entity) |
| **Errors**        | 401: UNAUTHORISED |

For example,

*Request*

GET `/api/teams`

*Response*

```json
{
  "success": true,
  "teams": [
    {
      "id": 1,
      "name": "Unassigned"
    },
    {
      "id": 2,
      "name": "Team 1"
    },
    ...
  ]
}
```

#### Create team
Endpoint to handle requests to create a team.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/teams` |
| **Method**        | `POST` |
| **Request Body**  | `name`: name of team |
| **Data type**     | json |
| **Content-Type**  | application/json |
| **Response**      | 201 - CREATED |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `created`, `id` and `team`. |
| `created`         | number of teams created  |
| `id`              | id of team in database  |
| `team`            | a [Team Entity](#team-entity)  |
| **Errors**        | 400 - BAD REQUEST <br> 422 - UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/api/teams`
```json
{
  "name": "Team 1"
}
```

*Response*

```json
{
  "success": true,
  "created": 1,
  "id": 1,
  "team": {
    "id": 2,
    "name": "Team 1"
  }
}
```

#### Get team
Endpoint to handle requests for team by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/teams/<int:team_id>` <br> where `<team_id>` is the id of the team |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `team`. |
| `team`            | a [Team Entity](#team-entity)  |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

##### Team Entity
A team entity contains the following attributes

`id`: team id <br>`name`: team name

For example,

*Request*

GET `/api/teams/1`

*Response*

```json
{
  "success": true,
  "team": {
    "id": 1,
    "name": "Unassigned"
  }
}
```

#### Update team
Endpoint to handle requests to update team by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/teams/<int:team_id>` <br> where `<team_id>` is the id of the team |
| **Method**        | `PATCH` |
| **Request Body**  | See [Create team](#create-team) |
| **Data type**     | See [Create team](#create-team) |
| **Content-Type**  | See [Create team](#create-team) |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `updated` and `team`. |
| `updated`         | number of teams updated |
| `team`            | a [Team Entity](#team-entity)  |
| **Errors**        | 400 - BAD REQUEST <br> 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

PATCH `/api/teams/2`
```json
{
  "name": "Team 1"
}
```

*Response*

```json
{
  "success": true,
  "updated": 1,
  "team": {
    "id": 2,
    "name": "Team 1"
  }
}
```

#### Delete team
Endpoint to handle requests to delete team by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/teams/<int:team_id>` <br> where `<team_id>` is the id of the team |
| **Method**        | `DELETE` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `deleted`. |
| `deleted`         | number of teams deleted |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

DELETE `/api/teams/2`

*Response*

```json
{
  "success": true,
  "deleted": 1
}
```

#### All matches
Endpoint to handle requests for all matches.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/matches` |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attribute named `matches`. |
| `matches`         | a list of [Match Entity](#team-entity) |
| **Errors**        | 401: UNAUTHORISED |

For example,

*Request*

GET `/api/matches`

*Response*

```json
{
  "matches": [
    {
      "away_id": 29,
      "home_id": 28,
      "id": 2,
      "result": false,
      "score_away": 0,
      "score_home": 0,
      "selections": [
        {
          "auth0_id": "auth0|acbdefg123456",
          "id": 49,
          "name": "Pat",
          "role_id": 2,
          "surname": "Ceann",
          "team_id": 28
        },
        ...
      ],
      "start_time": "2021-07-03T09:00:00"
    },
    ...
  ],
  "success": true
}
```

#### Create match
Endpoint to handle requests to create a match.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/matches` |
| **Method**        | `POST` |
| **Request Body**  | `away_id`: id of away team <br>`home_id`: id of home team <br>`result`: result final flag <br>`score_away`: away team score <br>`score_home`: home team score <br>`selections`: list of ids od users selected for match <br>`start_time`: start time of match in ISO format, YYYY-MM-DDTHH:MM:SS |
| **Data type**     | json |
| **Content-Type**  | application/json |
| **Response**      | 201 - CREATED |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `created`, `id` and `match`. |
| `created`         | number of matches created  |
| `id`              | id of match in database  |
| `match`           | a [Match Entity](#match-entity)  |
| **Errors**        | 400 - BAD REQUEST <br> 422 - UNPROCESSABLE ENTITY |

For example,

*Request*

POST `/api/matches`
```json
{
  "home_id": 2, 
  "away_id": 3, 
  "start_time": "2021-06-01T15:15:00", 
  "result": true, 
  "score_home": 2, 
  "score_away": 1, 
  "selections": [6, 7]
}
```

*Response*

```json
{
  "success": true,
  "created": 1,
  "id": 1,
  "match": {
    "id": 1,
    "home_id": 2,
    "away_id": 3,
    "start_time": "2021-06-01T15:15:00",
    "result": true,
    "score_home": 2,
    "score_away": 1,
    "selections": [
      {
          "auth0_id": "auth0|acbdefg123456",
          "id": 49,
          "name": "Pat",
          "role_id": 2,
          "surname": "Ceann",
          "team_id": 28
      },
      ...
    ]
  }
}
```

#### Get match
Endpoint to handle requests for match by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/matches/<int:match_id>` <br> where `<match_id>` is the id of the match |
| **Method**        | `GET` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `match`. |
| `match`           | a [Match Entity](#match-entity)  |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

##### Match Entity
A team entity contains the following attributes

`id`: match id <br>`away_id`: id of away team <br>`home_id`: id of home team <br>`result`: result final flag <br>`score_away`: away team score <br>`score_home`: home team score <br>`selections`: list of [User Entity](#user-entity) selected for match <br>`start_time`: start time of match 

For example,

*Request*

GET `/api/matches/1`

*Response*

```json
{
  "success": true,
  "match": {
    "id": 1,
    "home_id": 2,
    "away_id": 3,
    "start_time": "2021-06-01T15:15:00",
    "result": true,
    "score_home": 2,
    "score_away": 1,
    "selections": [
      {
        "auth0_id": "auth0|acbdefg123456",
        "id": 49,
        "name": "Pat",
        "role_id": 2,
        "surname": "Ceann",
        "team_id": 28
      },
      ...
    ]
  }
}
```

#### Update match
Endpoint to handle requests to PATCH match by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/matches/<int:match_id>` <br> where `<match_id>` is the id of the match |
| **Method**        | `PATCH` |
| **Request Body**  | See [Create match](#create-match) |
| **Data type**     | See [Create match](#create-match) |
| **Content-Type**  | See [Create match](#create-match) |
| **Response**      | 200: OK |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `updated` and `match`. |
| `updated`         | number of matches updated |
| `match`           | a [Match Entity](#match-entity)  |
| **Errors**        | 400 - BAD REQUEST <br> 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

PATCH `/api/matches/1`
```json
{
  "home_id": 2, 
  "away_id": 3, 
  "start_time": "2021-06-01T15:15:00", 
  "result": true, 
  "score_home": 2, 
  "score_away": 1, 
  "selections": [6, 7]
}
```

*Response*

```json
{
  "success": true,
  "updated": 1,
  "match": {
    "id": 1,
    "home_id": 2,
    "away_id": 3,
    "start_time": "2021-06-01T15:15:00",
    "result": true,
    "score_home": 2,
    "score_away": 1,
    "selections": [
      {
        "auth0_id": "auth0|acbdefg123456",
        "id": 49,
        "name": "Pat",
        "role_id": 2,
        "surname": "Ceann",
        "team_id": 28
      },
      ...
    ]
  }
}
```

#### Delete match
Endpoint to handle requests to DELETE match by id.

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/api/matches/<int:match_id>` <br> where `<match_id>` is the id of the match |
| **Method**        | `DELETE` |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | - |
| **Response Body** | A [Success Response](#success-response) with the *payload* attributes named `deleted`. |
| `deleted`         | number of matches deleted |
| **Errors**        | 401: UNAUTHORISED <br> 404: NOT FOUND |

For example,

*Request*

DELETE `/api/matches/1`

*Response*

```json
{
  "success": true,
  "deleted": 1
}
```

### Test API
This section deals with requests utilised for application testing purposes. 

> **Note:** The endpoints in the Test API are only available when the application is started with 
> [Disable server-side sessions (--postman_test)](README.md#disable-server-side-sessions---postman_test)
> argument.

#### Login (token)
Endpoint to handle login requests using an access token (only for Postman testing).

|                   | Description |
|------------------:|-------------|
| **Endpoint**      | `/login/token` |
| **Method**        | `POST` |
| **Query**         | - |
| **Request Body**  | - |
| **Data type**     | - |
| **Content-Type**  | application/json |
| **Response**      | 200: OK |
| **Response Body** | html |
| **Errors**        | 400: BAD REQUEST |

For example,

*Request*

POST `/login/token`
```json
{
  "access_token": "xxxxx.yyyyy.zzzzz"
}
```

*Response*

Redirects to the `Dashboard` screen.
