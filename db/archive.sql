create schema archive;

create type archive.t_file_type as enum('archive', 'image', 'text', 'audio');

create sequence archive.file_id_seq start with 10000000;

create table archive.file
(
    id              bigint primary key default nextval('archive.file_id_seq'),
    md5             char(32) not null,
    size            bigint not null,
    dt_added        timestamptz not null default current_timestamp(),
    t_file_type     file_type not null
);

create unique index on archive.file using btree (md5);

alter table archive.file add constraint file_size_check check (size > 0);

create sequence archive.original_filename_id_seq start with 10000000;

create table archive.original_filename
(
    id              bigint primary key default nextval('archive.original_filename_id_seq'),
    file_id         bigint not null references archive.file(id),
    filename        text not null,
);

create sequence archive.file_inclusion_id_seq start with 10000000;

create table archive.file_inclusion
(
    id                  bigint primary key default nextval('archive.file_inclusion_id_seq'),
    including_file_id   bigint not null references archive.file(id),
    included_file_id    bigint not null references archive.file(id)
);
