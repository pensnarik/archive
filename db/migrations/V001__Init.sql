create schema archive;

alter schema archive owner to archive;

set role archive;
set search_path to archive, public;

create type archive.t_file_type as enum('archive', 'image', 'text', 'audio', 'video');

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
    height              integer,
    pcp_hash            char(16),
    coords              point,
    exif_datetime       timestamp,
    format              text not null,
    mode                varchar(255) not null
);

comment on table archive.image is 'Images and attributes related to them';
comment on column archive.image.exif_datetime is 'Timestamp from EXIF, no need to store TZ info here';

create sequence archive.exif_id_seq start with 10000000;

create table archive.exif
(
    id                  bigint primary key default nextval('archive.exif_id_seq'),
    file_id             bigint not null references archive.file(id),
    tag                 text not null,
    value               text
);

create unique index on archive.exif using btree (file_id, tag);

create sequence archive.users_id_seq start with 100000;

create table archive.users
(
    id                  integer primary key default nextval('archive.users_id_seq'),
    dt_created          timestamptz not null default current_timestamp,
    email               text not null,
    token               text not null
);

create unique index on archive.users using btree (email);
create unique index on archive.users using btree (token);

insert into archive.users (email, token) values ('dev@dev', md5('dev'));

create sequence archive.backup_id_seq start with 10000000;

create table archive.backup
(
    id              bigint primary key default nextval('archive.backup_id_seq'),
    file_id         bigint not null references archive.file(id),
    service         text not null,
    uid             text not null,
    dt_backup       timestamptz not null default current_timestamp
);

create unique index on archive.backup (service, uid);

reset role;

create schema app;
alter schema app owner to app;
grant usage on schema app to archive;

create or replace
function app.file_backup
(
    ahash text,
    aservice text,
    auid text
) returns bigint as $$
declare
    vid bigint; vfile_id bigint;
begin
    vfile_id := app.file_id_get(ahash);

    if vfile_id is null then
        raise exception 'Couldn''t find file with hash %', ahash;
    end if;

    insert into archive.backup(file_id, service, uid)
    values (vfile_id, aservice, auid)
    returning id into vid;

    return vid;
end;
$$ language plpgsql security definer;

alter function app.file_backup(text, text, text) owner to archive;

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
    apcp_hash char(16),
    acoords point,
    aexif_datetime timestamp,
    aformat text,
    amode varchar,
    aexif json
) returns bigint as $$
declare
    vid bigint;
begin
    if exists (select * from archive.image where id = afile_id) then
        return vid;
    end if;

    insert into archive.image (id, width, height, pcp_hash, coords, exif_datetime, format,
      mode)
    values (afile_id, awidth, aheight, apcp_hash, acoords, aexif_datetime, aformat,
      amode)
    returning id into vid;

    insert into archive.exif (file_id, tag, value)
    select afile_id, key, value
      from json_each(aexif);

    return vid;
end;
$$ language plpgsql security definer;

alter function app.image_add(bigint, integer, integer, char(16), point, timestamp, text, varchar, json) owner to archive;

create function app.check_token
(
    atoken text
) returns boolean as $$
    select exists (select * from archive.users where token = atoken);
$$ language sql security definer immutable;

alter function app.check_token(text) owner to archive;

create or replace
function app.file_exists(atoken char(32)) returns boolean as $$
    select exists (select * from archive.file where md5 = atoken);
$$ language sql security definer immutable;

alter function app.file_exists(char(32)) owner to archive;

