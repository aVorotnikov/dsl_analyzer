CREATE TABLE dsl_type
(
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL
);
INSERT INTO dsl_type (category) VALUES ("None");

CREATE TABLE languages
(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dsl_type_id INTEGER NOT NULL,
    FOREIGN KEY(dsl_type_id) REFERENCES dsl_type(id)
);

CREATE TABLE language_data
(
    id INTEGER PRIMARY KEY,
    language_id INTEGER NOT NULL,
    files INTEGER NOT NULL,
    blank INTEGER NOT NULL,
    comment INTEGER NOT NULL,
    code INTEGER NOT NULL,
    FOREIGN KEY(language_id) REFERENCES languages(id)
);

CREATE TABLE repository
(
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    clone_url TEXT NOT NULL,
    forks_count INTEGER NOT NULL,
    stargazers_count INTEGER NOT NULL,
    watchers_count INTEGER NOT NULL
);

CREATE TABLE repository_language_data
(
    id INTEGER PRIMARY KEY,
    repository_id INTEGER NOT NULL,
    language_data_id INTEGER NOT NULL,
    FOREIGN KEY(repository_id) REFERENCES repository(id),
    FOREIGN KEY(language_data_id) REFERENCES language_data(id)
);
