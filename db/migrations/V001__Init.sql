create schema archive;

alter schema archive owner to archive;

set role archive;
set search_path to archive, public;

create type archive.t_file_type as enum('archive', 'image', 'text', 'audio');

create sequence archive.file_id_seq start with 10000000;

create table archive.file
(
    id              bigint primary key default nextval('archive.file_id_seq'),
    md5             char(32) not null,
    size            bigint not null,
    dt_added        timestamptz not null default current_timestamp,
    file_type       archive.t_file_type not null
);

create unique index on archive.file using btree (md5);

alter table archive.file add constraint file_size_check check (size > 0);

create sequence archive.original_filename_id_seq start with 10000000;

create table archive.original_filename
(
    id              bigint primary key default nextval('archive.original_filename_id_seq'),
    file_id         bigint not null references archive.file(id),
    filename        text not null
);

create sequence archive.file_inclusion_id_seq start with 10000000;

create table archive.file_inclusion
(
    id                  bigint primary key default nextval('archive.file_inclusion_id_seq'),
    including_file_id   bigint not null references archive.file(id),
    included_file_id    bigint not null references archive.file(id)
);

reset role;

create schema app;
alter schema app owner to app;

create or replace
function app.file_add(amd5 char(32), asize bigint, afile_type archive.t_file_type) returns integer as
$$
declare
    vid bigint;
begin
    select id into vid from archive.file where md5 = amd5 for update;

    if vid is null then
        insert into archive.file(md5, size, file_type) values (amd5, asize, afile_type)
        returning id into vid;
    end if;

    return vid;
end;
$$ language plpgsql security definer;

alter function app.file_add(char(32), bigint, archive.t_file_type) owner to archive;