create or replace
function app.image_list
(
    afilter text,
    avalue text
) returns table
(
    file_name text,
    file_type text,
    ctime timestamptz,
    mtime timestamptz,
    size bigint,
    hint text
) as $$
begin
    if afilter = '/By date' then
        return query
        select to_char(date_trunc('year', i.exif_datetime), 'yyyy') as file_name,
               'd' as file_type,
               max(f.ctime) as ctime,
               max(f.mtime) as mtime,
               sum(f.size)::bigint as size,
               count(*)::text as hint
          from archive.image i
          join archive.file f on f.id = i.id
         where i.exif_datetime is not null
          group by 1, 2
          order by 1;
    elsif afilter = 'year' then
        return query
        select to_char(date_trunc('month', i.exif_datetime), 'yyyy-mm') as file_name,
               'd' as file_type,
               max(f.ctime) as ctime,
               max(f.mtime) as mtime,
               sum(f.size)::bigint as size,
               count(*)::text as hint
          from archive.image i
          join archive.file f on f.id = i.id
         where to_char(i.exif_datetime, 'yyyy') = avalue
          group by 1, 2
          order by 1;
    elsif afilter = 'month' then
        return query
        select to_char(date_trunc('day', i.exif_datetime), 'yyyy-mm-dd') as file_name,
               'd' as file_type,
               max(f.ctime) as ctime,
               max(f.mtime) as mtime,
               sum(f.size)::bigint as size,
               count(*)::text as hint
          from archive.image i
          join archive.file f on f.id = i.id
         where to_char(i.exif_datetime, 'yyyy-mm') = avalue
          group by 1, 2
          order by 1;
    elsif afilter = 'day' then
        return query
        select format('%s.%s', f.md5, i.format) as file_name,
               'f'::text as file_type,
               f.ctime as ctime,
               f.mtime as mtime,
               f.size as size,
               ''::text as hint
          from archive.image i
          join archive.file f on f.id = i.id
         where to_char(i.exif_datetime, 'yyyy-mm-dd') = avalue
          order by 1;
    elsif afilter = '/By maker' then
        return query
        select e.value as file_name,
               'd' as file_type,
               max(f.ctime) as ctime,
               max(f.mtime) as mtime,
               sum(f.size)::bigint as size,
               count(*)::text as hint
          from archive.image i
          join archive.exif e on e.file_id = i.id
          join archive.file f on f.id = i.id
         where e.tag = 'Make'
          group by 1, 2
          order by 1;
    elsif afilter = 'Make' then
        return query
        select e2.value as file_name,
               'd' as file_type,
               max(f.ctime) as ctime,
               max(f.mtime) as mtime,
               sum(f.size)::bigint as size,
               count(*)::text as hint
          from archive.image i
          join archive.exif e on e.file_id = i.id and e.tag = 'Make'
          join archive.file f on f.id = i.id
          join archive.exif e2 on e2.file_id = i.id and e2.tag = 'Model'
         where e.value = avalue
          group by 1, 2
          order by 1;
    elsif afilter = 'Model' then
        return query
        select format('%s.%s', f.md5, i.format) as file_name,
               'f'::text as file_type,
               f.ctime as ctime,
               f.mtime as mtime,
               f.size as size,
               ''::text as hint
          from archive.image i
          join archive.file f on f.id = i.id
          join archive.exif e on e.file_id = i.id and e.tag = 'Model'
         where e.value = avalue
          order by 1;
    end if;
end;
$$ language plpgsql security definer;

alter function app.image_list(text, text) owner to archive;

create or replace
function app.image_local_filename
(
    ahash text
) returns text as $$
    select filename
      from archive.file f
      join archive.original_filename ori on ori.file_id = f.id
     where f.md5 = ahash
     order by ori.filename like './tmp%'
     limit 1;
$$ language sql security definer immutable;

alter function app.image_local_filename(text) owner to archive;

create or replace
function app.image_getattr(ahash text) returns table
(
    size bigint,
    ctime bigint,
    mtime bigint
) as $$
    select f.size,
           extract(epoch from f.ctime)::bigint as ctime,
           extract(epoch from f.mtime)::bigint as mtime
      from archive.file f
     where f.md5 = ahash;
$$ language sql security definer immutable;

alter function app.image_getattr(text) owner to archive;


        select format('%s.%s', f.md5, i.format) as file_name,
               'f'::text as file_type,
               f.ctime as ctime,
               f.mtime as mtime,
               f.size as size,
               ''::text as hint
          from archive.image i
          join archive.file f on f.id = i.id
          join archive.exif e on e.file_id = i.id and e.tag = 'Model'
         where e.value = '"iPhone 4S"'
          order by 1;