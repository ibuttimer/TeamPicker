INSERT INTO
    teams (name)
VALUES
    ('Team 1'),
    ('Team 2'),
    ('Team 3');

INSERT INTO
    users (name, surname, auth0_id, role_id, team_id)
VALUES
    ('Manny',   'Uno',  'auth0|abcdef12345xyz', 1, 2),
    ('Manfred', 'Dos',  'auth0|abcdef12345xyz', 1, 3),
    ('Mildred', 'Tres', 'auth0|abcdef12345xyz', 1, 4);

INSERT INTO
    users (name, surname, auth0_id, role_id, team_id)
VALUES
    ('Patrik',   'Einer', 'auth0|abcdef12345xyz', 2, 2),
    ('Pat',      'Ceann', 'auth0|abcdef12345xyz', 2, 2),
    ('Patrice',  'Un',    'auth0|abcdef12345xyz', 2, 2),
    ('Johann',   'Zwei',  'auth0|abcdef12345xyz', 2, 3),
    ('Sean',     'Do',    'auth0|abcdef12345xyz', 2, 3),
    ('Jean',     'Deux',  'auth0|abcdef12345xyz', 2, 3),
    ('Joanna',   'Drei',  'auth0|abcdef12345xyz', 2, 4),
    ('Dearbhla', 'Triur', 'auth0|abcdef12345xyz', 2, 4),
    ('Jean',     'Trois', 'auth0|abcdef12345xyz', 2, 4);

select * from roles;
select * from teams;
select * from users;
select * from matches;
select * from selections;
