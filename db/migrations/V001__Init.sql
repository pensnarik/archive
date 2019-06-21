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
    ctime           timestamptz,
    mtime           timestamptz,
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

create unique index on archive.original_filename using btree (file_id, filename);

create sequence archive.file_inclusion_id_seq start with 10000000;

create table archive.file_inclusion
(
    id                  bigint primary key default nextval('archive.file_inclusion_id_seq'),
    including_file_id   bigint not null references archive.file(id),
    included_file_id    bigint not null references archive.file(id)
);

create unique index on archive.file_inclusion(including_file_id, included_file_id);

create table archive.image
(
    id                  bigint primary key references archive.file(id),
    width               integer,
    height              integer
);

create sequence archive.exif_id_seq start with 10000000;

create table archive.exif
(
    id                  bigint primary key default nextval('archive.exif_id_seq'),
    file_id             bigint not null references archive.file(id),
    tag                 text not null,
    value               text
);

create unique index on archive.exif using btree (file_id, tag);

reset role;

create schema app;
alter schema app owner to app;
grant usage on schema app to archive;

create or replace
function app.file_add
(
    amd5 char(32),
    asize bigint,
    afile_type archive.t_file_type,
    actime timestamptz,
    amtime timestamptz,
    aoriginal_filename text,
    aparent char(32)
) returns bigint as
$$
declare
    vid bigint; vinclusion_id bigint; vparent_id bigint;
begin
    select id into vid from archive.file where md5 = amd5 for update;

    if vid is null then
        insert into archive.file(md5, size, file_type, ctime, mtime)
        values (amd5, asize, afile_type, actime, amtime)
        returning id into vid;
    end if;

    perform app.original_filename_add(vid, aoriginal_filename);

    if aparent is not null then
        vparent_id := app.file_id_get(aparent);

        if vparent_id is null then
            raise exception 'Could not find parent file';
        end if;

        select id into vinclusion_id
          from archive.file_inclusion
         where including_file_id = vparent_id
           and included_file_id = vid
           for update;

        if vinclusion_id is null then
            insert into archive.file_inclusion (including_file_id, included_file_id)
            values (vparent_id, vid)
            returning id into vinclusion_id;
        end if;
    end if;

    return vid;
end;
$$ language plpgsql security definer;

alter function app.file_add(char(32), bigint, archive.t_file_type, timestamptz, timestamptz, text, char(32)) owner to archive;

create or replace
function app.original_filename_add
(
    afile_id bigint,
    afilename text
) returns bigint as $$
declare
    vid bigint;
begin
    select id into vid from archive.original_filename
     where file_id = afile_id and filename = afilename;

    if vid is null then
        insert into archive.original_filename(file_id, filename)
        values (afile_id, afilename)
        returning id into vid;
    end if;

    return vid;
end;
$$ language plpgsql security definer;

alter function app.original_filename_add(bigint, text) owner to archive;

create or replace
function app.file_id_get(ahash char(32)) returns bigint as $$
    select id from archive.file where md5 = ahash;
$$ language sql security definer stable;

alter function app.file_id_get(char(32)) owner to archive;

create or replace
function app.image_add
(
    afile_id bigint,
    awidth integer,
    aheight integer,
    aexif json
) returns bigint as $$
declare
    vid bigint;
begin
    if exists (select * from archive.image where id = afile_id) then
        return vid;
    end if;

    insert into archive.image (id, width, height)
    values (afile_id, awidth, aheight)
    returning id into vid;

    insert into archive.exif (file_id, tag, value)
    select afile_id, key, value 
      from json_each(aexif);

    return vid;
end;
$$ language plpgsql security definer;

alter function app.image_add(bigint, integer, integer, json) owner to archive;